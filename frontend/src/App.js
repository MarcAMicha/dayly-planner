import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { 
  AIConfigurationModal, 
  VoiceConfigurationModal, 
  VoiceCommandInterface, 
  AIOptimizationPanel,
  EnhancedStatsCard 
} from "./components";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Context for family and auth state
const FamilyContext = createContext();

// Custom hook to use family context
export const useFamilyContext = () => {
  const context = useContext(FamilyContext);
  if (!context) {
    throw new Error('useFamilyContext must be used within FamilyProvider');
  }
  return context;
};

// Family Provider Component
const FamilyProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [familyMembers, setFamilyMembers] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedMember, setSelectedMember] = useState(null);

  // Auth functions
  const login = async (email) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email });
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      setUser(user);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setFamilyMembers([]);
    setEvents([]);
  };

  // Data loading functions
  const loadFamilyMembers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/family-members`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFamilyMembers(response.data);
    } catch (error) {
      console.error('Failed to load family members:', error);
    }
  };

  const loadEvents = async (memberId = null, startDate = null, endDate = null) => {
    try {
      const token = localStorage.getItem('token');
      let params = {};
      if (memberId) params.family_member_id = memberId;
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();

      const response = await axios.get(`${API}/events`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });
      setEvents(response.data);
    } catch (error) {
      console.error('Failed to load events:', error);
    }
  };

  // Check for existing token on app load
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await axios.get(`${API}/family-members/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setUser(response.data);
        } catch (error) {
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  // Load family data when user is authenticated
  useEffect(() => {
    if (user) {
      loadFamilyMembers();
      loadEvents();
    }
  }, [user]);

  const value = {
    user,
    familyMembers,
    events,
    loading,
    selectedDate,
    selectedMember,
    setSelectedDate,
    setSelectedMember,
    login,
    logout,
    loadFamilyMembers,
    loadEvents
  };

  return (
    <FamilyContext.Provider value={value}>
      {children}
    </FamilyContext.Provider>
  );
};

// Login Component
const Login = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useFamilyContext();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    const success = await login(email);
    if (!success) {
      alert('Login failed. Please check your email.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a4 4 0 118 0v4m-4 8a2 2 0 100-4 2 2 0 000 4zm0 0v4a4 4 0 008 0v-4" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Family Daily Planner</h1>
          <p className="text-gray-600">Sign in to your family account</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter your email"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 text-white font-semibold py-3 px-4 rounded-xl hover:from-purple-600 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Demo accounts: parent1@example.com, child1@example.com
          </p>
        </div>
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = () => {
  const { user, logout, familyMembers, selectedMember, setSelectedMember } = useFamilyContext();

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a4 4 0 118 0v4m-4 8a2 2 0 100-4 2 2 0 000 4zm0 0v4a4 4 0 008 0v-4" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-gray-900">Family Planner</h1>
            <div className="hidden sm:flex items-center space-x-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                🤖 AI Ready
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                🎤 Voice Ready
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {user?.role === 'parent' && (
              <select
                value={selectedMember || ''}
                onChange={(e) => setSelectedMember(e.target.value || null)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="">All Family Members</option>
                {familyMembers.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.name}
                  </option>
                ))}
              </select>
            )}

            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${user?.color || '#6366f1'}`} style={{backgroundColor: user?.color}}></div>
              <span className="text-sm font-medium text-gray-700">{user?.name}</span>
              <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                {user?.role}
              </span>
            </div>

            <button
              onClick={logout}
              className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user, events, familyMembers, selectedMember, selectedDate, setSelectedDate, loadEvents } = useFamilyContext();
  const [showEventModal, setShowEventModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [stats, setStats] = useState(null);
  const [showAIConfig, setShowAIConfig] = useState(false);
  const [showVoiceConfig, setShowVoiceConfig] = useState(false);

  // Load dashboard stats
  useEffect(() => {
    const loadStats = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API}/dashboard/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setStats(response.data);
      } catch (error) {
        console.error('Failed to load stats:', error);
      }
    };
    loadStats();
  }, [events]);

  // Filter events based on selected member and date
  const filteredEvents = events.filter(event => {
    const eventDate = new Date(event.start_time);
    const isToday = eventDate.toDateString() === selectedDate.toDateString();
    const memberMatch = !selectedMember || event.family_member_id === selectedMember;
    return isToday && memberMatch;
  });

  const upcomingEvents = events
    .filter(event => new Date(event.start_time) >= new Date())
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
    .slice(0, 5);

  const getMemberById = (id) => familyMembers.find(m => m.id === id);

  const handleVoiceCommand = (response) => {
    console.log('Voice command result:', response);
    // Refresh events if voice command created/modified events
    loadEvents();
  };

  const handleAIOptimization = (result) => {
    console.log('AI optimization result:', result);
    // Refresh data after optimization
    loadEvents();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back, {user?.name}! 👋
        </h2>
        <p className="text-gray-600">Here's what's happening with your family today.</p>
      </div>

      {/* Enhanced Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <EnhancedStatsCard
            title="Total Events"
            value={stats.total_events}
            gradient="stats-card-total"
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a4 4 0 118 0v4m-4 8a2 2 0 100-4 2 2 0 000 4zm0 0v4a4 4 0 008 0v-4" />
              </svg>
            }
          />

          <EnhancedStatsCard
            title="Upcoming"
            value={stats.upcoming_events}
            subtitle="Next 7 days"
            gradient="stats-card-upcoming"
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />

          <EnhancedStatsCard
            title="AI Optimized"
            value={stats.ai_optimized_count || 0}
            subtitle={stats.ai_enabled ? "AI Active" : "AI Inactive"}
            gradient="stats-card-tasks"
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            }
          />

          <EnhancedStatsCard
            title="Conflicts"
            value={stats.conflicts_count}
            subtitle="Needs attention"
            gradient="stats-card-conflicts"
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            }
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Today's Events */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900">Today's Schedule</h3>
              <div className="flex items-center space-x-3">
                <input
                  type="date"
                  value={selectedDate.toISOString().split('T')[0]}
                  onChange={(e) => setSelectedDate(new Date(e.target.value))}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <button
                  onClick={() => setShowEventModal(true)}
                  className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:from-purple-600 hover:to-indigo-700 transition-all duration-200"
                >
                  Add Event
                </button>
              </div>
            </div>

            <div className="space-y-3">
              {filteredEvents.length === 0 ? (
                <div className="text-center py-8">
                  <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a4 4 0 118 0v4m-4 8a2 2 0 100-4 2 2 0 000 4zm0 0v4a4 4 0 008 0v-4" />
                  </svg>
                  <p className="text-gray-500">No events scheduled for this day</p>
                </div>
              ) : (
                filteredEvents.map((event) => {
                  const member = getMemberById(event.family_member_id);
                  const startTime = new Date(event.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                  const endTime = new Date(event.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                  
                  return (
                    <div key={event.id} className="flex items-center p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer">
                      <div className="w-3 h-3 rounded-full mr-4" style={{ backgroundColor: member?.color || '#6366f1' }}></div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h4 className="font-medium text-gray-900">{event.title}</h4>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            event.priority === 'high' ? 'bg-red-100 text-red-700' :
                            event.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                            {event.priority}
                          </span>
                          {event.ai_optimized && (
                            <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
                              🤖 AI
                            </span>
                          )}
                          {event.conflicts && event.conflicts.length > 0 && (
                            <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full">
                              Conflict
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">{startTime} - {endTime} • {member?.name}</p>
                        {event.description && (
                          <p className="text-sm text-gray-500 mt-1">{event.description}</p>
                        )}
                      </div>
                      <button
                        onClick={() => {
                          setEditingEvent(event);
                          setShowEventModal(true);
                        }}
                        className="text-purple-600 hover:text-purple-700 p-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* AI & Voice Features Sidebar */}
        <div className="space-y-6">
          {/* AI Configuration */}
          <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-2xl shadow-sm p-6 text-white">
            <h3 className="text-lg font-semibold mb-2">🤖 AI Optimization</h3>
            <p className="text-white/80 text-sm mb-4">
              {stats?.ai_enabled ? 'AI scheduling optimization is active' : 'Configure AI for intelligent scheduling'}
            </p>
            <button
              onClick={() => setShowAIConfig(true)}
              className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200"
            >
              {stats?.ai_enabled ? 'AI Settings' : 'Configure AI'}
            </button>
          </div>

          {/* Voice Configuration */}
          <div className="bg-gradient-to-r from-blue-500 to-cyan-600 rounded-2xl shadow-sm p-6 text-white">
            <h3 className="text-lg font-semibold mb-2">🎤 Voice Commands</h3>
            <p className="text-white/80 text-sm mb-4">
              {stats?.voice_enabled ? 'Voice commands are ready' : 'Configure voice input for hands-free scheduling'}
            </p>
            <button
              onClick={() => setShowVoiceConfig(true)}
              className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200"
            >
              {stats?.voice_enabled ? 'Voice Settings' : 'Configure Voice'}
            </button>
          </div>

          {/* Voice Command Interface */}
          <VoiceCommandInterface onVoiceCommand={handleVoiceCommand} />

          {/* AI Optimization Panel */}
          <AIOptimizationPanel 
            events={events} 
            familyMembers={familyMembers} 
            onOptimize={handleAIOptimization}
          />

          {/* Upcoming Events */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Events</h3>
            <div className="space-y-3">
              {upcomingEvents.slice(0, 5).map((event) => {
                const member = getMemberById(event.family_member_id);
                const eventDate = new Date(event.start_time);
                
                return (
                  <div key={event.id} className="flex items-start space-x-3">
                    <div className="w-2 h-2 rounded-full mt-2" style={{ backgroundColor: member?.color || '#6366f1' }}></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{event.title}</p>
                      <p className="text-xs text-gray-500">
                        {eventDate.toLocaleDateString()} • {member?.name}
                      </p>
                    </div>
                  </div>
                );
              })}
              {upcomingEvents.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">No upcoming events</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      {showEventModal && (
        <EventModal
          event={editingEvent}
          onClose={() => {
            setShowEventModal(false);
            setEditingEvent(null);
          }}
          onSave={() => {
            loadEvents();
            setShowEventModal(false);
            setEditingEvent(null);
          }}
        />
      )}

      <AIConfigurationModal
        isOpen={showAIConfig}
        onClose={() => setShowAIConfig(false)}
        onSave={() => {
          loadEvents();
          setShowAIConfig(false);
        }}
      />

      <VoiceConfigurationModal
        isOpen={showVoiceConfig}
        onClose={() => setShowVoiceConfig(false)}
        onSave={() => {
          loadEvents();
          setShowVoiceConfig(false);
        }}
      />
    </div>
  );
};

// Event Modal Component
const EventModal = ({ event, onClose, onSave }) => {
  const { user, familyMembers } = useFamilyContext();
  const [formData, setFormData] = useState({
    title: event?.title || '',
    description: event?.description || '',
    start_time: event?.start_time || new Date().toISOString().slice(0, 16),
    end_time: event?.end_time || new Date(Date.now() + 3600000).toISOString().slice(0, 16),
    event_type: event?.event_type || 'task',
    priority: event?.priority || 'medium',
    family_member_id: event?.family_member_id || user?.id,
    location: event?.location || '',
    reminder_minutes: event?.reminder_minutes || 15
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      
      if (event) {
        // Update existing event
        await axios.put(`${API}/events/${event.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        // Create new event
        await axios.post(`${API}/events`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      
      onSave();
    } catch (error) {
      console.error('Failed to save event:', error);
      alert('Failed to save event. Please try again.');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">
            {event ? 'Edit Event' : 'Create Event'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
              <input
                type="datetime-local"
                value={formData.start_time}
                onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Time</label>
              <input
                type="datetime-local"
                value={formData.end_time}
                onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select
                value={formData.event_type}
                onChange={(e) => setFormData({ ...formData, event_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="task">Task</option>
                <option value="appointment">Appointment</option>
                <option value="reminder">Reminder</option>
                <option value="family_time">Family Time</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>

          {user?.role === 'parent' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Assign to</label>
              <select
                value={formData.family_member_id}
                onChange={(e) => setFormData({ ...formData, family_member_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                {familyMembers.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Optional"
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 bg-gradient-to-r from-purple-500 to-indigo-600 text-white py-2 px-4 rounded-xl hover:from-purple-600 hover:to-indigo-700 transition-all duration-200"
            >
              {event ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <FamilyProvider>
      <div className="App min-h-screen bg-gray-50">
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </div>
    </FamilyProvider>
  );
}

// App Routes Component
const AppRoutes = () => {
  const { user, loading } = useFamilyContext();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a4 4 0 118 0v4m-4 8a2 2 0 100-4 2 2 0 000 4zm0 0v4a4 4 0 008 0v-4" />
            </svg>
          </div>
          <p className="text-gray-600">Loading your family planner...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  return (
    <>
      <Navigation />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
};

export default App;
