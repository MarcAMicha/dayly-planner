import requests
import json
from datetime import datetime, timedelta
import time
import unittest
import sys

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://841c2e20-6917-40c7-9fc7-5f1e1cb3d56e.preview.emergentagent.com/api"

class FamilyPlannerBackendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test data and clean the database for a fresh start"""
        print(f"Testing backend API at: {BACKEND_URL}")
        
        # Test basic health check
        response = requests.get(f"{BACKEND_URL}/")
        assert response.status_code == 200, f"API health check failed: {response.text}"
        print("✅ API health check passed")
        
        # Create test family members
        cls.family_members = []
        cls.access_tokens = {}
        
        # Create 2 parents and 3 children
        cls.create_test_family()
    
    @classmethod
    def create_test_family(cls):
        """Create a test family with 2 parents and 3 children"""
        # Create parents
        parent1 = cls.create_family_member("Parent One", "parent1@example.com", "parent")
        parent2 = cls.create_family_member("Parent Two", "parent2@example.com", "parent")
        
        # Create children
        child1 = cls.create_family_member("Child One", "child1@example.com", "child")
        child2 = cls.create_family_member("Child Two", "child2@example.com", "child")
        child3 = cls.create_family_member("Child Three", "child3@example.com", "child")
        
        # Login with each family member to get access tokens
        for member in [parent1, parent2, child1, child2, child3]:
            cls.login_family_member(member)
    
    @classmethod
    def create_family_member(cls, name, email, role):
        """Create a family member and return the created member data"""
        payload = {
            "name": name,
            "email": email,
            "role": role,
            "color": "#6366f1"  # Default purple color
        }
        
        response = requests.post(f"{BACKEND_URL}/family-members", json=payload)
        
        if response.status_code == 400 and "Email already registered" in response.text:
            # If member already exists, try to login instead
            print(f"Member {email} already exists, skipping creation")
            return {"email": email}
        
        assert response.status_code == 200, f"Failed to create family member: {response.text}"
        member_data = response.json()
        cls.family_members.append(member_data)
        print(f"✅ Created family member: {name} ({role})")
        return member_data
    
    @classmethod
    def login_family_member(cls, member):
        """Login with a family member and store the access token"""
        payload = {"email": member["email"]}
        response = requests.post(f"{BACKEND_URL}/auth/login", json=payload)
        assert response.status_code == 200, f"Failed to login: {response.text}"
        
        data = response.json()
        cls.access_tokens[member["email"]] = data["access_token"]
        print(f"✅ Logged in as: {member['email']}")
        return data
    
    def get_auth_header(self, email):
        """Get the authorization header for a family member"""
        token = self.access_tokens.get(email)
        if not token:
            raise ValueError(f"No token found for {email}")
        return {"Authorization": f"Bearer {token}"}
    
    def test_01_family_member_management(self):
        """Test family member management APIs"""
        print("\n=== Testing Family Member Management API ===")
        
        # Test getting all family members as a parent
        headers = self.get_auth_header("parent1@example.com")
        response = requests.get(f"{BACKEND_URL}/family-members", headers=headers)
        self.assertEqual(response.status_code, 200)
        members = response.json()
        self.assertGreaterEqual(len(members), 5)  # At least our 5 test members
        print("✅ Parent can get all family members")
        
        # Test getting current user profile
        response = requests.get(f"{BACKEND_URL}/family-members/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        profile = response.json()
        self.assertEqual(profile["email"], "parent1@example.com")
        print("✅ Get current user profile works")
        
        # Test updating a family member as a parent
        parent_id = next(m["id"] for m in members if m["email"] == "parent1@example.com")
        update_payload = {"preferences": {"theme": "dark"}}
        response = requests.put(
            f"{BACKEND_URL}/family-members/{parent_id}", 
            json=update_payload,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        updated_member = response.json()
        self.assertEqual(updated_member["preferences"]["theme"], "dark")
        print("✅ Parent can update their own profile")
        
        # Test parent updating a child's profile
        child_id = next(m["id"] for m in members if m["email"] == "child1@example.com")
        update_payload = {"preferences": {"bedtime": "21:00"}}
        response = requests.put(
            f"{BACKEND_URL}/family-members/{child_id}", 
            json=update_payload,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Parent can update child's profile")
        
        # Test child trying to update parent's profile (should fail)
        child_headers = self.get_auth_header("child1@example.com")
        update_payload = {"preferences": {"theme": "light"}}
        response = requests.put(
            f"{BACKEND_URL}/family-members/{parent_id}", 
            json=update_payload,
            headers=child_headers
        )
        self.assertEqual(response.status_code, 403)
        print("✅ Child cannot update parent's profile (permission denied)")
        
        # Test child updating their own profile (should succeed)
        child_id = next(m["id"] for m in members if m["email"] == "child1@example.com")
        update_payload = {"preferences": {"favorite_color": "blue"}}
        response = requests.put(
            f"{BACKEND_URL}/family-members/{child_id}", 
            json=update_payload,
            headers=child_headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Child can update their own profile")
    
    def test_02_authentication_system(self):
        """Test authentication system"""
        print("\n=== Testing Authentication System ===")
        
        # Test login with valid credentials
        payload = {"email": "parent1@example.com"}
        response = requests.post(f"{BACKEND_URL}/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        print("✅ Login with valid credentials works")
        
        # Test login with invalid credentials
        payload = {"email": "nonexistent@example.com"}
        response = requests.post(f"{BACKEND_URL}/auth/login", json=payload)
        self.assertEqual(response.status_code, 404)
        print("✅ Login with invalid credentials fails correctly")
        
        # Test accessing protected endpoint without token
        response = requests.get(f"{BACKEND_URL}/family-members")
        self.assertEqual(response.status_code, 403)
        print("✅ Accessing protected endpoint without token fails correctly")
        
        # Test accessing protected endpoint with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{BACKEND_URL}/family-members", headers=headers)
        self.assertEqual(response.status_code, 401)
        print("✅ Accessing protected endpoint with invalid token fails correctly")
        
        # Test accessing protected endpoint with valid token
        headers = self.get_auth_header("parent1@example.com")
        response = requests.get(f"{BACKEND_URL}/family-members", headers=headers)
        self.assertEqual(response.status_code, 200)
        print("✅ Accessing protected endpoint with valid token works")
    
    def test_03_calendar_event_management(self):
        """Test calendar event management APIs"""
        print("\n=== Testing Calendar Event Management API ===")
        
        # Get family member IDs
        headers = self.get_auth_header("parent1@example.com")
        response = requests.get(f"{BACKEND_URL}/family-members", headers=headers)
        members = response.json()
        
        parent1_id = next(m["id"] for m in members if m["email"] == "parent1@example.com")
        parent2_id = next(m["id"] for m in members if m["email"] == "parent2@example.com")
        child1_id = next(m["id"] for m in members if m["email"] == "child1@example.com")
        
        # Test creating an event as a parent
        now = datetime.utcnow()
        event_payload = {
            "title": "Family Dinner",
            "description": "Weekly family dinner",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=2)).isoformat(),
            "event_type": "family_time",
            "priority": "high",
            "family_member_id": parent1_id,
            "attendees": [parent1_id, parent2_id, child1_id],
            "location": "Home",
            "reminder_minutes": 30
        }
        
        response = requests.post(
            f"{BACKEND_URL}/events", 
            json=event_payload,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        event1 = response.json()
        self.assertEqual(event1["title"], "Family Dinner")
        print("✅ Parent can create an event")
        
        # Test creating an overlapping event to check conflict detection
        conflict_event_payload = {
            "title": "Conflicting Event",
            "description": "This should conflict with Family Dinner",
            "start_time": (now + timedelta(days=1, minutes=30)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=1, minutes=30)).isoformat(),
            "event_type": "appointment",
            "priority": "medium",
            "family_member_id": parent1_id,
            "location": "Somewhere else"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/events", 
            json=conflict_event_payload,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        conflict_event = response.json()
        self.assertGreaterEqual(len(conflict_event["conflicts"]), 1)
        print("✅ Conflict detection works for overlapping events")
        
        # Test creating an event for a child as a parent
        child_event_payload = {
            "title": "Homework Time",
            "description": "Math homework",
            "start_time": (now + timedelta(days=2)).isoformat(),
            "end_time": (now + timedelta(days=2, hours=1)).isoformat(),
            "event_type": "task",
            "priority": "high",
            "family_member_id": child1_id
        }
        
        response = requests.post(
            f"{BACKEND_URL}/events", 
            json=child_event_payload,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        child_event = response.json()
        print("✅ Parent can create an event for a child")
        
        # Test child creating their own event
        child_headers = self.get_auth_header("child1@example.com")
        child_own_event_payload = {
            "title": "Play Time",
            "description": "Video games",
            "start_time": (now + timedelta(days=3)).isoformat(),
            "end_time": (now + timedelta(days=3, hours=1)).isoformat(),
            "event_type": "task",
            "priority": "low",
            "family_member_id": child1_id
        }
        
        response = requests.post(
            f"{BACKEND_URL}/events", 
            json=child_own_event_payload,
            headers=child_headers
        )
        self.assertEqual(response.status_code, 200)
        child_own_event = response.json()
        print("✅ Child can create their own event")
        
        # Test child trying to create an event for parent (should fail)
        parent_event_payload = {
            "title": "Parent Event",
            "description": "This should fail",
            "start_time": (now + timedelta(days=4)).isoformat(),
            "end_time": (now + timedelta(days=4, hours=1)).isoformat(),
            "event_type": "appointment",
            "priority": "medium",
            "family_member_id": parent1_id
        }
        
        response = requests.post(
            f"{BACKEND_URL}/events", 
            json=parent_event_payload,
            headers=child_headers
        )
        self.assertEqual(response.status_code, 403)
        print("✅ Child cannot create an event for a parent (permission denied)")
        
        # Test getting all events as a parent
        response = requests.get(f"{BACKEND_URL}/events", headers=headers)
        self.assertEqual(response.status_code, 200)
        events = response.json()
        self.assertGreaterEqual(len(events), 3)  # At least our 3 test events
        print("✅ Parent can get all events")
        
        # Test getting events for a specific family member
        response = requests.get(
            f"{BACKEND_URL}/events?family_member_id={child1_id}", 
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        child_events = response.json()
        for event in child_events:
            self.assertEqual(event["family_member_id"], child1_id)
        print("✅ Parent can get events for a specific family member")
        
        # Test child getting their own events
        response = requests.get(f"{BACKEND_URL}/events", headers=child_headers)
        self.assertEqual(response.status_code, 200)
        own_events = response.json()
        for event in own_events:
            self.assertEqual(event["family_member_id"], child1_id)
        print("✅ Child can only see their own events")
        
        # Test updating an event as a parent
        update_payload = {"title": "Updated Family Dinner", "priority": "medium"}
        response = requests.put(
            f"{BACKEND_URL}/events/{event1['id']}", 
            json=update_payload,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        updated_event = response.json()
        self.assertEqual(updated_event["title"], "Updated Family Dinner")
        self.assertEqual(updated_event["priority"], "medium")
        print("✅ Parent can update an event")
        
        # Test child updating their own event
        update_payload = {"title": "Updated Play Time"}
        response = requests.put(
            f"{BACKEND_URL}/events/{child_own_event['id']}", 
            json=update_payload,
            headers=child_headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Child can update their own event")
        
        # Test child trying to update parent's event (should fail)
        update_payload = {"title": "Hacked Event"}
        response = requests.put(
            f"{BACKEND_URL}/events/{event1['id']}", 
            json=update_payload,
            headers=child_headers
        )
        self.assertEqual(response.status_code, 403)
        print("✅ Child cannot update parent's event (permission denied)")
        
        # Test deleting an event as a parent
        response = requests.delete(
            f"{BACKEND_URL}/events/{conflict_event['id']}", 
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Parent can delete an event")
        
        # Test child deleting their own event
        response = requests.delete(
            f"{BACKEND_URL}/events/{child_own_event['id']}", 
            headers=child_headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Child can delete their own event")
        
        # Test child trying to delete parent's event (should fail)
        response = requests.delete(
            f"{BACKEND_URL}/events/{event1['id']}", 
            headers=child_headers
        )
        self.assertEqual(response.status_code, 403)
        print("✅ Child cannot delete parent's event (permission denied)")
    
    def test_04_dashboard_statistics(self):
        """Test dashboard statistics API"""
        print("\n=== Testing Dashboard Statistics API ===")
        
        # Test getting dashboard stats as a parent
        headers = self.get_auth_header("parent1@example.com")
        response = requests.get(f"{BACKEND_URL}/dashboard/stats", headers=headers)
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        
        # Verify stats structure
        self.assertIn("total_events", stats)
        self.assertIn("events_by_type", stats)
        self.assertIn("upcoming_events", stats)
        self.assertIn("conflicts_count", stats)
        print("✅ Parent can get family dashboard stats")
        
        # Test getting dashboard stats as a child
        child_headers = self.get_auth_header("child1@example.com")
        response = requests.get(f"{BACKEND_URL}/dashboard/stats", headers=child_headers)
        self.assertEqual(response.status_code, 200)
        child_stats = response.json()
        
        # Child should only see their own stats
        print("✅ Child can get their own dashboard stats")
        
        # Verify that child stats are a subset of family stats
        self.assertLessEqual(child_stats["total_events"], stats["total_events"])
        print("✅ Child stats are correctly filtered")
    
    def test_05_modular_ai_service(self):
        """Test modular AI service configuration"""
        print("\n=== Testing Modular AI Service API ===")
        
        # Test configuring AI service as a parent
        headers = self.get_auth_header("parent1@example.com")
        ai_config = {
            "provider": "openai",
            "api_key": "test_key",
            "model": "gpt-3.5-turbo",
            "enabled": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/ai/configure", 
            json=ai_config,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Parent can configure AI service")
        
        # Test getting AI status
        response = requests.get(f"{BACKEND_URL}/ai/status", headers=headers)
        self.assertEqual(response.status_code, 200)
        status = response.json()
        self.assertEqual(status["provider"], "openai")
        self.assertEqual(status["enabled"], True)
        print("✅ Getting AI service status works")
        
        # Test child trying to configure AI service (should fail)
        child_headers = self.get_auth_header("child1@example.com")
        response = requests.post(
            f"{BACKEND_URL}/ai/configure", 
            json=ai_config,
            headers=child_headers
        )
        self.assertEqual(response.status_code, 403)
        print("✅ Child cannot configure AI service (permission denied)")
    
    def test_06_modular_voice_service(self):
        """Test modular voice service configuration"""
        print("\n=== Testing Modular Voice Service API ===")
        
        # Test configuring voice service as a parent
        headers = self.get_auth_header("parent1@example.com")
        voice_config = {
            "provider": "google",
            "api_key": "test_key",
            "enabled": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/voice/configure", 
            json=voice_config,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Parent can configure voice service")
        
        # Test getting voice status
        response = requests.get(f"{BACKEND_URL}/voice/status", headers=headers)
        self.assertEqual(response.status_code, 200)
        status = response.json()
        self.assertEqual(status["provider"], "google")
        self.assertEqual(status["enabled"], True)
        print("✅ Getting voice service status works")
        
        # Test child trying to configure voice service (should fail)
        child_headers = self.get_auth_header("child1@example.com")
        response = requests.post(
            f"{BACKEND_URL}/voice/configure", 
            json=voice_config,
            headers=child_headers
        )
        self.assertEqual(response.status_code, 403)
        print("✅ Child cannot configure voice service (permission denied)")

if __name__ == "__main__":
    # Run the tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)