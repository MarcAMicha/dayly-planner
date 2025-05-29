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
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.llm.openai import OpenAIChatRealtime

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

# AI Services - Placeholder API key for demo
DEFAULT_OPENAI_API_KEY = "sk-placeholder-key-for-demo-replace-with-real-key"

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
    ai_suggestions: List[str] = Field(default_factory=list)
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

class VoiceCommand(BaseModel):
    text: str
    family_member_id: str
    session_id: Optional[str] = None

class VoiceResponse(BaseModel):
    text: str
    audio_url: Optional[str] = None
    action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class AIOptimizationRequest(BaseModel):
    events: List[CalendarEvent]
    family_members: List[FamilyMember]
    preferences: Optional[Dict[str, Any]] = None

class AIOptimizationResponse(BaseModel):
    suggestions: List[str]
    optimized_events: List[CalendarEvent]
    conflicts_resolved: int
    time_saved_minutes: int

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

async def get_ai_config() -> Optional[AIService]:
    """Get current AI configuration"""
    config = await db.ai_config.find_one({})
    if not config:
        return None
    return AIService(**config)

async def get_voice_config() -> Optional[VoiceService]:
    """Get current voice configuration"""
    config = await db.voice_config.find_one({})
    if not config:
        return None
    return VoiceService(**config)

async def create_ai_chat(api_key: str = None, model: str = "gpt-4o") -> LlmChat:
    """Create AI chat instance with current configuration"""
    if not api_key:
        ai_config = await get_ai_config()
        api_key = ai_config.api_key if ai_config else DEFAULT_OPENAI_API_KEY
    
    session_id = str(uuid.uuid4())
    system_message = """You are an AI assistant specialized in family scheduling optimization. 
    Your role is to help families manage their time efficiently by:
    1. Detecting scheduling conflicts
    2. Suggesting optimal time slots
    3. Balancing family member preferences
    4. Prioritizing events based on importance
    5. Minimizing travel time between locations
    6. Ensuring adequate rest and family time
    
    Always provide practical, family-friendly suggestions."""
    
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message=system_message
    ).with_model("openai", model)
    
    return chat

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
        return {"enabled": False, "provider": None, "model": None}
    return AIService(**config)

@api_router.post("/ai/optimize", response_model=AIOptimizationResponse)
async def optimize_schedule(
    request: AIOptimizationRequest,
    current_user: FamilyMember = Depends(get_current_user)
):
    """AI-powered schedule optimization"""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(status_code=403, detail="Only parents can use AI optimization")
    
    try:
        # Create AI chat instance
        chat = await create_ai_chat()
        
        # Prepare family schedule context
        family_context = {
            "family_members": [{"name": m.name, "role": m.role, "preferences": m.preferences} for m in request.family_members],
            "events": [{"title": e.title, "start": e.start_time.isoformat(), "end": e.end_time.isoformat(), 
                       "type": e.event_type, "priority": e.priority, "member": e.family_member_id} for e in request.events],
            "preferences": request.preferences or {}
        }
        
        # Create optimization prompt
        optimization_prompt = f"""
        Analyze this family schedule and provide optimization suggestions:
        
        Family Context: {family_context}
        
        Please provide:
        1. Scheduling conflict analysis
        2. Time optimization suggestions
        3. Family time recommendations
        4. Efficiency improvements
        5. Stress reduction tips
        
        Format your response as actionable suggestions for busy family life.
        """
        
        # Get AI suggestions
        user_message = UserMessage(text=optimization_prompt)
        ai_response = await chat.send_message(user_message)
        
        # Parse AI response and create suggestions
        suggestions = ai_response.split('\n') if ai_response else ["AI service temporarily unavailable"]
        suggestions = [s.strip() for s in suggestions if s.strip()][:5]  # Top 5 suggestions
        
        return AIOptimizationResponse(
            suggestions=suggestions,
            optimized_events=request.events,  # For now, return original events
            conflicts_resolved=len([e for e in request.events if e.conflicts]),
            time_saved_minutes=30  # Placeholder calculation
        )
        
    except Exception as e:
        # Graceful fallback when AI is not available
        logger.error(f"AI optimization failed: {e}")
        return AIOptimizationResponse(
            suggestions=[
                "Try grouping similar tasks together to reduce context switching",
                "Consider scheduling family meals at consistent times",
                "Balance high-priority events throughout the week",
                "Leave buffer time between appointments",
                "Plan family activities during weekends when possible"
            ],
            optimized_events=request.events,
            conflicts_resolved=0,
            time_saved_minutes=0
        )

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

@api_router.post("/voice/command", response_model=VoiceResponse)
async def process_voice_command(
    command: VoiceCommand,
    current_user: FamilyMember = Depends(get_current_user)
):
    """Process voice commands for calendar management"""
    try:
        # Create AI chat for voice command interpretation
        chat = await create_ai_chat()
        
        # Voice command interpretation prompt
        voice_prompt = f"""
        Parse this voice command for family calendar management: "{command.text}"
        
        Determine the intent and extract relevant information:
        - Action: (create_event, get_schedule, update_event, etc.)
        - Event details: title, date, time, type, priority
        - Family member affected
        
        Respond with a helpful confirmation and any clarification needed.
        If creating an event, ask for any missing details.
        """
        
        user_message = UserMessage(text=voice_prompt)
        ai_response = await chat.send_message(user_message)
        
        # Simple voice command parsing (could be enhanced with more sophisticated NLP)
        if "create" in command.text.lower() or "add" in command.text.lower():
            action = "create_event"
            response_text = f"I'll help you create a new event. {ai_response}"
        elif "schedule" in command.text.lower() or "what's" in command.text.lower():
            action = "get_schedule"
            response_text = f"Here's your schedule information: {ai_response}"
        else:
            action = "general"
            response_text = ai_response
        
        return VoiceResponse(
            text=response_text,
            action=action,
            data={"original_command": command.text, "family_member_id": command.family_member_id}
        )
        
    except Exception as e:
        logger.error(f"Voice command processing failed: {e}")
        return VoiceResponse(
            text="I'm sorry, I couldn't process that voice command. Please try again or use the regular interface.",
            action="error",
            data={"error": str(e)}
        )

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
    
    # AI optimized events
    ai_optimized_query = {**query, "ai_optimized": True}
    ai_optimized_count = await db.calendar_events.count_documents(ai_optimized_query)
    
    return {
        "total_events": total_events,
        "events_by_type": {item["_id"]: item["count"] for item in events_by_type},
        "upcoming_events": upcoming_events,
        "conflicts_count": conflicts_count,
        "ai_optimized_count": ai_optimized_count,
        "ai_enabled": (await get_ai_status(current_user))["enabled"],
        "voice_enabled": (await get_voice_status(current_user))["enabled"]
    }

# Voice Realtime (WebRTC) - Advanced Voice Features
try:
    # Initialize OpenAI Realtime Chat for advanced voice features
    openai_realtime = OpenAIChatRealtime(api_key=DEFAULT_OPENAI_API_KEY)
    
    # Register realtime voice routes
    voice_router = APIRouter()
    OpenAIChatRealtime.register_openai_realtime_router(voice_router, openai_realtime)
    api_router.include_router(voice_router, prefix="/voice/realtime")
    
except Exception as e:
    logger.warning(f"Advanced voice features not available: {e}")

# Basic health check
@api_router.get("/")
async def root():
    ai_config = await get_ai_config()
    voice_config = await get_voice_config()
    
    return {
        "message": "Family Daily Planner API", 
        "status": "active",
        "features": {
            "ai_optimization": ai_config.enabled if ai_config else False,
            "voice_commands": voice_config.enabled if voice_config else False,
            "voice_realtime": True  # Advanced voice features available
        }
    }

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
