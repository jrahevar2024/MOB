import logging
import os
import json
import re
from typing import Dict, Any, Optional, Union, Tuple
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

# Keywords to detect chatbot-specific requirements
CHATBOT_KEYWORDS = [
    'chatbot', 'chat bot', 'conversational', 'conversation', 'chat interface',
    'assistant', 'bot', 'dialogue', 'dialog', 'chat application', 'messaging',
    'natural language', 'nlp', 'response generation', 'chat ui', 'chat window',
    'message', 'reply', 'conversational model', 'conversational ai'
]

def detect_application_type(message: str) -> str:
    """
    Detect whether the request is for a chatbot or a general CRUD application.
    
    Args:
        message: The user's requirement message
        
    Returns:
        'chatbot' or 'crud' based on detected type
    """
    message_lower = message.lower()
    
    # Check for chatbot-specific keywords
    chatbot_score = sum(1 for keyword in CHATBOT_KEYWORDS if keyword in message_lower)
    
    # Check for CRUD-specific keywords
    crud_keywords = ['crud', 'database', 'users', 'products', 'orders', 'inventory', 
                     'management system', 'admin panel', 'dashboard', 'e-commerce',
                     'booking', 'reservation', 'scheduling']
    crud_score = sum(1 for keyword in crud_keywords if keyword in message_lower)
    
    # If document mentions role, constraints, tone, response - likely chatbot spec
    chatbot_spec_patterns = [
        r'role\s*:', r'constraints\s*:', r'tone\s*:', r'response\s*length',
        r'memory\s*:', r'function\s*:', r'goal\s*:', r'personality',
        r'max\s+\w+\s+sentences', r'conversational\s+model'
    ]
    spec_matches = sum(1 for pattern in chatbot_spec_patterns if re.search(pattern, message_lower))
    chatbot_score += spec_matches * 2  # Weight spec patterns more heavily
    
    logger.info(f"Application type detection - Chatbot score: {chatbot_score}, CRUD score: {crud_score}")
    
    if chatbot_score > crud_score or chatbot_score >= 2:
        return 'chatbot'
    return 'crud'

def _create_chatbot_analysis_prompt(output_format: str) -> str:
    """Create analysis prompt specifically for chatbot applications"""
    
    base_prompt = """You are an expert at analyzing chatbot and conversational AI specifications.
The user is describing a CHATBOT or CONVERSATIONAL APPLICATION. Extract the requirements carefully.

## CHATBOT-SPECIFIC ANALYSIS CATEGORIES

### 1. Bot Identity & Purpose
- Name/identity of the chatbot
- Primary purpose and use case
- Target audience/users

### 2. Personality & Tone
- Communication style (formal, casual, friendly, etc.)
- Tone characteristics (helpful, humorous, serious, etc.)
- Any specific personality traits defined

### 3. Response Behavior (CRITICAL)
- Response length constraints (e.g., max sentences, word limits)
- Response speed/latency requirements
- Verbosity level (minimal, detailed, etc.)

### 4. Memory & Context
- Short-term memory (within conversation)
- Long-term memory requirements
- Context retention rules

### 5. Capabilities & Functions
- What the bot can/should do
- What the bot should NOT do
- Special commands or triggers

### 6. Constraints & Limitations
- Content restrictions
- Topic limitations
- Safety/moderation rules

### 7. Integration Requirements
- APIs to connect with
- Data sources
- External services

### 8. UI Requirements
- Chat interface style
- Input/output format
- Additional UI elements (buttons, quick replies, etc.)

"""
    
    if output_format == "json":
        base_prompt += """## OUTPUT FORMAT
Return a valid JSON object with this structure for CHATBOT applications:

{
  "app_type": "chatbot",
  "app_name": "Name of the chatbot",
  "description": "Brief description of the chatbot's purpose",
  "personality": {
    "tone": "neutral|friendly|formal|casual|humorous",
    "traits": ["trait1", "trait2"],
    "communication_style": "description of how the bot communicates"
  },
  "response_rules": {
    "max_sentences": 2,
    "max_words": null,
    "style": "concise|detailed|minimal",
    "avoid": ["things to avoid in responses"]
  },
  "memory": {
    "type": "none|short_term|long_term",
    "context_turns": 0,
    "persist_data": false
  },
  "capabilities": ["capability1", "capability2"],
  "restrictions": ["restriction1", "restriction2"],
  "ui_requirements": {
    "style": "minimal|standard|rich",
    "features": ["chat_window", "message_history", "typing_indicator"]
  },
  "api_endpoints": [
    {"method": "POST", "path": "/chat", "description": "Send message and get response"}
  ],
  "integrations": []
}

IMPORTANT:
- Set app_type to "chatbot"
- Extract exact constraints from the document (e.g., "max 2 sentences" -> max_sentences: 2)
- If memory is "zero" or "none", set memory.type to "none" and context_turns to 0
- Return ONLY valid JSON, no additional text"""
    else:
        base_prompt += """## OUTPUT FORMAT
Format your response as structured sections focusing on chatbot-specific requirements.
Be specific about response constraints, personality, and behavior rules.

### Bot Identity
- Name and purpose

### Personality & Tone
- Communication style details

### Response Rules (CRITICAL)
- Length constraints
- Style requirements

### Memory & Context
- What the bot remembers

### Capabilities
- What the bot can do"""
    
    return base_prompt

def _create_crud_analysis_prompt(output_format: str) -> str:
    """Create analysis prompt for standard CRUD/web applications"""
    
    base_prompt = """You are a senior software architect and requirements analyst specializing in full-stack web applications.
Your task is to extract COMPLETE and DETAILED requirements from the user's message to enable accurate code generation.

## ANALYSIS CATEGORIES

### 1. Application Overview
- Primary purpose and goals
- Target users/audience
- Core value proposition

### 2. Data Entities (CRITICAL for backend)
Identify ALL data entities/models needed. For each entity, determine:
- Entity name (e.g., User, Product, Order)
- Key attributes/fields
- Relationships to other entities (one-to-many, many-to-many)
- Which fields are required vs optional

### 3. API Endpoints (CRITICAL for backend)
Infer the REST API endpoints needed:
- Resource names (plural, lowercase)
- CRUD operations needed for each resource
- Any special endpoints (search, filter, aggregate)
- Authentication requirements per endpoint

### 4. UI Components (CRITICAL for frontend)
Identify the user interface needs:
- Pages/views required
- Forms for data entry
- Lists/tables for displaying data
- Detail views for individual items
- Navigation structure

### 5. Features & Functionalities
- Core features that must be implemented
- Secondary/nice-to-have features
- User workflows and interactions

### 6. Authentication & Authorization
- Is user authentication required?
- User roles and permissions
- Protected vs public resources

### 7. Technical Constraints
- Performance requirements
- Data validation rules
- Business logic constraints

### 8. Integration Requirements
- External APIs or services
- Third-party integrations
- Data import/export needs

"""
    
    if output_format == "json":
        base_prompt += """## OUTPUT FORMAT
Return a valid JSON object with the following structure. Include ALL applicable categories.
Be specific and detailed - this JSON will be used directly for code generation.

{
  "app_type": "crud",
  "app_name": "Descriptive name for the application",
  "description": "Brief description of what the app does",
  "entities": [
    {
      "name": "EntityName",
      "attributes": [
        {"name": "field_name", "type": "string|int|float|bool|datetime|text", "required": true|false}
      ],
      "relationships": ["has_many: OtherEntity", "belongs_to: ParentEntity"]
    }
  ],
  "api_endpoints": [
    {"method": "GET|POST|PUT|DELETE", "path": "/resource", "description": "What it does", "auth_required": true|false}
  ],
  "ui_components": [
    {"name": "ComponentName", "type": "page|form|list|detail|modal", "description": "What it displays"}
  ],
  "features": ["Feature 1", "Feature 2"],
  "auth_required": true|false,
  "user_roles": ["admin", "user"] or [],
  "constraints": ["Constraint 1", "Constraint 2"],
  "integrations": ["Integration 1"] or []
}

IMPORTANT: 
- Set app_type to "crud"
- Return ONLY valid JSON, no additional text or markdown
- Infer reasonable defaults when not explicitly stated
- Include at least one entity with attributes
- Include complete CRUD endpoints for each entity"""
    else:
        base_prompt += """## OUTPUT FORMAT
Format your response as structured sections with clear headers and bullet points.
Be specific and actionable - developers should be able to implement from this analysis.

For each category that applies:
### Category Name
- Specific point 1
- Specific point 2

Focus especially on:
- Naming the data entities clearly
- Listing the API endpoints that will be needed
- Describing the UI components required"""
    
    return base_prompt

async def analyze_requirements(message: str, output_format: str = "text") -> Union[str, Dict[str, Any]]:
    """
    Analyze user requirements and extract structured information
    
    Args:
        message: The user message to analyze
        output_format: Format for output - "text" (human-readable) or "json" (for code generation)
        
    Returns:
        A formatted string or JSON object containing the analyzed requirements
    """
    logger.info(f"Analyzing requirements from: {message[:50]}...")
    
    # Detect application type
    app_type = detect_application_type(message)
    logger.info(f"Detected application type: {app_type}")
    
    # Create appropriate system prompt based on application type
    if app_type == 'chatbot':
        system_prompt = _create_chatbot_analysis_prompt(output_format)
    else:
        system_prompt = _create_crud_analysis_prompt(output_format)

    # Construct prompt for Gemini with instructions to analyze requirements
    prompt = f"System: {system_prompt}\n\nUser input: {message}\n\nAnalysis:"
    
    try:
        # Use LangChain Vertex AI with Gemini
        logger.info(f"[LangChain] Initializing Gemini via Vertex AI for requirements analysis (model: {GEMINI_MODEL})")
        llm = ChatVertexAI(
            model=GEMINI_MODEL,
            project=GCP_PROJECT_ID,
            location=GCP_LOCATION,
            temperature=0.1,  # Low temperature for more factual/analytical response
            max_output_tokens=2048  # Token count for analysis
        )
        
        # Invoke asynchronously using LangChain
        logger.info(f"[LangChain] Invoking requirements analysis via Vertex AI ainvoke()")
        response = await llm.ainvoke(prompt)
        analysis_text = response.content if hasattr(response, 'content') else str(response)
        logger.info(f"[LangChain] Requirements analysis completed via Vertex AI ({len(analysis_text)} chars)")
        analysis_text = analysis_text.strip()
        
        if output_format == "json":
            # Try to parse as JSON
            try:
                json_result = parse_json_result(analysis_text)
                logger.info(f"Requirements analysis completed successfully as JSON")
                return json_result
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                # Fallback to text format
                formatted_analysis = format_analysis_for_display(analysis_text)
                return formatted_analysis
        else:
            # Format for better display in UI
            formatted_analysis = format_analysis_for_display(analysis_text)
            
            logger.info(f"Requirements analysis completed successfully as text")
            return formatted_analysis
    except Exception as e:
        logger.error(f"Exception during requirements analysis: {str(e)}")
        return f"Failed to analyze requirements: {str(e)}"

def parse_json_result(text: str) -> Dict[str, Any]:
    """
    Parse and validate JSON result from LLM
    
    Args:
        text: The raw text from the LLM that should contain JSON
        
    Returns:
        Parsed JSON as a Python dictionary
    """
    # Find JSON content - sometimes the LLM includes extra text
    json_start = text.find('{')
    json_end = text.rfind('}') + 1
    
    if json_start >= 0 and json_end > json_start:
        json_text = text[json_start:json_end]
        return json.loads(json_text)
    else:
        raise ValueError("No valid JSON object found in response")

def format_analysis_for_display(analysis_text: str) -> str:
    """
    Format the analysis text for better display in the UI
    
    Args:
        analysis_text: The raw analysis text from the LLM
        
    Returns:
        Formatted text suitable for UI display
    """
    # Ensure we have some content
    if not analysis_text or len(analysis_text.strip()) < 10:
        return "No clear requirements identified. Please provide more details."
    
    # Split by lines to process categories
    lines = analysis_text.strip().split('\n')
    formatted_lines = []
    current_category = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line is a category header (numbered or with colon)
        if (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.')) and ':' in line) or \
           (line.endswith(':')) or \
           (line.isupper() and len(line) > 3):  # All caps category
            
            # Format as a category header
            current_category = line
            formatted_lines.append(f"### {line}")
        
        # If line starts with bullet or number, it's a point under a category
        elif line.startswith(('- ', '• ', '* ', '· ')) or \
             (len(line) > 2 and line[0].isdigit() and line[1] == '.'):
            formatted_lines.append(line)
        
        # Otherwise treat as continuation or standalone point
        else:
            if current_category:
                formatted_lines.append(f"- {line}")
            else:
                formatted_lines.append(line)
    
    return "\n".join(formatted_lines)

async def analyze_and_format_for_code_generation(message: str) -> Tuple[str, Dict[str, Any]]:
    """
    Analyze requirements and return both human-readable text and JSON for code generation
    
    Args:
        message: The user message to analyze
        
    Returns:
        A tuple containing (human_readable_text, json_for_code_generation)
    """
    # Get JSON output first
    json_output = await analyze_requirements(message, output_format="json")
    
    # Get human-readable text output 
    if isinstance(json_output, dict):
        # If JSON generation was successful, also get text format
        text_output = await analyze_requirements(message, output_format="text")
        return text_output, json_output
    else:
        # If JSON generation failed, we already have text output
        return json_output, {} 