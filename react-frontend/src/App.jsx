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
  User as UserIcon
} from 'lucide-react';
import LoginPage from './LoginPage';
import './App.css';

const API_BASE_URL = 'http://localhost:5000';

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
  
  // Settings
  const [showAnalysis, setShowAnalysis] = useState(true);
  const [autoGenerateCode, setAutoGenerateCode] = useState(true);
  const [deployServices, setDeployServices] = useState(true);
  
  // API Status
  const [apiStatus, setApiStatus] = useState({ status: 'checking', message: 'Checking...' });
  const [vertexAIStatus, setVertexAIStatus] = useState({ status: 'checking', message: 'Checking...' });
  
  // Deployment
  const [backendUrl, setBackendUrl] = useState(null);
  const [frontendUrl, setFrontendUrl] = useState(null);
  
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
    }
  }, [isAuthenticated]);
  
  const checkAPIHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`, { timeout: 5000 });
      if (response.status === 200) {
        setApiStatus({ status: 'success', message: 'Flask API is running' });
        setVertexAIStatus({ status: 'success', message: 'Vertex AI is active' });
      }
    } catch (error) {
      setApiStatus({ status: 'error', message: 'Flask API not responding' });
      setVertexAIStatus({ status: 'error', message: 'Cannot connect to Vertex AI' });
    }
  };
  
  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    
    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (event) => {
        const fileData = {
          name: file.name,
          type: file.type,
          size: file.size,
          content: event.target.result,
          preview: event.target.result.substring(0, 500) + '...'
        };
        
        setUploadedFiles(prev => [...prev, fileData]);
      };
      reader.readAsText(file);
    });
  };
  
  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
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
    
    // Check if this is a code generation request
    const codeKeywords = ['generate code', 'create code', 'write code', 'code for', 'generate a program',
                          'build an application', 'develop a system', 'create an app', 'write a program',
                          'create a chatbot', 'build a chatbot', 'chatbot', 'bot'];
    const isCodeRequest = codeKeywords.some(keyword => messageContent.toLowerCase().includes(keyword));
    
    try {
      if (isCodeRequest && autoGenerateCode) {
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
        // Regular requirements analysis
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
            <UserIcon size={24} />
          </div>
          <div className="user-info">
            <div className="user-name">{user?.username || 'User'}</div>
            <div className="user-email">{user?.email || 'user@example.com'}</div>
          </div>
        </div>
        
        <h2>🤖 Mother of Bots</h2>
        <p style={{ fontSize: '0.9rem', color: '#666' }}>
          Multi-Agent Chat Interface
        </p>
        <div className="user-role-badge">
          <span className={`role-tag ${user?.role}`}>
            {user?.role === 'admin' ? '👑 Administrator' : '👤 User'}
          </span>
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
            <div>
              <h3>Flask API Status</h3>
              <div className={`status-badge ${apiStatus.status}`}>
                {apiStatus.status === 'success' ? <CheckCircle size={16} /> : 
                 apiStatus.status === 'error' ? <XCircle size={16} /> : 
                 <AlertCircle size={16} />}
                {apiStatus.message}
              </div>
            </div>
            
            <div>
              <h3>Vertex AI Status</h3>
              <div className={`status-badge ${vertexAIStatus.status}`}>
                {vertexAIStatus.status === 'success' ? <CheckCircle size={16} /> : 
                 vertexAIStatus.status === 'error' ? <XCircle size={16} /> : 
                 <AlertCircle size={16} />}
                {vertexAIStatus.message}
              </div>
            </div>
            
            <div>
              <h3>Interface Settings</h3>
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
            
            {backendUrl && frontendUrl && (
              <div>
                <h3>Deployed Services</h3>
                <div className="deployment-info">
                  <p>Your application is running!</p>
                  <p><a href={backendUrl} target="_blank" rel="noopener noreferrer">Backend API</a></p>
                  <p><a href={frontendUrl} target="_blank" rel="noopener noreferrer">Frontend UI</a></p>
                  <button className="btn btn-danger" style={{ marginTop: '10px', width: '100%' }}>
                    <StopCircle size={16} /> Stop Services
                  </button>
                </div>
              </div>
            )}
          </>
        )}
        
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
          <h1>Mother of Bots Chat</h1>
          <p>Using gemini-2.5-flash via Vertex AI 🦜️</p>
        </div>
        
        <div className="chat-messages">
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
        
        {/* File Upload Section */}
        <div className="file-upload-section">
          <div className="file-upload-header">
            <Upload size={20} />
            Upload Documents
          </div>
          <div 
            className="file-upload-area" 
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.doc,.txt,.xlsx,.xls"
              onChange={handleFileUpload}
            />
            <FileText size={32} style={{ margin: '0 auto 10px', color: '#667eea' }} />
            <p>Drag and drop files here or click to browse</p>
            <p style={{ fontSize: '0.85rem', color: '#666' }}>Supported: PDF, DOCX, TXT, XLSX</p>
          </div>
          
          {uploadedFiles.length > 0 && (
            <div className="uploaded-files">
              {uploadedFiles.map((file, index) => (
                <div key={index} className="uploaded-file">
                  <div className="file-info">
                    <FileText size={20} />
                    <div>
                      <div className="file-name">{file.name}</div>
                      <div className="file-size">{formatBytes(file.size)}</div>
                    </div>
                  </div>
                  <button className="remove-file-btn" onClick={() => removeFile(index)}>
                    <X size={20} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Chat Input */}
        <div className="chat-input-section">
          <div className="chat-input-container">
            <textarea
              className="chat-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              disabled={isProcessing}
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
  );
}

export default App;

