import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Send, 
  Upload, 
  X, 
  FileText, 
  Settings, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  StopCircle,
  LogOut,
  User as UserIcon,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import LoginPage from './LoginPage';
import './App.css';

// API configuration - can be overridden via environment variable
// In Kubernetes, nginx proxies /api to backend, so we use empty string in production
// For localhost development, connect directly to backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:5000' 
    : '');

function App() {
  // Authentication state
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  // Conversation management
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [expandedDocuments, setExpandedDocuments] = useState(new Set());
  const [showFileUpload, setShowFileUpload] = useState(false);
  
  // Settings
  const [showAnalysis, setShowAnalysis] = useState(true);
  const [autoGenerateCode, setAutoGenerateCode] = useState(true);
  const [deployServices, setDeployServices] = useState(true);
  
  // Chat Mode: 'normal', 'code', 'deploy'
  const [chatMode, setChatMode] = useState('normal');
  
  // API Status
  const [apiStatus, setApiStatus] = useState({ status: 'checking', message: 'Checking...' });
  const [vertexAIStatus, setVertexAIStatus] = useState({ status: 'checking', message: 'Checking...' });
  
  // Deployment
  const [backendUrl, setBackendUrl] = useState(null);
  const [frontendUrl, setFrontendUrl] = useState(null);
  const [deploymentId, setDeploymentId] = useState(null);
  
  // GCP Status
  const [gcpStatus, setGcpStatus] = useState({ 
    gcp: { configured: false }, 
    langchain_vertex_ai: { available: false } 
  });
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  
  // Check authentication on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    const storedToken = localStorage.getItem('authToken');
    
    if (storedUser && storedToken) {
      setUser(JSON.parse(storedUser));
      setIsAuthenticated(true);
      
      // Load conversations
      const storedConversations = localStorage.getItem('conversations');
      if (storedConversations) {
        const parsedConversations = JSON.parse(storedConversations);
        setConversations(parsedConversations);
        
        // Load the most recent conversation or create a new one
        if (parsedConversations.length > 0) {
          const lastConversation = parsedConversations[0];
          setCurrentConversationId(lastConversation.id);
          setMessages(lastConversation.messages);
        } else {
          createNewConversation();
        }
      } else {
        createNewConversation();
      }
    }
  }, []);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Save conversation when messages change
  useEffect(() => {
    if (currentConversationId && messages.length > 0) {
      saveCurrentConversation(messages);
    }
  }, [messages]);
  
  // Check API health on mount (only if authenticated)
  useEffect(() => {
    if (isAuthenticated) {
      checkAPIHealth();
      checkGCPStatus();
    }
  }, [isAuthenticated]);
  
  const checkAPIHealth = async () => {
    try {
      // Use /health directly (nginx proxies it to backend)
      const healthUrl = API_BASE_URL ? `${API_BASE_URL}/health` : '/health';
      const response = await axios.get(healthUrl, { timeout: 5000 });
      if (response.status === 200) {
        setApiStatus({ status: 'success', message: 'Flask API is running' });
        setVertexAIStatus({ status: 'success', message: 'Vertex AI is active' });
      }
    } catch (error) {
      setApiStatus({ status: 'error', message: 'Flask API not responding' });
      setVertexAIStatus({ status: 'error', message: 'Cannot connect to Vertex AI' });
    }
  };
  
  const checkGCPStatus = async () => {
    try {
      // Use /api/check-gcp-status (nginx proxies /api to backend)
      const gcpStatusUrl = API_BASE_URL 
        ? `${API_BASE_URL}/api/check-gcp-status` 
        : '/api/check-gcp-status';
      const response = await axios.get(gcpStatusUrl, { timeout: 5000 });
      if (response.data.status === 'success') {
        setGcpStatus(response.data);
      }
    } catch (error) {
      console.error('Error checking GCP status:', error);
    }
  };
  
  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    const maxFileSize = 50 * 1024 * 1024; // 50MB
    
    for (const file of files) {
      // Check file size
      if (file.size > maxFileSize) {
        alert(`File ${file.name} is too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Maximum size is 50MB.`);
        continue;
      }
      
      // Check if file is already uploaded
      if (uploadedFiles.some(f => f.name === file.name)) {
        alert(`File ${file.name} is already uploaded.`);
        continue;
      }
      
      try {
        // Create form data for file upload
        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_name', file.name);
        formData.append('file_type', file.type || '');
        
        // Process file through API
        const response = await axios.post(`${API_BASE_URL}/api/process-document`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 60000, // 60 seconds timeout for large files
        });
        
        if (response.data.status === 'success') {
          setUploadedFiles(prev => [...prev, {
            name: response.data.name,
            type: response.data.type,
            size: response.data.size,
            content: response.data.content,
            preview: response.data.preview
          }]);
        } else {
          alert(`Error processing ${file.name}: ${response.data.error || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Error processing file:', error);
        const errorMessage = error.response?.data?.detail || error.response?.data?.error || error.message || 'Unknown error';
        alert(`Error processing ${file.name}: ${errorMessage}`);
      }
    }
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
    setExpandedDocuments(prev => {
      const newSet = new Set(prev);
      newSet.delete(index);
      return newSet;
    });
  };
  
  const toggleDocumentPreview = (index) => {
    setExpandedDocuments(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };
  
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };
  
  const sendMessage = async () => {
    if (!inputValue.trim() && uploadedFiles.length === 0) return;
    
    // Prepare message with document context
    let messageContent = inputValue;
    const attachedDocs = uploadedFiles.map(f => f.name);
    
    if (uploadedFiles.length > 0) {
      let docContext = '\n\n--- Uploaded Documents Context ---\n';
      uploadedFiles.forEach(file => {
        docContext += `\n[Document: ${file.name}]\n${file.content}\n`;
      });
      messageContent = `${inputValue}\n${docContext}`;
    }
    
    // Add user message to chat
    const userMessage = {
      role: 'user',
      content: inputValue,
      documents: attachedDocs
    };
    
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputValue('');
    setIsProcessing(true);
    
    // Update conversation title if it's the first message
    if (messages.length === 0) {
      updateConversationTitle(currentConversationId, inputValue);
    }
    
    // Save conversation
    saveCurrentConversation(newMessages);
    
    // Determine request type based on chat mode
    let isCodeRequest = false;
    let isDeployRequest = false;
    
    if (chatMode === 'code') {
      // In code mode, always treat as code generation request
      isCodeRequest = true;
    } else if (chatMode === 'deploy') {
      // In deploy mode, always treat as chatbot deployment request
      isDeployRequest = true;
      isCodeRequest = true; // Deployment uses the same endpoint
    } else {
      // Normal mode - check keywords
      const codeKeywords = ['generate code', 'create code', 'write code', 'code for', 'generate a program',
                            'build an application', 'develop a system', 'create an app', 'write a program',
                            'create a chatbot', 'build a chatbot', 'chatbot', 'bot'];
      isCodeRequest = codeKeywords.some(keyword => messageContent.toLowerCase().includes(keyword));
    }
    
    try {
      if ((isCodeRequest || isDeployRequest) && autoGenerateCode) {
        // Full code generation workflow
        setProcessingStatus({
          currentStep: 1,
          steps: [
            '📋 Step 1: Analyzing requirements',
            '⚙️ Step 2: Generating backend code',
            '🎨 Step 3: Generating user interface',
            '🔗 Step 4: Integrating components',
            '🚀 Step 5: Deploying your application'
          ]
        });
        
        const response = await axios.post(`${API_BASE_URL}/api/generate-full-project`, {
          message: messageContent
        }, {
          timeout: 600000 // 10 minutes
        });
        
        if (response.data.status === 'success') {
          const { requirements_analysis, generated_code, project, deployment } = response.data;
          
          // Add requirements analysis if enabled
          if (showAnalysis && requirements_analysis.text) {
            setMessages(prev => [...prev, {
              role: 'system',
              content: `**Requirements Analysis:**\n\n${requirements_analysis.text}`
            }]);
          }
          
          // Format the response with code
          let responseContent = '';
          
          if (generated_code.backend) {
            responseContent += `## Generated Backend Code (Python)\n\`\`\`python\n${generated_code.backend}\n\`\`\`\n\n`;
          }
          
          if (generated_code.ui) {
            responseContent += `## Generated Frontend UI (React)\n\`\`\`jsx\n${generated_code.ui}\n\`\`\`\n\n`;
          }
          
          if (project.directory && project.exists) {
            responseContent += `## Project Integration\nA complete project has been assembled at: \`${project.directory}\`\n\n`;
            responseContent += `- Backend code is in the \`backend/\` directory\n`;
            responseContent += `- Frontend code is in the \`frontend/\` directory\n`;
            responseContent += `- A README.md with setup instructions is included\n\n`;
          }
          
          if (deployment.backend_url && deployment.frontend_url) {
            setBackendUrl(deployment.backend_url);
            setFrontendUrl(deployment.frontend_url);
            setDeploymentId(deployment.deployment_id || null);
            
            responseContent += `## Deployment\nYour application has been deployed and is running at:\n\n`;
            responseContent += `- Backend API: [${deployment.backend_url}](${deployment.backend_url})\n`;
            responseContent += `- Frontend UI: [${deployment.frontend_url}](${deployment.frontend_url})\n\n`;
            responseContent += `The services will remain running until you close this application or click "Stop Services".\n`;
          }
          
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: responseContent
          }]);
        }
      } else {
        // Regular chat mode
        if (chatMode === 'normal') {
          // Check if user is admin or regular user
          if (user?.role === 'user') {
            // Simple chat for regular users - direct Gemini chat
            setProcessingStatus({
              currentStep: 0,
              steps: ['Thinking...']
            });
            
            // Prepare conversation history for context
            const conversationHistory = messages.map(msg => ({
              role: msg.role,
              content: msg.content
            }));
            
            const response = await axios.post(`${API_BASE_URL}/api/simple-chat`, {
              message: messageContent,
              conversation_history: conversationHistory
            });
            
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: response.data.response || 'I understand your request. How can I help you further?'
            }]);
          } else {
            // Admin - use requirements analysis as chat response
            setProcessingStatus({
              currentStep: 0,
              steps: ['Thinking...']
            });
            
            const response = await axios.post(`${API_BASE_URL}/api/analyze-requirements`, {
              message: messageContent,
              output_format: 'text'
            });
            
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: response.data.result || 'I understand your request. How can I help you further?'
            }]);
          }
        } else {
          // Fallback to requirements analysis
          setProcessingStatus({
            currentStep: 0,
            steps: ['Analyzing requirements...']
          });
          
          const response = await axios.post(`${API_BASE_URL}/api/analyze-requirements`, {
            message: messageContent,
            output_format: 'text'
          });
          
          if (showAnalysis) {
            setMessages(prev => [...prev, {
              role: 'system',
              content: `**Requirements Analysis:**\n\n${response.data.result}`
            }]);
          }
          
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: `I've analyzed your requirements. ${autoGenerateCode ? 'If you\'d like me to generate code, please explicitly request it.' : ''}`
          }]);
        }
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error: ${errorMessage}\n\nPlease make sure the Flask API is running and try again.`
      }]);
    } finally {
      setIsProcessing(false);
      setProcessingStatus(null);
      setUploadedFiles([]);
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  
  // Feature button handlers
  const handleChatWithAI = () => {
    setChatMode('normal');
    setInputValue('');
    setUploadedFiles([]);
    // Add welcome message based on user role
    if (user?.role === 'user') {
      // Simple welcome for regular users - like Gemini chat
      setMessages([{
        role: 'assistant',
        content: 'Hello! How can I help you today?'
      }]);
    } else {
      // Detailed welcome for admin
      setMessages([{
        role: 'assistant',
        content: '👋 **Hello! I\'m your personalized AI agent.**\n\nI can help you with:\n\n- Answering questions\n- Providing explanations\n- Brainstorming ideas\n- Writing and editing\n- Problem solving\n- And much more!\n\nHow can I assist you today?'
      }]);
    }
  };
  
  const handleUploadDocuments = () => {
    // Trigger file upload
    fileInputRef.current?.click();
  };
  
  const handleGenerateCode = () => {
    setChatMode('code');
    setInputValue('');
    setUploadedFiles([]);
    // Add welcome message for code generation
    setMessages([{
      role: 'assistant',
      content: '⚡ **Code Generation Mode**\n\nI\'m your specialized code generation assistant! I can help you:\n\n- Write backend APIs (FastAPI, Flask, Django, etc.)\n- Create frontend components (React, Vue, Angular, etc.)\n- Build full-stack applications\n- Generate database schemas and models\n- Write tests and documentation\n- Create CLI tools and scripts\n\n**Example prompts:**\n- "Create a REST API for a todo app"\n- "Build a React component for a login form"\n- "Write a Python script to process CSV files"\n\nWhat would you like me to build?'
    }]);
  };
  
  const handleDeployChatbots = () => {
    setChatMode('deploy');
    setInputValue('');
    setUploadedFiles([]);
    // Add welcome message for chatbot deployment
    setMessages([{
      role: 'assistant',
      content: '🚀 **Chatbot Deployment Mode**\n\nI can create and deploy custom chatbots for you! Just describe what kind of chatbot you need:\n\n- Customer service chatbot\n- FAQ assistant\n- Technical support bot\n- E-commerce helper\n- Educational tutor\n- Healthcare assistant\n- Or any specialized chatbot\n\n**Example prompts:**\n- "Create a customer service chatbot for a hotel"\n- "Build a FAQ bot for my website"\n- "Make a technical support assistant"\n\nI\'ll generate the complete project (backend + frontend) and deploy it automatically!'
    }]);
  };
  
  const createNewConversation = () => {
    const newConversation = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    const updatedConversations = [newConversation, ...conversations];
    setConversations(updatedConversations);
    setCurrentConversationId(newConversation.id);
    setMessages([]);
    setUploadedFiles([]);
    
    // Save to localStorage
    localStorage.setItem('conversations', JSON.stringify(updatedConversations));
  };
  
  const switchConversation = (conversationId) => {
    const conversation = conversations.find(c => c.id === conversationId);
    if (conversation) {
      setCurrentConversationId(conversationId);
      setMessages(conversation.messages);
      setUploadedFiles([]);
    }
  };
  
  const deleteConversation = (conversationId) => {
    const updatedConversations = conversations.filter(c => c.id !== conversationId);
    setConversations(updatedConversations);
    localStorage.setItem('conversations', JSON.stringify(updatedConversations));
    
    // If deleting current conversation, switch to another or create new
    if (conversationId === currentConversationId) {
      if (updatedConversations.length > 0) {
        switchConversation(updatedConversations[0].id);
      } else {
        createNewConversation();
      }
    }
  };
  
  const updateConversationTitle = (conversationId, firstMessage) => {
    const updatedConversations = conversations.map(conv => {
      if (conv.id === conversationId && conv.title === 'New Chat') {
        return {
          ...conv,
          title: firstMessage.substring(0, 30) + (firstMessage.length > 30 ? '...' : ''),
          updatedAt: new Date().toISOString()
        };
      }
      return conv;
    });
    setConversations(updatedConversations);
    localStorage.setItem('conversations', JSON.stringify(updatedConversations));
  };
  
  const saveCurrentConversation = (newMessages) => {
    const updatedConversations = conversations.map(conv => {
      if (conv.id === currentConversationId) {
        return {
          ...conv,
          messages: newMessages,
          updatedAt: new Date().toISOString()
        };
      }
      return conv;
    });
    
    // Sort by updatedAt (most recent first)
    updatedConversations.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
    
    setConversations(updatedConversations);
    localStorage.setItem('conversations', JSON.stringify(updatedConversations));
  };
  
  const resetConversation = () => {
    setMessages([]);
    setUploadedFiles([]);
    setChatMode('normal');
    saveCurrentConversation([]);
  };
  
  const handleLogin = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  };
  
  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('authToken');
    localStorage.removeItem('conversations');
    setUser(null);
    setIsAuthenticated(false);
    setMessages([]);
    setConversations([]);
    setCurrentConversationId(null);
    setUploadedFiles([]);
    setBackendUrl(null);
    setFrontendUrl(null);
    setDeploymentId(null);
  };
  
  const handleStopServices = async () => {
    if (!deploymentId && !backendUrl) {
      alert('No active deployment to stop');
      return;
    }
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/stop-deployment`, {
        deployment_id: deploymentId || null
      });
      
      if (response.data.status === 'success') {
        setBackendUrl(null);
        setFrontendUrl(null);
        setDeploymentId(null);
        alert('Services stopped successfully');
      } else {
        alert(`Error stopping services: ${response.data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error stopping services:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      alert(`Error stopping services: ${errorMessage}`);
    }
  };
  
  const renderMessage = (message, index) => {
    const isUser = message.role === 'user';
    const isSystem = message.role === 'system';
    const isAssistant = message.role === 'assistant';
    
    let icon = isUser ? '🧑‍💻' : isSystem ? '🔎' : '🤖';
    
    return (
      <div key={index} className={`message ${message.role}`}>
        <div className="message-header">
          <span>{icon}</span>
          <span>{message.role.charAt(0).toUpperCase() + message.role.slice(1)}</span>
        </div>
        <div className="message-content">
          {renderMessageContent(message.content)}
          {message.documents && message.documents.length > 0 && (
            <div className="document-badges">
              {message.documents.map((doc, i) => (
                <span key={i} className="document-badge">
                  <FileText size={14} /> {doc}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };
  
  const renderMessageContent = (content) => {
    // Simple markdown-like rendering
    const parts = content.split('```');
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        // Code block
        const lines = part.split('\n');
        const language = lines[0].trim();
        const code = lines.slice(1).join('\n');
        return <pre key={index}><code>{code}</code></pre>;
      } else {
        // Regular text with basic formatting
        return (
          <div key={index} dangerouslySetInnerHTML={{
            __html: part
              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
              .replace(/\*(.*?)\*/g, '<em>$1</em>')
              .replace(/`(.*?)`/g, '<code>$1</code>')
              .replace(/^## (.*$)/gim, '<h2>$1</h2>')
              .replace(/^### (.*$)/gim, '<h3>$1</h3>')
              .replace(/^- (.*$)/gim, '<li>$1</li>')
              .replace(/\n/g, '<br>')
          }} />
        );
      }
    });
  };
  
  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }
  
  return (
    <div className="app">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="user-profile">
          <div className="user-avatar">
            {user?.username ? user.username.charAt(0).toUpperCase() : 'U'}
          </div>
          <div className="user-info">
            <div className="user-name">{user?.username || 'User'}</div>
            <div className="user-email">{user?.email || 'user@example.com'}</div>
          </div>
        </div>
        
        {/* Recent Chats Section */}
        <div className="recent-chats-section">
          <div className="recent-chats-header">
            <h3>💬 Recent Chats</h3>
            <button className="new-chat-btn" onClick={createNewConversation} title="New Chat">
              +
            </button>
          </div>
          <div className="conversations-list">
            {conversations.map(conv => (
              <div
                key={conv.id}
                className={`conversation-item ${conv.id === currentConversationId ? 'active' : ''}`}
                onClick={() => switchConversation(conv.id)}
              >
                <div className="conversation-info">
                  <div className="conversation-title">{conv.title}</div>
                  <div className="conversation-date">
                    {new Date(conv.updatedAt).toLocaleDateString()}
                  </div>
                </div>
                <button
                  className="delete-conversation-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                  }}
                  title="Delete"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
        
        {/* Admin-only sections */}
        {user?.role === 'admin' && (
          <>
            <div className="sidebar-section">
              <h3>⚡ System Status</h3>
              <div className={`status-badge ${apiStatus.status === 'success' ? 'success' : apiStatus.status === 'error' ? 'error' : 'checking'}`}>
                {apiStatus.status === 'success' ? <CheckCircle size={16} /> : 
                 apiStatus.status === 'error' ? <XCircle size={16} /> : 
                 <AlertCircle size={16} />}
                {apiStatus.message}
              </div>
              <div className={`status-badge ${vertexAIStatus.status === 'success' ? 'success' : vertexAIStatus.status === 'error' ? 'error' : 'checking'}`} style={{ marginTop: '8px' }}>
                {vertexAIStatus.status === 'success' ? <CheckCircle size={16} /> : 
                 vertexAIStatus.status === 'error' ? <XCircle size={16} /> : 
                 <AlertCircle size={16} />}
                {vertexAIStatus.message}
              </div>
            </div>
            
            <div className="sidebar-section">
              <h3>⚙️ Interface Settings</h3>
              <div className="settings-container">
                <div className="setting-item">
                  <input 
                    type="checkbox" 
                    id="showAnalysis" 
                    checked={showAnalysis}
                    onChange={(e) => setShowAnalysis(e.target.checked)}
                  />
                  <label htmlFor="showAnalysis">Show requirements analysis</label>
                </div>
                <div className="setting-item">
                  <input 
                    type="checkbox" 
                    id="autoCode" 
                    checked={autoGenerateCode}
                    onChange={(e) => setAutoGenerateCode(e.target.checked)}
                  />
                  <label htmlFor="autoCode">Auto-generate code</label>
                </div>
                <div className="setting-item">
                  <input 
                    type="checkbox" 
                    id="deploy" 
                    checked={deployServices}
                    onChange={(e) => setDeployServices(e.target.checked)}
                  />
                  <label htmlFor="deploy">Deploy generated projects</label>
                </div>
              </div>
            </div>
            
            {backendUrl && frontendUrl && (
              <div className="sidebar-section">
                <h3>🚀 Deployed Services</h3>
                <div className="deployment-info">
                  <p style={{ fontWeight: 600, marginBottom: '12px' }}>✨ Your application is running!</p>
                  <p><a href={backendUrl} target="_blank" rel="noopener noreferrer">🔗 Backend API</a></p>
                  <p><a href={frontendUrl} target="_blank" rel="noopener noreferrer">🌐 Frontend UI</a></p>
                  <button 
                    className="btn btn-danger" 
                    style={{ marginTop: '12px', width: '100%' }}
                    onClick={handleStopServices}
                  >
                    <StopCircle size={16} /> Stop Services
                  </button>
                </div>
              </div>
            )}
            
            <div className="sidebar-section">
              <h3>☁️ GCP / Vertex AI Status</h3>
              <div className={`status-badge ${gcpStatus.gcp?.configured ? 'success' : 'error'}`}>
                {gcpStatus.gcp?.configured ? <CheckCircle size={16} /> : <XCircle size={16} />}
                {gcpStatus.gcp?.configured 
                  ? `GCP credentials configured (Project: ${gcpStatus.gcp?.project || 'N/A'})`
                  : `GCP credentials: ${gcpStatus.gcp?.error || 'Not configured'}`
                }
              </div>
              <div className={`status-badge ${gcpStatus.langchain_vertex_ai?.available ? 'success' : 'error'}`} style={{ marginTop: '8px' }}>
                {gcpStatus.langchain_vertex_ai?.available ? <CheckCircle size={16} /> : <XCircle size={16} />}
                {gcpStatus.langchain_vertex_ai?.available 
                  ? 'LangChain + Vertex AI is active'
                  : `LangChain + Vertex AI: ${gcpStatus.langchain_vertex_ai?.error || 'Not available'}`
                }
              </div>
            </div>
          </>
        )}
        
        <div className="sidebar-section" style={{ marginTop: 'auto' }}>
          <h3>🎯 Chat Mode</h3>
          <div className="mode-selector">
            <button 
              className={`mode-btn ${chatMode === 'normal' ? 'active' : ''}`}
              onClick={handleChatWithAI}
              title="Personal AI Agent Chat"
            >
              💬 Normal Chat
            </button>
            <button 
              className={`mode-btn ${chatMode === 'code' ? 'active' : ''}`}
              onClick={handleGenerateCode}
              title="Code Generation Assistant"
            >
              ⚡ Code Gen
            </button>
            <button 
              className={`mode-btn ${chatMode === 'deploy' ? 'active' : ''}`}
              onClick={handleDeployChatbots}
              title="Deploy Chatbots"
            >
              🚀 Deploy
            </button>
          </div>
        </div>
        
        <div style={{ marginTop: 'auto' }}>
          <button className="btn btn-secondary" style={{ width: '100%', marginBottom: '10px' }} onClick={resetConversation}>
            <RefreshCw size={16} /> Reset Conversation
          </button>
          <button className="btn btn-danger" style={{ width: '100%' }} onClick={handleLogout}>
            <LogOut size={16} /> Logout
          </button>
        </div>
      </div>
      
      {/* Main Chat Area */}
      <div className="main-content">
        <div className="chat-header">
          <div className="chat-header-content">
            <div className="model-name">Gemini 2.5 Flash</div>
            <div className="chat-mode-indicator">
              {chatMode === 'normal' && <span className="mode-badge normal">💬 Personal AI</span>}
              {chatMode === 'code' && <span className="mode-badge code">⚡ Code Gen</span>}
              {chatMode === 'deploy' && <span className="mode-badge deploy">🚀 Deploy</span>}
            </div>
          </div>
        </div>
        
        <div className="chat-messages">
          {messages.length === 0 && !processingStatus && (
            <div className="empty-chat-state">
              <div className="empty-chat-icon">🤖</div>
              <h2>Welcome</h2>
              <p>Start a conversation by typing a message below, or upload documents to provide context.</p>
              <div className="empty-chat-features">
                <div className="feature-item" onClick={handleChatWithAI}>
                  <span className="feature-icon">💬</span>
                  <span>Chat with AI agents</span>
                </div>
                <div className="feature-item" onClick={handleUploadDocuments}>
                  <span className="feature-icon">📎</span>
                  <span>Upload documents</span>
                </div>
                <div className="feature-item" onClick={handleGenerateCode}>
                  <span className="feature-icon">⚡</span>
                  <span>Generate code</span>
                </div>
                <div className="feature-item" onClick={handleDeployChatbots}>
                  <span className="feature-icon">🚀</span>
                  <span>Deploy chatbots</span>
                </div>
              </div>
            </div>
          )}
          
          {processingStatus && (
            <div className="status-message processing">
              {processingStatus.steps.map((step, index) => (
                <div key={index} className="status-step">
                  {index <= processingStatus.currentStep && <div className="spinner" />}
                  <span>{step}</span>
                </div>
              ))}
            </div>
          )}
          
          {messages.map((message, index) => renderMessage(message, index))}
          <div ref={messagesEndRef} />
        </div>
        
        {/* Compact File Upload Section */}
        {uploadedFiles.length > 0 && (
          <div className="uploaded-files-compact">
            <div className="uploaded-files-header-compact">
              <span>📎 {uploadedFiles.length} file{uploadedFiles.length > 1 ? 's' : ''} attached</span>
              <button 
                className="toggle-upload-btn"
                onClick={() => setShowFileUpload(!showFileUpload)}
              >
                {showFileUpload ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
            </div>
            {showFileUpload && (
              <div className="uploaded-files-list">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="uploaded-file-compact">
                    <div className="file-info-compact">
                      <FileText size={16} />
                      <span className="file-name-compact">{file.name}</span>
                      <span className="file-size-compact">{formatBytes(file.size)}</span>
                    </div>
                    <button className="remove-file-btn-compact" onClick={() => removeFile(index)} title="Remove">
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Chat Input */}
        <div className="chat-input-section">
          <div className="chat-input-wrapper">
            <button 
              className="file-upload-btn-compact"
              onClick={() => fileInputRef.current?.click()}
              title="Upload files"
            >
              <Upload size={20} />
            </button>
            <div className="chat-input-container">
              <textarea
                className="chat-input"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  chatMode === 'normal' ? 'Chat with your AI agent...' :
                  chatMode === 'code' ? 'Describe the code you want to generate...' :
                  chatMode === 'deploy' ? 'Describe the chatbot you want to create...' :
                  'Type your message here...'
                }
                disabled={isProcessing}
              />
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.txt,.xlsx,.xls"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
              <button 
                className="send-btn" 
                onClick={sendMessage}
                disabled={isProcessing || (!inputValue.trim() && uploadedFiles.length === 0)}
              >
                <Send size={20} />
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

