from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import hashlib
from enum import Enum
import jwt


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
SECRET_KEY = "family_planner_secret_key_change_in_production"

# Enums
class UserRole(str, Enum):
    PARENT = "parent"
    CHILD = "child"

class EventType(str, Enum):
    TASK = "task"
    APPOINTMENT = "appointment"
    REMINDER = "reminder"
    FAMILY_TIME = "family_time"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Models
class FamilyMember(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    role: UserRole
    color: str = Field(default="#6366f1")  # Purple theme default
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FamilyMemberCreate(BaseModel):
    name: str
    email: str
    role: UserRole
    color: Optional[str] = "#6366f1"
    preferences: Optional[Dict[str, Any]] = None

class FamilyMemberLogin(BaseModel):
    email: str

class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    event_type: EventType
    priority: Priority = Priority.MEDIUM
    family_member_id: str
    created_by: str  # ID of who created this event
    attendees: List[str] = Field(default_factory=list)  # List of family member IDs
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    reminder_minutes: int = 15
    tags: List[str] = Field(default_factory=list)
    ai_optimized: bool = False
    conflicts: List[str] = Field(default_factory=list)  # List of conflicting event IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    event_type: EventType
    priority: Priority = Priority.MEDIUM
    family_member_id: str
    attendees: Optional[List[str]] = None
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    reminder_minutes: int = 15
    tags: Optional[List[str]] = None

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_type: Optional[EventType] = None
    priority: Optional[Priority] = None
    attendees: Optional[List[str]] = None
    location: Optional[str] = None
    reminder_minutes: Optional[int] = None
    tags: Optional[List[str]] = None

class AIService(BaseModel):
    """Abstract AI service interface for modular integration"""
    provider: str  # "openai", "local", "anthropic", etc.
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    enabled: bool = False

class VoiceService(BaseModel):
    """Abstract voice service interface for modular integration"""
    provider: str  # "openai", "google", "azure", etc.
    api_key: Optional[str] = None
    enabled: bool = False

# Helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(user_id: str = Depends(verify_token)):
    user = await db.family_members.find_one({"id": user_id})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return FamilyMember(**user)

def check_event_conflicts(new_event: CalendarEvent, existing_events: List[CalendarEvent]) -> List[str]:
    """Basic conflict detection without AI"""
    conflicts = []
    for event in existing_events:
        if (event.family_member_id == new_event.family_member_id and 
            event.id != new_event.id):
            # Check for time overlap
            if (new_event.start_time < event.end_time and 
                new_event.end_time > event.start_time):
                conflicts.append(event.id)
    return conflicts

# Authentication routes
@api_router.post("/auth/login")
async def login(login_data: FamilyMemberLogin):
    user = await db.family_members.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    access_token = create_access_token(data={"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer", "user": FamilyMember(**user)}

# Family Member routes
@api_router.post("/family-members", response_model=FamilyMember)
async def create_family_member(member: FamilyMemberCreate):
    # Check if email already exists
    existing = await db.family_members.find_one({"email": member.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    member_dict = member.dict()
    if member_dict.get('preferences') is None:
        member_dict['preferences'] = {}
    
    member_obj = FamilyMember(**member_dict)
    await db.family_members.insert_one(member_obj.dict())
    return member_obj

@api_router.get("/family-members", response_model=List[FamilyMember])
async def get_family_members(current_user: FamilyMember = Depends(get_current_user)):
    members = await db.family_members.find().to_list(1000)
    return [FamilyMember(**member) for member in members]

@api_router.get("/family-members/me", response_model=FamilyMember)
async def get_current_user_profile(current_user: FamilyMember = Depends(get_current_user)):
    return current_user

@api_router.put("/family-members/{member_id}", response_model=FamilyMember)
async def update_family_member(
    member_id: str,
    updates: Dict[str, Any],
    current_user: FamilyMember = Depends(get_current_user)
):
    # Check permissions
    if current_user.role != UserRole.PARENT and current_user.id != member_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Update member
    await db.family_members.update_one(
        {"id": member_id},
        {"$set": updates}
    )
    
    updated_member = await db.family_members.find_one({"id": member_id})
    if not updated_member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return FamilyMember(**updated_member)

# Calendar Event routes
@api_router.post("/events", response_model=CalendarEvent)
async def create_event(
    event: CalendarEventCreate,
    current_user: FamilyMember = Depends(get_current_user)
):
    # Check permissions
    if (current_user.role != UserRole.PARENT and 
        current_user.id != event.family_member_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    event_dict = event.dict()
    event_dict['created_by'] = current_user.id
    if event_dict.get('attendees') is None:
        event_dict['attendees'] = []
    if event_dict.get('tags') is None:
        event_dict['tags'] = []
    
    event_obj = CalendarEvent(**event_dict)
    
    # Check for conflicts
    existing_events = await db.calendar_events.find({
        "family_member_id": event.family_member_id
    }).to_list(1000)
    
    existing_event_objects = [CalendarEvent(**e) for e in existing_events]
    conflicts = check_event_conflicts(event_obj, existing_event_objects)
    event_obj.conflicts = conflicts
    
    await db.calendar_events.insert_one(event_obj.dict())
    return event_obj

@api_router.get("/events", response_model=List[CalendarEvent])
async def get_events(
    family_member_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: FamilyMember = Depends(get_current_user)
):
    query = {}
    
    # Apply filters based on user role
    if current_user.role == UserRole.CHILD:
        query["family_member_id"] = current_user.id
    elif family_member_id:
        query["family_member_id"] = family_member_id
    
    # Date range filter
    if start_date and end_date:
        query["start_time"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["start_time"] = {"$gte": start_date}
    elif end_date:
        query["end_time"] = {"$lte": end_date}
    
    events = await db.calendar_events.find(query).to_list(1000)
    return [CalendarEvent(**event) for event in events]

@api_router.put("/events/{event_id}", response_model=CalendarEvent)
async def update_event(
    event_id: str,
    updates: CalendarEventUpdate,
    current_user: FamilyMember = Depends(get_current_user)
):
    # Get existing event
    existing_event = await db.calendar_events.find_one({"id": event_id})
    if not existing_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check permissions
    if (current_user.role != UserRole.PARENT and 
        current_user.id != existing_event["created_by"] and
        current_user.id != existing_event["family_member_id"]):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    update_dict['updated_at'] = datetime.utcnow()
    
    await db.calendar_events.update_one(
        {"id": event_id},
        {"$set": update_dict}
    )
    
    updated_event = await db.calendar_events.find_one({"id": event_id})
    return CalendarEvent(**updated_event)

@api_router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    current_user: FamilyMember = Depends(get_current_user)
):
    # Get existing event
    existing_event = await db.calendar_events.find_one({"id": event_id})
    if not existing_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check permissions
    if (current_user.role != UserRole.PARENT and 
        current_user.id != existing_event["created_by"]):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    await db.calendar_events.delete_one({"id": event_id})
    return {"message": "Event deleted successfully"}

# AI Service Configuration (Modular)
@api_router.post("/ai/configure")
async def configure_ai_service(
    ai_config: AIService,
    current_user: FamilyMember = Depends(get_current_user)
):
    if current_user.role != UserRole.PARENT:
        raise HTTPException(status_code=403, detail="Only parents can configure AI services")
    
    await db.ai_config.delete_many({})  # Replace existing config
    await db.ai_config.insert_one(ai_config.dict())
    return {"message": "AI service configured successfully"}

@api_router.get("/ai/status")
async def get_ai_status(current_user: FamilyMember = Depends(get_current_user)):
    config = await db.ai_config.find_one({})
    if not config:
        return {"enabled": False, "provider": None}
    return AIService(**config)

# Voice Service Configuration (Modular)
@api_router.post("/voice/configure")
async def configure_voice_service(
    voice_config: VoiceService,
    current_user: FamilyMember = Depends(get_current_user)
):
    if current_user.role != UserRole.PARENT:
        raise HTTPException(status_code=403, detail="Only parents can configure voice services")
    
    await db.voice_config.delete_many({})  # Replace existing config
    await db.voice_config.insert_one(voice_config.dict())
    return {"message": "Voice service configured successfully"}

@api_router.get("/voice/status")
async def get_voice_status(current_user: FamilyMember = Depends(get_current_user)):
    config = await db.voice_config.find_one({})
    if not config:
        return {"enabled": False, "provider": None}
    return VoiceService(**config)

# Dashboard & Analytics
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: FamilyMember = Depends(get_current_user)):
    if current_user.role == UserRole.CHILD:
        # Child can only see their own stats
        query = {"family_member_id": current_user.id}
    else:
        # Parents can see family stats
        query = {}
    
    total_events = await db.calendar_events.count_documents(query)
    
    # Events by type
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
    ]
    events_by_type = await db.calendar_events.aggregate(pipeline).to_list(10)
    
    # Upcoming events (next 7 days)
    upcoming_query = {**query, "start_time": {"$gte": datetime.utcnow(), "$lte": datetime.utcnow() + timedelta(days=7)}}
    upcoming_events = await db.calendar_events.count_documents(upcoming_query)
    
    # Conflicts
    conflicts_query = {**query, "conflicts": {"$ne": []}}
    conflicts_count = await db.calendar_events.count_documents(conflicts_query)
    
    return {
        "total_events": total_events,
        "events_by_type": {item["_id"]: item["count"] for item in events_by_type},
        "upcoming_events": upcoming_events,
        "conflicts_count": conflicts_count
    }

# Basic health check
@api_router.get("/")
async def root():
    return {"message": "Family Daily Planner API", "status": "active"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
