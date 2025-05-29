import React, { useState, useEffect, useRef } from "react";
import { useFamilyContext } from "./App";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// AI Configuration Component
export const AIConfigurationModal = ({ isOpen, onClose, onSave }) => {
  const { user } = useFamilyContext();
  const [config, setConfig] = useState({
    provider: "openai",
    api_key: "",
    model: "gpt-4o",
    enabled: false
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadCurrentConfig();
    }
  }, [isOpen]);

  const loadCurrentConfig = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/ai/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.provider) {
        setConfig(response.data);
      }
    } catch (error) {
      console.error('Failed to load AI config:', error);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/ai/configure`, config, {
        headers: { Authorization: `Bearer ${token}` }
      });
      onSave();
      onClose();
    } catch (error) {
      console.error('Failed to save AI config:', error);
      alert('Failed to save AI configuration');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">AI Optimization</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
            <select
              value={config.provider}
              onChange={(e) => setConfig({ ...config, provider: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="openai">OpenAI</option>
              <option value="local">Local LLM</option>
              <option value="anthropic">Anthropic Claude</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
            <input
              type="password"
              value={config.api_key}
              onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter your API key or use placeholder for demo"
            />
            <p className="text-xs text-gray-500 mt-1">
              Leave empty to use demo mode with placeholder key
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
            <select
              value={config.model}
              onChange={(e) => setConfig({ ...config, model: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="claude-sonnet-4-20250514">Claude Sonnet 4</option>
              <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="ai-enabled"
              checked={config.enabled}
              onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
              className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
            />
            <label htmlFor="ai-enabled" className="ml-2 text-sm text-gray-700">
              Enable AI optimization
            </label>
          </div>

          <div className="bg-purple-50 p-4 rounded-lg">
            <h4 className="font-medium text-purple-900 mb-2">AI Features:</h4>
            <ul className="text-sm text-purple-700 space-y-1">
              <li>• Intelligent scheduling optimization</li>
              <li>• Conflict detection and resolution</li>
              <li>• Family time recommendations</li>
              <li>• Efficiency improvements</li>
            </ul>
          </div>
        </div>

        <div className="flex space-x-3 pt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex-1 bg-gradient-to-r from-purple-500 to-indigo-600 text-white py-2 px-4 rounded-xl hover:from-purple-600 hover:to-indigo-700 transition-all duration-200 disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Voice Configuration Component
export const VoiceConfigurationModal = ({ isOpen, onClose, onSave }) => {
  const [config, setConfig] = useState({
    provider: "openai",
    api_key: "",
    enabled: false
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadCurrentConfig();
    }
  }, [isOpen]);

  const loadCurrentConfig = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/voice/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.provider) {
        setConfig(response.data);
      }
    } catch (error) {
      console.error('Failed to load voice config:', error);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/voice/configure`, config, {
        headers: { Authorization: `Bearer ${token}` }
      });
      onSave();
      onClose();
    } catch (error) {
      console.error('Failed to save voice config:', error);
      alert('Failed to save voice configuration');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Voice Commands</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
            <select
              value={config.provider}
              onChange={(e) => setConfig({ ...config, provider: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="openai">OpenAI</option>
              <option value="google">Google Speech</option>
              <option value="azure">Azure Speech</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
            <input
              type="password"
              value={config.api_key}
              onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter your API key or use placeholder for demo"
            />
            <p className="text-xs text-gray-500 mt-1">
              Leave empty to use demo mode with placeholder key
            </p>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="voice-enabled"
              checked={config.enabled}
              onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
              className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
            />
            <label htmlFor="voice-enabled" className="ml-2 text-sm text-gray-700">
              Enable voice commands
            </label>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">Voice Features:</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• "Add family dinner for tomorrow at 6 PM"</li>
              <li>• "What's on my schedule today?"</li>
              <li>• "Create a doctor appointment for Sarah"</li>
              <li>• Real-time voice interactions</li>
            </ul>
          </div>
        </div>

        <div className="flex space-x-3 pt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex-1 bg-gradient-to-r from-blue-500 to-cyan-600 text-white py-2 px-4 rounded-xl hover:from-blue-600 hover:to-cyan-700 transition-all duration-200 disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Voice Command Component
export const VoiceCommandInterface = ({ onVoiceCommand }) => {
  const { user } = useFamilyContext();
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [voiceConfig, setVoiceConfig] = useState(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    loadVoiceConfig();
    initializeSpeechRecognition();
  }, []);

  const loadVoiceConfig = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/voice/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVoiceConfig(response.data);
    } catch (error) {
      console.error('Failed to load voice config:', error);
    }
  };

  const initializeSpeechRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onstart = () => {
        setIsListening(true);
      };

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setTranscript(transcript);
        processVoiceCommand(transcript);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  };

  const processVoiceCommand = async (text) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/voice/command`, {
        text,
        family_member_id: user.id
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Handle voice response
      if (response.data.text && 'speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(response.data.text);
        speechSynthesis.speak(utterance);
      }

      if (onVoiceCommand) {
        onVoiceCommand(response.data);
      }
    } catch (error) {
      console.error('Failed to process voice command:', error);
    }
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setTranscript('');
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  if (!voiceConfig?.enabled) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Voice Commands</h3>
        <div className={`w-3 h-3 rounded-full ${voiceConfig?.enabled ? 'bg-green-400' : 'bg-gray-400'}`}></div>
      </div>

      <div className="text-center">
        <button
          onClick={isListening ? stopListening : startListening}
          className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-200 ${
            isListening 
              ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
              : 'bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700'
          }`}
        >
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2a4 4 0 014 4v6a4 4 0 01-8 0V6a4 4 0 014-4z" />
            <path d="M19 10v2a7 7 0 01-14 0v-2" />
            <path d="M12 19v4" />
            <path d="M8 23h8" />
          </svg>
        </button>
        
        <p className="text-sm text-gray-600 mt-2">
          {isListening ? 'Listening...' : 'Tap to speak'}
        </p>
        
        {transcript && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-700">"{transcript}"</p>
          </div>
        )}
      </div>

      <div className="mt-4 text-xs text-gray-500 space-y-1">
        <p>Try saying:</p>
        <p>• "Add family dinner tomorrow at 6 PM"</p>
        <p>• "What's on my schedule today?"</p>
        <p>• "Create a doctor appointment for next week"</p>
      </div>
    </div>
  );
};

// AI Optimization Component
export const AIOptimizationPanel = ({ events, familyMembers, onOptimize }) => {
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [aiConfig, setAiConfig] = useState(null);

  useEffect(() => {
    loadAIConfig();
  }, []);

  const loadAIConfig = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/ai/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAiConfig(response.data);
    } catch (error) {
      console.error('Failed to load AI config:', error);
    }
  };

  const runOptimization = async () => {
    setIsOptimizing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/ai/optimize`, {
        events: events.slice(0, 50), // Limit for performance
        family_members: familyMembers,
        preferences: {
          optimize_for: "family_time",
          minimize_conflicts: true,
          balance_workload: true
        }
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setOptimizationResult(response.data);
      if (onOptimize) {
        onOptimize(response.data);
      }
    } catch (error) {
      console.error('Optimization failed:', error);
    } finally {
      setIsOptimizing(false);
    }
  };

  if (!aiConfig?.enabled) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">AI Optimization</h3>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${aiConfig?.enabled ? 'bg-green-400' : 'bg-gray-400'}`}></div>
          <span className="text-sm text-gray-600">{aiConfig?.model || 'Not configured'}</span>
        </div>
      </div>

      <div className="space-y-4">
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-4 rounded-lg">
          <p className="text-sm text-purple-700 mb-3">
            AI can analyze your family's schedule and provide intelligent optimization suggestions.
          </p>
          <button
            onClick={runOptimization}
            disabled={isOptimizing}
            className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:from-purple-600 hover:to-indigo-700 transition-all duration-200 disabled:opacity-50"
          >
            {isOptimizing ? 'Optimizing...' : 'Optimize Schedule'}
          </button>
        </div>

        {optimizationResult && (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Optimization Results</h4>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-green-50 p-3 rounded-lg">
                <p className="text-sm font-medium text-green-900">Conflicts Resolved</p>
                <p className="text-2xl font-bold text-green-700">{optimizationResult.conflicts_resolved}</p>
              </div>
              <div className="bg-blue-50 p-3 rounded-lg">
                <p className="text-sm font-medium text-blue-900">Time Saved</p>
                <p className="text-2xl font-bold text-blue-700">{optimizationResult.time_saved_minutes}min</p>
              </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h5 className="font-medium text-gray-900 mb-2">AI Suggestions:</h5>
              <ul className="space-y-1">
                {optimizationResult.suggestions.map((suggestion, index) => (
                  <li key={index} className="text-sm text-gray-700 flex items-start">
                    <span className="text-purple-500 mr-2">•</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Stats Card Component
export const EnhancedStatsCard = ({ title, value, icon, gradient, subtitle }) => {
  return (
    <div className={`stats-card ${gradient}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-white/80 text-sm font-medium">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {subtitle && <p className="text-white/70 text-xs mt-1">{subtitle}</p>}
        </div>
        <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
          {icon}
        </div>
      </div>
    </div>
  );
};
