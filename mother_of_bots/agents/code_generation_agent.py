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

# Removed SPADE CodeGenerationAgent - using FastAPI instead

# Standalone Code Generation Agent (no SPADE dependency)
class StandaloneCodeGenerationAgent:
    """Code Generation Agent using LangChain (no SPADE dependency)"""
    
    def __init__(self, name="StandaloneCodeGenerationAgent"):
        self.name = name
        self.running = False
        logger.info(f"Standalone {self.name} initialized")
    
    async def generate_code(self, requirements):
        """Generate code based on requirements dict or string using LangChain"""
        
        # Convert string requirements to dict if needed
        if isinstance(requirements, str):
            specs = {
                "description": requirements,
                "type": "direct_request"
            }
        else:
            specs = requirements
        
        # Try up to 3 times with different temperature settings if needed
        for attempt, temp in enumerate([(0.1, 9000 ), (0.2, 10000), (0.05, 11000)]):
            temperature, num_predict = temp
            
            # Log the attempt
            logger.info(f"Code generation attempt {attempt+1}/3 with temperature={temperature}")
        
            # Create code generation prompt
            prompt = self._create_code_generation_prompt(specs)
            
            try:
                # Use LangChain Vertex AI with Gemini
                logger.info(f"[LangChain] Initializing Gemini via Vertex AI (model: {GEMINI_MODEL}, project: {GCP_PROJECT_ID})")
                llm = ChatVertexAI(
                    model=GEMINI_MODEL,
                    project=GCP_PROJECT_ID,
                    location=GCP_LOCATION,
                    temperature=temperature,
                    max_output_tokens=num_predict
                )
                
                # Invoke asynchronously using LangChain
                logger.info(f"[LangChain] Invoking code generation via Vertex AI ainvoke()")
                response = await llm.ainvoke(prompt)
                generated_code = response.content if hasattr(response, 'content') else str(response)
                logger.info(f"[LangChain] Code generation completed via Vertex AI ({len(generated_code)} chars)")
                generated_code = generated_code.strip()
                
                # Check if we got a reasonable amount of code
                formatted_code = self._format_generated_code(generated_code)
                
                if len(formatted_code) > 100 and "import" in formatted_code and "def" in formatted_code:
                    logger.info(f"Code generation successful on attempt {attempt+1}")
                    return formatted_code
                else:
                    logger.warning(f"Generated code seems incomplete on attempt {attempt+1}, will retry")
                    
                    # If this is the last attempt, return what we have
                    if attempt == 2:
                        return formatted_code
            except Exception as e:
                logger.error(f"Exception during code generation attempt {attempt+1}: {str(e)}")
                if attempt == 2:
                    return f"Failed to generate code: {str(e)}"
        
        return "Failed to generate code after multiple attempts"
    
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
    
    def _create_code_generation_prompt(self, specs: Dict[str, Any]) -> str:
        """Create a detailed prompt for code generation based on specs"""
        
        # Detect if this is a chatbot request
        if self._is_chatbot_request(specs):
            return self._create_chatbot_backend_prompt(specs)
        
        # Convert specs to a formatted string for the prompt
        if "description" in specs and specs.get("type") == "direct_request":
            # Direct text request
            specs_text = f"User requirements: {specs['description']}"
        else:
            # Structured JSON requirements
            specs_text = json.dumps(specs, indent=2)
        
        return f"""You are an expert Python backend engineer with 15+ years of experience building production-grade REST APIs.
Your task is to generate a COMPLETE, FULLY FUNCTIONAL backend application in Python.

## PROJECT REQUIREMENTS
{specs_text}

## MANDATORY TECHNICAL REQUIREMENTS

### 1. Framework & Structure
- Use FastAPI as the web framework
- Create a single-file application (app.py) that is ready to run
- Include ALL imports at the top of the file
- Use async/await patterns throughout

### 2. CORS Configuration (CRITICAL)
You MUST include CORS middleware to allow frontend connections:
```
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Database Setup
- Use SQLAlchemy with SQLite for simplicity (async support via aiosqlite)
- Define ALL database models with proper relationships
- Include database initialization that creates tables on startup
- Use dependency injection for database sessions:
```
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### 4. Complete CRUD Operations
For EVERY entity/resource in the requirements, implement ALL of these endpoints:
- GET /{{resources}} - List all (with optional pagination)
- GET /{{resources}}/{{id}} - Get single by ID
- POST /{{resources}} - Create new
- PUT /{{resources}}/{{id}} - Update existing
- DELETE /{{resources}}/{{id}} - Delete by ID

### 5. Pydantic Models
Create request/response schemas for ALL endpoints:
- Base schema (shared fields)
- Create schema (for POST requests)
- Update schema (for PUT requests, all fields optional)
- Response schema (includes id and timestamps)

### 6. HTTP Status Codes & Error Handling
Use these EXACT status constants from FastAPI:
- status.HTTP_200_OK for successful GET/PUT
- status.HTTP_201_CREATED for successful POST  
- status.HTTP_204_NO_CONTENT for successful DELETE
- status.HTTP_404_NOT_FOUND when resource doesn't exist
- status.HTTP_422_UNPROCESSABLE_ENTITY for invalid input
- status.HTTP_500_INTERNAL_SERVER_ERROR for server errors

Example error handling:
```python
from fastapi import status, HTTPException

@app.get("/items/{{item_id}}")
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item
```

### 7. API Documentation
- Add descriptive docstrings to all endpoints
- Use FastAPI's built-in OpenAPI/Swagger support
- Include response_model in route decorators

### 8. Startup Event
Include proper startup to initialize database:
```
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

## OUTPUT FORMAT
- Output ONLY Python code, no markdown formatting or explanations
- The code must be complete and runnable with: uvicorn app:app --reload
- Include a health check endpoint: GET /health
- Include a root endpoint: GET / that returns API info

## EXAMPLE STRUCTURE
```
# Imports
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./app.db"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Base model
class Base(DeclarativeBase):
    pass

# SQLAlchemy Models here...
# Pydantic Schemas here...
# FastAPI app with CORS...
# Dependency injection...
# All CRUD endpoints...
# Startup event...
```

Now generate the complete backend code:"""
    
    def _create_chatbot_backend_prompt(self, specs: Dict[str, Any]) -> str:
        """Create a prompt specifically for chatbot backend generation"""
        
        specs_text = json.dumps(specs, indent=2)
        
        # Extract chatbot-specific settings
        personality = specs.get("personality", {})
        tone = personality.get("tone", "neutral")
        traits = personality.get("traits", [])
        response_rules = specs.get("response_rules", {})
        max_sentences = response_rules.get("max_sentences", 2)
        style = response_rules.get("style", "concise")
        memory = specs.get("memory", {})
        memory_type = memory.get("type", "none")
        
        return f"""You are an expert Python backend engineer specializing in building chatbot APIs.
Your task is to generate a COMPLETE, FULLY FUNCTIONAL chatbot backend in Python.

## CHATBOT SPECIFICATIONS
{specs_text}

## MANDATORY REQUIREMENTS

### 1. Framework & Structure
- Use FastAPI as the web framework
- Create a single-file application (app.py) that is ready to run
- Include ALL imports at the top of the file

### 2. CORS Configuration (CRITICAL)
You MUST include CORS middleware:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Chatbot Configuration
Create a ChatbotConfig class to store the bot's behavior settings:
```python
class ChatbotConfig:
    TONE = "{tone}"
    TRAITS = {traits}
    MAX_SENTENCES = {max_sentences}
    RESPONSE_STYLE = "{style}"
    MEMORY_TYPE = "{memory_type}"  # "none", "short_term", or "long_term"
```

### 4. Core Chatbot Endpoint
Implement the main chat endpoint:
```python
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Generate response based on chatbot config
    pass
```

### 5. Response Generation Logic
The chatbot MUST:
- Keep responses to maximum {max_sentences} sentences
- Use a {tone} tone
- Be {style} in its responses
- {"NOT maintain any conversation history (stateless)" if memory_type == "none" else "Maintain conversation context within the session"}

### 6. Simple Response Generator
Create a simple rule-based or template response generator:
```python
def generate_response(user_message: str, config: ChatbotConfig) -> str:
    # Simple response logic
    # Ensure response is within max_sentences limit
    # Apply tone and style constraints
    pass
```

### 7. Additional Endpoints
- GET / - API info
- GET /health - Health check
- GET /config - Return current chatbot configuration
- POST /chat - Main chat endpoint

### 8. Session Management (if memory != "none")
{"Skip this section - no session management needed for stateless bot" if memory_type == "none" else '''
- Generate unique session IDs
- Store conversation history per session
- Clean up old sessions periodically
'''}

## OUTPUT FORMAT
- Output ONLY Python code, no markdown formatting or explanations
- The code must be complete and runnable with: uvicorn app:app --reload
- Include sample responses that match the chatbot's personality

## EXAMPLE MINIMAL CHATBOT STRUCTURE
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

# Chatbot configuration
class ChatbotConfig:
    TONE = "{tone}"
    MAX_SENTENCES = {max_sentences}
    
# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

# FastAPI app
app = FastAPI(title="Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_response(message: str) -> str:
    # Simple response logic here
    # Keep response short and in the configured tone
    pass

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    response_text = generate_response(request.message)
    return ChatResponse(response=response_text, session_id=session_id)

@app.get("/")
async def root():
    return {{"message": "Chatbot API", "version": "1.0.0"}}

@app.get("/health")
async def health():
    return {{"status": "ok"}}
```

Now generate the complete chatbot backend code:"""

    
    def _format_generated_code(self, code: str) -> str:
        """Format the generated code, extracting only the Python code if necessary"""
        
        # Remove any leading/trailing whitespace
        code = code.strip()
        
        # List of markdown code block markers to check (in order of specificity)
        code_markers = ["```python", "```py", "```"]
        
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
        if lines and lines[0].strip().lower() in ['python', 'py', 'javascript', 'jsx', 'js']:
            code = '\n'.join(lines[1:]).strip()
        
        # Remove any remaining ``` at the start or end
        if code.startswith("```"):
            code = code[3:].strip()
            # Remove language identifier if present
            if code.split('\n')[0].strip().lower() in ['python', 'py', 'javascript', 'jsx', 'js', '']:
                code = '\n'.join(code.split('\n')[1:]).strip()
        
        if code.endswith("```"):
            code = code[:-3].strip()
        
        return code
    
    def _validate_code_completeness(self, code: str, is_chatbot: bool = False) -> bool:
        """Validate that generated code appears complete"""
        
        # Basic checks
        if len(code) < 100:
            return False
        
        if "import" not in code:
            return False
        
        if is_chatbot:
            # Chatbot-specific checks
            required_elements = ["FastAPI", "/chat", "ChatRequest", "ChatResponse"]
            return sum(1 for elem in required_elements if elem in code) >= 3
        else:
            # CRUD app checks
            required_elements = ["FastAPI", "def ", "async def", "@app"]
            return sum(1 for elem in required_elements if elem in code) >= 3
    
    async def start(self):
        """Start the agent"""
        logger.info(f"Starting agent {self.name}")
        logger.info(f"Using Gemini model: {GEMINI_MODEL} via Vertex AI (project: {GCP_PROJECT_ID})")
        
        self.running = True
        logger.info(f"Agent {self.name} started successfully")
        return True
        
    async def stop(self):
        """Stop the agent"""
        logger.info(f"Stopping agent {self.name}")
        self.running = False
        logger.info(f"Agent {self.name} stopped")
        
    def is_alive(self):
        """Check if the agent is running"""
        return self.running 