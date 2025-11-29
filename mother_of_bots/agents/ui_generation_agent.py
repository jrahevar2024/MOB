import logging
import os
import json
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get Vertex AI / Gemini settings from environment variables
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "motherofbots")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Removed SPADE UIGenerationAgent - using FastAPI instead

class StandaloneUIGenerationAgent:
    """A standalone version of UI generation agent that doesn't require SPADE/XMPP"""
    
    def __init__(self, name="StandaloneUIGenerationAgent"):
        self.name = name
        self.running = False
        logger.info(f"StandaloneUIGenerationAgent initialized: {name}")
    
    async def generate_ui_code(self, requirements):
        """Generate UI code based on the requirements provided"""
        logger.info(f"StandaloneUIGenerationAgent generating UI code")
        
        # Format requirements if needed
        if isinstance(requirements, str):
            requirements = {
                "description": requirements,
                "type": "direct_request"
            }
        
        # Create prompt for UI generation
        prompt = self._create_ui_generation_prompt(requirements)
        
        # Try up to 3 times with different temperature settings if needed
        for attempt, temp in enumerate([(0.1, 9000 ), (0.2, 10000), (0.05, 11000)]):
            temperature, num_predict = temp
            
            logger.info(f"UI code generation attempt {attempt+1}/3 with temperature={temperature}")
            
            try:
                # Use LangChain Vertex AI with Gemini
                llm = ChatVertexAI(
                    model=GEMINI_MODEL,
                    project=GCP_PROJECT_ID,
                    location=GCP_LOCATION,
                    temperature=temperature,
                    max_output_tokens=num_predict
                )
                
                # Invoke asynchronously using LangChain
                response = await llm.ainvoke(prompt)
                generated_code = response.content if hasattr(response, 'content') else str(response)
                generated_code = generated_code.strip()
                
                # Format the generated code
                formatted_code = self._format_generated_code(generated_code)
                
                if len(formatted_code) > 100 and "import" in formatted_code and ("function" in formatted_code or "const" in formatted_code):
                    logger.info(f"UI code generation successful on attempt {attempt+1}")
                    return formatted_code
                else:
                    logger.warning(f"Generated UI code seems incomplete on attempt {attempt+1}")
                    
                    # If this is the last attempt, return what we have
                    if attempt == 2:
                        return formatted_code
            except Exception as e:
                logger.error(f"Exception during UI code generation attempt {attempt+1}: {str(e)}")
                if attempt == 2:
                    return f"Failed to generate UI code: {str(e)}"
        
        return "Failed to generate UI code after multiple attempts"
    
    def _is_chatbot_request(self, specs: Dict[str, Any]) -> bool:
        """Detect if the requirements are for a chatbot application"""
        # Check if app_type is explicitly set to chatbot
        if specs.get("app_type") == "chatbot":
            return True
        
        # Check for chatbot-specific fields
        chatbot_fields = ["personality", "response_rules", "memory", "tone", "traits"]
        if any(field in specs for field in chatbot_fields):
            return True
        
        # Check description for chatbot keywords
        description = str(specs.get("description", "")).lower()
        chatbot_keywords = ["chatbot", "chat bot", "conversational", "bot", "assistant", "dialogue"]
        if any(keyword in description for keyword in chatbot_keywords):
            return True
        
        return False
    
    def _create_ui_generation_prompt(self, specs: Dict[str, Any]) -> str:
        """Create a detailed prompt for UI code generation based on specs"""
        
        # Detect if this is a chatbot request
        if self._is_chatbot_request(specs):
            return self._create_chatbot_ui_prompt(specs)
        
        # Convert specs to a formatted string for the prompt
        if "description" in specs and specs.get("type") == "direct_request":
            # Direct text request
            specs_text = f"User requirements: {specs['description']}"
        else:
            # Structured JSON requirements
            specs_text = json.dumps(specs, indent=2)
        
        return f"""You are a senior frontend engineer with 10+ years of experience building production React applications.
Your task is to generate a COMPLETE, FULLY FUNCTIONAL React frontend that connects to a backend API.

## PROJECT REQUIREMENTS
{specs_text}

## MANDATORY TECHNICAL REQUIREMENTS

### 1. API Configuration (CRITICAL)
The backend API runs at http://localhost:8001. You MUST:
- Define API_BASE_URL at the top of the file
- Use this base URL for ALL API calls
- Include proper error handling for network failures

```javascript
const API_BASE_URL = 'http://localhost:8001';
```

### 2. Complete API Integration
For EVERY feature in the requirements, implement FULL CRUD operations:
- Fetch and display lists of items (GET /resources)
- View individual item details (GET /resources/{{id}})
- Create new items with forms (POST /resources)
- Edit existing items (PUT /resources/{{id}})
- Delete items with confirmation (DELETE /resources/{{id}})

### 3. API Call Pattern (MUST FOLLOW)
Every API call MUST include:
- Loading state while request is in progress
- Error handling with user-friendly messages
- Success feedback to the user

```javascript
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);

const fetchData = async () => {{
  setLoading(true);
  setError(null);
  try {{
    const response = await fetch(`${{API_BASE_URL}}/endpoint`);
    if (!response.ok) {{
      throw new Error(response.status === 404 ? 'Not found' : 'Server error');
    }}
    const data = await response.json();
    // Update state with data
  }} catch (err) {{
    setError(err.message || 'Failed to fetch data');
  }} finally {{
    setLoading(false);
  }}
}};
```

### 4. State Management
- Use React hooks (useState, useEffect, useCallback)
- Implement proper loading states for ALL async operations
- Store fetched data in component state
- Update UI immediately after successful mutations (optimistic updates optional)

### 5. Form Handling
For ALL forms, implement:
- Controlled inputs with useState
- Form validation before submission
- Disabled submit button while loading
- Clear error/success messages
- Reset form after successful submission

```javascript
const [formData, setFormData] = useState({{ name: '', email: '' }});
const [formErrors, setFormErrors] = useState({{}});

const handleSubmit = async (e) => {{
  e.preventDefault();
  if (!validateForm()) return;
  // Submit logic...
}};
```

### 6. UI Components (MUST INCLUDE)
- Loading spinner component for all async operations
- Error alert/banner component for displaying errors
- Success notification for completed actions
- Confirmation dialog for delete operations
- Empty state when no data exists

### 7. TailwindCSS Styling
- Use TailwindCSS utility classes for ALL styling
- Implement responsive design (mobile-first)
- Use consistent spacing and colors
- Include hover/focus states for interactive elements
- Add transitions for smooth UX

### 8. Component Structure
Create a single App component that includes:
- Header with app title
- Main content area with all features
- Proper layout using Flexbox/Grid
- All sub-components inline (single file)

## OUTPUT FORMAT REQUIREMENTS
- Output ONLY JSX/JavaScript code, NO markdown formatting
- Export a single App component as default
- Include ALL imports at the top (React hooks)
- The code must work directly in a browser with Babel
- Use standard JavaScript (not TypeScript)

## EXAMPLE STRUCTURE
```javascript
const API_BASE_URL = 'http://localhost:8001';

// Reusable Loading Spinner
const LoadingSpinner = () => (
  <div className="flex justify-center items-center p-4">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
  </div>
);

// Reusable Error Alert
const ErrorAlert = ({{ message, onDismiss }}) => (
  <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
    <span>{{message}}</span>
    {{onDismiss && <button onClick={{onDismiss}} className="absolute top-0 right-0 px-4 py-3">&times;</button>}}
  </div>
);

// Main App Component
function App() {{
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {{
    fetchItems();
  }}, []);

  const fetchItems = async () => {{
    setLoading(true);
    try {{
      const res = await fetch(`${{API_BASE_URL}}/items`);
      if (!res.ok) throw new Error('Failed to fetch');
      setItems(await res.json());
    }} catch (err) {{
      setError(err.message);
    }} finally {{
      setLoading(false);
    }}
  }};

  // ... more handlers and JSX
}}

export default App;
```

Now generate the complete React frontend code:"""
    
    def _create_chatbot_ui_prompt(self, specs: Dict[str, Any]) -> str:
        """Create a prompt specifically for chatbot UI generation"""
        
        specs_text = json.dumps(specs, indent=2)
        
        # Extract chatbot-specific settings for UI hints
        ui_requirements = specs.get("ui_requirements", {})
        ui_style = ui_requirements.get("style", "standard")
        
        return f"""You are a senior frontend engineer specializing in chat interfaces and conversational UIs.
Your task is to generate a COMPLETE, FULLY FUNCTIONAL chat interface in React.

## CHATBOT SPECIFICATIONS
{specs_text}

## MANDATORY REQUIREMENTS

### 1. API Configuration (CRITICAL)
The chatbot backend API runs at http://localhost:8001. You MUST:
```javascript
const API_BASE_URL = 'http://localhost:8001';
```

### 2. Chat Interface Components
Create these essential components:

#### ChatMessage Component
```javascript
const ChatMessage = ({{ message, isUser }}) => (
  <div className={{`flex ${{isUser ? 'justify-end' : 'justify-start'}} mb-4`}}>
    <div className={{`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${{
      isUser ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'
    }}`}}>
      {{message}}
    </div>
  </div>
);
```

#### ChatInput Component
```javascript
const ChatInput = ({{ onSend, disabled }}) => {{
  const [input, setInput] = useState('');
  
  const handleSubmit = (e) => {{
    e.preventDefault();
    if (input.trim() && !disabled) {{
      onSend(input.trim());
      setInput('');
    }}
  }};
  
  return (
    <form onSubmit={{handleSubmit}} className="flex gap-2">
      <input
        type="text"
        value={{input}}
        onChange={{(e) => setInput(e.target.value)}}
        placeholder="Type a message..."
        disabled={{disabled}}
        className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        type="submit"
        disabled={{disabled || !input.trim()}}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        Send
      </button>
    </form>
  );
}};
```

### 3. Main Chat Logic
The App component MUST:
- Maintain message history in state
- Send messages to POST /chat endpoint
- Display bot responses
- Show loading indicator while waiting for response
- Handle errors gracefully

```javascript
const [messages, setMessages] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);
const [sessionId, setSessionId] = useState(null);

const sendMessage = async (text) => {{
  // Add user message to state
  setMessages(prev => [...prev, {{ text, isUser: true }}]);
  setLoading(true);
  setError(null);
  
  try {{
    const response = await fetch(`${{API_BASE_URL}}/chat`, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ message: text, session_id: sessionId }})
    }});
    
    if (!response.ok) throw new Error('Failed to get response');
    
    const data = await response.json();
    setSessionId(data.session_id);
    setMessages(prev => [...prev, {{ text: data.response, isUser: false }}]);
  }} catch (err) {{
    setError('Failed to send message. Please try again.');
  }} finally {{
    setLoading(false);
  }}
}};
```

### 4. UI Layout
Create a clean chat interface with:
- Header with chatbot name/title
- Scrollable message area
- Fixed input area at bottom
- Auto-scroll to latest message

### 5. Styling with TailwindCSS
- Clean, modern chat bubble design
- Different colors for user vs bot messages
- Responsive layout
- Typing indicator when loading
- Smooth animations

### 6. Additional Features
- Welcome message on load
- Clear chat button
- Error display
- Loading/typing indicator

## OUTPUT FORMAT REQUIREMENTS
- Output ONLY JSX/JavaScript code, NO markdown formatting or code blocks
- Do NOT wrap code in ``` markers
- Export a single App component as default
- Include ALL imports at the top (React, useState, useEffect, useRef)
- The code must work directly in a browser with Babel
- Use standard JavaScript (not TypeScript)

## COMPLETE EXAMPLE STRUCTURE
const API_BASE_URL = 'http://localhost:8001';

const ChatMessage = ({{ message, isUser }}) => (
  // Message bubble component
);

const TypingIndicator = () => (
  // Animated dots indicator
);

function App() {{
  const [messages, setMessages] = useState([
    {{ text: 'Hello! How can I help you today?', isUser: false }}
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);
  
  // Auto-scroll effect
  useEffect(() => {{
    messagesEndRef.current?.scrollIntoView({{ behavior: 'smooth' }});
  }}, [messages]);
  
  const sendMessage = async (text) => {{
    // Send message logic
  }};
        
        return (
    <div className="flex flex-col h-screen bg-gray-100">
      {{/* Header */}}
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <h1 className="text-xl font-bold">Chatbot</h1>
      </header>
      
      {{/* Messages Area */}}
      <div className="flex-1 overflow-y-auto p-4">
        {{messages.map((msg, idx) => (
          <ChatMessage key={{idx}} message={{msg.text}} isUser={{msg.isUser}} />
        ))}}
        {{loading && <TypingIndicator />}}
        <div ref={{messagesEndRef}} />
      </div>
      
      {{/* Input Area */}}
      <div className="p-4 bg-white border-t">
        {{error && <div className="text-red-500 text-sm mb-2">{{error}}</div>}}
        <ChatInput onSend={{sendMessage}} disabled={{loading}} />
      </div>
    </div>
  );
}}

export default App;

Now generate the complete chatbot React UI code (NO markdown, just code):"""
    
    def _format_generated_code(self, code: str) -> str:
        """Format the generated code, extracting only the React code if necessary"""
        
        # Remove any leading/trailing whitespace
        code = code.strip()
        
        # List of markdown code block markers to check (in order of specificity)
        code_markers = ["```jsx", "```javascript", "```tsx", "```react", "```js", "```"]
        
        for marker in code_markers:
            if marker in code:
                # Find the first occurrence of the marker
                start_idx = code.find(marker)
                # Move past the marker and any newline
                start = start_idx + len(marker)
                if start < len(code) and code[start] == '\n':
                    start += 1
                
                # Find the closing ```
                end = code.rfind("```")
                
                # Make sure we found a valid closing marker after the start
                if end > start:
                    extracted = code[start:end].strip()
                    # Recursively check if there are more code blocks inside
                    if "```" in extracted:
                        return self._format_generated_code(extracted)
                    return extracted
        
        # Check if code starts with a language identifier on first line (without ```)
        lines = code.split('\n')
        if lines and lines[0].strip().lower() in ['javascript', 'jsx', 'js', 'tsx', 'react']:
            code = '\n'.join(lines[1:]).strip()
        
        # Remove any remaining ``` at the start or end
        if code.startswith("```"):
            code = code[3:].strip()
            # Remove language identifier if present
            first_line = code.split('\n')[0].strip().lower()
            if first_line in ['javascript', 'jsx', 'js', 'tsx', 'react', '']:
                code = '\n'.join(code.split('\n')[1:]).strip()
        
        if code.endswith("```"):
            code = code[:-3].strip()
        
        return code
    
    def _validate_ui_completeness(self, code: str, is_chatbot: bool = False) -> bool:
        """Validate that generated UI code appears complete"""
        
        # Basic checks
        if len(code) < 100:
            return False
        
        if is_chatbot:
            # Chatbot UI specific checks
            required_elements = ["API_BASE_URL", "useState", "message", "send", "App"]
            return sum(1 for elem in required_elements if elem in code) >= 4
        else:
            # General CRUD UI checks
            required_elements = ["API_BASE_URL", "useState", "fetch", "App"]
            return sum(1 for elem in required_elements if elem in code) >= 3
    
    async def start(self):
        """Start the agent"""
        logger.info(f"Starting StandaloneUIGenerationAgent: {self.name}")
        self.running = True
    
    async def stop(self):
        """Stop the agent"""
        logger.info(f"Stopping StandaloneUIGenerationAgent: {self.name}")
        self.running = False
    
    def is_alive(self):
        """Check if agent is running"""
        return self.running 