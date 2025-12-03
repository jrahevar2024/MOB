"""
Flask application for Mother of Bots agents
Replaces SPADE with REST API endpoints
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import asyncio
import traceback
from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI

# Import standalone agents
from .agents.requirements_analyzer import analyze_requirements, analyze_and_format_for_code_generation
from .agents.code_generation_agent import StandaloneCodeGenerationAgent
from .agents.ui_generation_agent import StandaloneUIGenerationAgent
from .agents.integrator_agent import StandaloneIntegratorAgent
from .agents.deployer_agent import StandaloneDeployerAgent
from .document_processor import process_document

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Add CORS to allow Streamlit to call the API
CORS(app, resources={r"/*": {"origins": "*"}})

# Store active deployer agents for stopping services
active_deployer_agents = {}


def run_async(coro):
    """Helper to run async functions in sync Flask context"""
    return asyncio.run(coro)


# Health check endpoint
@app.route("/", methods=["GET"])
def root():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Mother of Bots API",
        "version": "1.0.0",
        "framework": "Flask",
        "llm_framework": "LangChain"
    })


@app.route("/health", methods=["GET"])
def health():
    """Detailed health check"""
    return jsonify({
        "status": "healthy",
        "langchain": "active",
        "llm_provider": "vertex_ai",
        "gcp_project_id": os.getenv("GCP_PROJECT_ID", "motherofbots"),
        "gcp_location": os.getenv("GCP_LOCATION", "us-central1"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    })


# Document Processing Endpoint
@app.route("/api/process-document", methods=["POST"])
def process_document_endpoint():
    """
    Process uploaded documents (PDF, DOCX, DOC, TXT, XLSX) and extract text
    
    Expected form data:
        file: File object - The uploaded file
        file_name: str (optional) - The file name
        file_type: str (optional) - The MIME type
        
    Returns:
        Document info with extracted text content
    """
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "detail": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "detail": "No file selected"}), 400
        
        file_name = request.form.get('file_name', file.filename)
        file_type = request.form.get('file_type', file.content_type or '')
        
        # Read file bytes
        file_bytes = file.read()
        
        # Process document
        result = process_document(file_bytes, file_name, file_type)
        
        if result and result.get("status") == "error":
            return jsonify(result), 400
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"[API] Error processing document: {str(e)}")
        return jsonify({"status": "error", "detail": f"Error processing document: {str(e)}"}), 500


# GCP/Vertex AI Status Check Endpoint
@app.route("/api/check-gcp-status", methods=["GET"])
def check_gcp_status_endpoint():
    """
    Check GCP credentials and Vertex AI status
    
    Returns:
        Status of GCP credentials and Vertex AI availability
    """
    try:
        # Check GCP credentials
        gcp_status = {"configured": False, "project": None, "error": None}
        try:
            import google.auth
            credentials, project = google.auth.default()
            if credentials:
                gcp_status["configured"] = True
                gcp_status["project"] = project or os.getenv("GCP_PROJECT_ID", "motherofbots")
            else:
                gcp_status["error"] = "GCP credentials not found"
        except Exception as e:
            gcp_status["error"] = str(e)
        
        # Check LangChain Vertex AI
        langchain_status = {"available": False, "error": None}
        try:
            from langchain_google_vertexai import ChatVertexAI
            GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "motherofbots")
            GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
            GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            
            test_llm = ChatVertexAI(
                model=GEMINI_MODEL,
                project=GCP_PROJECT_ID,
                location=GCP_LOCATION
            )
            langchain_status["available"] = True
        except ImportError as e:
            langchain_status["error"] = f"LangChain Vertex AI not available: {str(e)}"
        except Exception as e:
            langchain_status["error"] = f"Vertex AI connection test failed: {str(e)}"
        
        return jsonify({
            "status": "success",
            "gcp": gcp_status,
            "langchain_vertex_ai": langchain_status,
            "gcp_project_id": os.getenv("GCP_PROJECT_ID", "motherofbots"),
            "gcp_location": os.getenv("GCP_LOCATION", "us-central1"),
            "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        })
    except Exception as e:
        logger.error(f"[API] Error checking GCP status: {str(e)}")
        return jsonify({"status": "error", "detail": f"Error checking GCP status: {str(e)}"}), 500


# Simple Chat Endpoint (for users - direct Gemini chat without prompt engineering)
@app.route("/api/simple-chat", methods=["POST"])
def simple_chat_endpoint():
    """
    Simple chat endpoint - direct Gemini conversation without prompt engineering
    Similar to Gemini web chat interface
    
    Expected JSON:
        message: str - User's message
        conversation_history: list (optional) - Previous messages for context
        
    Returns:
        Simple chat response from Gemini
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"status": "error", "detail": "Message is required"}), 400
        
        user_message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])
        
        if not user_message.strip():
            return jsonify({"status": "error", "detail": "Message cannot be empty"}), 400
        
        # Get GCP configuration
        gcp_project_id = os.getenv("GCP_PROJECT_ID", "motherofbots")
        gcp_location = os.getenv("GCP_LOCATION", "us-central1")
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        # Create simple chat function
        async def get_chat_response():
            try:
                # Initialize ChatVertexAI with minimal configuration
                llm = ChatVertexAI(
                    model=gemini_model,
                    project=gcp_project_id,
                    location=gcp_location,
                    temperature=0.7  # Slightly higher for more natural conversation
                )
                
                # Build conversation context if history provided
                if conversation_history:
                    # Format history for LangChain
                    messages = []
                    for msg in conversation_history[-10:]:  # Keep last 10 messages for context
                        role = msg.get('role', 'user')
                        content = msg.get('content', '')
                        if role == 'user':
                            messages.append(("human", content))
                        elif role == 'assistant':
                            messages.append(("ai", content))
                    
                    # Add current message
                    messages.append(("human", user_message))
                    
                    # Invoke with conversation history
                    response = await llm.ainvoke(messages)
                else:
                    # Simple single message
                    response = await llm.ainvoke(user_message)
                
                response_text = response.content if hasattr(response, 'content') else str(response)
                return response_text.strip()
            except Exception as e:
                logger.error(f"Error in simple chat: {str(e)}")
                raise
        
        # Run async function
        response_text = run_async(get_chat_response())
        
        return jsonify({
            "status": "success",
            "response": response_text
        })
        
    except Exception as e:
        logger.error(f"Error in simple chat endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "detail": f"Error in chat: {str(e)}"}), 500


@app.route("/api/stop-deployment", methods=["POST"])
def stop_deployment_endpoint():
    """
    Stop currently running deployed services
    
    Expected JSON body (optional):
        deployment_id: str - ID of the deployment to stop (if not provided, stops all)
        
    Returns:
        Status of stopping services
    """
    try:
        data = request.get_json() or {}
        deployment_id = data.get("deployment_id")
        
        if deployment_id and deployment_id in active_deployer_agents:
            # Stop specific deployment
            agent = active_deployer_agents[deployment_id]
            run_async(agent.stop())
            del active_deployer_agents[deployment_id]
            logger.info(f"[API] Stopped deployment {deployment_id}")
            return jsonify({
                "status": "success",
                "message": f"Deployment {deployment_id} stopped successfully"
            })
        elif deployment_id:
            return jsonify({
                "status": "error",
                "detail": f"Deployment {deployment_id} not found"
            }), 404
        else:
            # Stop all deployments
            stopped_count = 0
            for dep_id, agent in list(active_deployer_agents.items()):
                try:
                    run_async(agent.stop())
                    stopped_count += 1
                    logger.info(f"[API] Stopped deployment {dep_id}")
                except Exception as e:
                    logger.error(f"[API] Error stopping deployment {dep_id}: {str(e)}")
            
            active_deployer_agents.clear()
            
            return jsonify({
                "status": "success",
                "message": f"Stopped {stopped_count} deployment(s) successfully"
            })
    except Exception as e:
        logger.error(f"[API] Error stopping deployment: {str(e)}")
        return jsonify({"status": "error", "detail": f"Error stopping deployment: {str(e)}"}), 500


# Requirements Analysis Endpoint
@app.route("/api/analyze-requirements", methods=["POST"])
def analyze_requirements_endpoint():
    """
    Analyze user requirements and extract structured information
    
    Expected JSON body:
        message: str - The user message to analyze
        output_format: str - "text" or "json" (default: "text")
        
    Returns:
        Analyzed requirements in text or JSON format
    """
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"status": "error", "detail": "Missing 'message' field"}), 400
        
        message = data["message"]
        output_format = data.get("output_format", "text")
        
        logger.info(f"[API] Analyzing requirements: {message[:50]}...")
        result = run_async(analyze_requirements(message, output_format))
        return jsonify({
            "status": "success",
            "result": result,
            "format": output_format
        })
    except Exception as e:
        logger.error(f"[API] Error analyzing requirements: {str(e)}")
        return jsonify({"status": "error", "detail": f"Error analyzing requirements: {str(e)}"}), 500


@app.route("/api/analyze-requirements-full", methods=["POST"])
def analyze_requirements_full_endpoint():
    """
    Analyze requirements and return both text and JSON formats
    
    Expected JSON body:
        message: str - The user message to analyze
        
    Returns:
        Tuple of (text_analysis, json_analysis)
    """
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"status": "error", "detail": "Missing 'message' field"}), 400
        
        message = data["message"]
        
        logger.info(f"[API] Analyzing requirements (full): {message[:50]}...")
        text_result, json_result = run_async(analyze_and_format_for_code_generation(message))
        return jsonify({
            "status": "success",
            "text_analysis": text_result,
            "json_analysis": json_result
        })
    except Exception as e:
        logger.error(f"[API] Error in full requirements analysis: {str(e)}")
        return jsonify({"status": "error", "detail": f"Error analyzing requirements: {str(e)}"}), 500


# Code Generation Endpoint
@app.route("/api/generate-code", methods=["POST"])
def generate_code_endpoint():
    """
    Generate backend code based on requirements
    
    Expected JSON body:
        requirements: str or dict - The requirements for code generation
        
    Returns:
        Generated backend code
    """
    async def _generate_code(requirements):
        agent = StandaloneCodeGenerationAgent()
        await agent.start()
        try:
            code = await agent.generate_code(requirements)
            return code
        finally:
            await agent.stop()
    
    try:
        data = request.get_json()
        if not data or "requirements" not in data:
            return jsonify({"status": "error", "detail": "Missing 'requirements' field"}), 400
        
        requirements = data["requirements"]
        
        logger.info(f"[API] Generating code for requirements")
        code = run_async(_generate_code(requirements))
        return jsonify({
            "status": "success",
            "code": code,
            "length": len(code)
        })
    except Exception as e:
        logger.error(f"[API] Error generating code: {str(e)}")
        return jsonify({"status": "error", "detail": f"Error generating code: {str(e)}"}), 500


# UI Generation Endpoint
@app.route("/api/generate-ui", methods=["POST"])
def generate_ui_endpoint():
    """
    Generate UI code based on requirements
    
    Expected JSON body:
        requirements: str or dict - The requirements for UI generation
        
    Returns:
        Generated UI code
    """
    async def _generate_ui(requirements):
        agent = StandaloneUIGenerationAgent()
        await agent.start()
        try:
            ui_code = await agent.generate_ui_code(requirements)
            return ui_code
        finally:
            await agent.stop()
    
    try:
        data = request.get_json()
        if not data or "requirements" not in data:
            return jsonify({"status": "error", "detail": "Missing 'requirements' field"}), 400
        
        requirements = data["requirements"]
        
        logger.info(f"[API] Generating UI code for requirements")
        ui_code = run_async(_generate_ui(requirements))
        return jsonify({
            "status": "success",
            "ui_code": ui_code,
            "length": len(ui_code)
        })
    except Exception as e:
        logger.error(f"[API] Error generating UI code: {str(e)}")
        return jsonify({"status": "error", "detail": f"Error generating UI code: {str(e)}"}), 500


# Project Integration Endpoint
@app.route("/api/integrate-project", methods=["POST"])
def integrate_project_endpoint():
    """
    Integrate backend and UI code into a complete project
    
    Expected JSON body:
        backend_code: str - The backend code
        ui_code: str - The UI code
        requirements: dict (optional) - Additional requirements
        
    Returns:
        Project directory path
    """
    async def _integrate_project(backend_code, ui_code, requirements):
        agent = StandaloneIntegratorAgent()
        await agent.start()
        try:
            project_dir = await agent.integrate_project(backend_code, ui_code, requirements)
            return project_dir
        finally:
            await agent.stop()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "detail": "Missing request body"}), 400
        if "backend_code" not in data:
            return jsonify({"status": "error", "detail": "Missing 'backend_code' field"}), 400
        if "ui_code" not in data:
            return jsonify({"status": "error", "detail": "Missing 'ui_code' field"}), 400
        
        backend_code = data["backend_code"]
        ui_code = data["ui_code"]
        requirements = data.get("requirements", {})
        
        logger.info(f"[API] Integrating project")
        project_dir = run_async(_integrate_project(backend_code, ui_code, requirements))
        return jsonify({
            "status": "success",
            "project_dir": project_dir,
            "exists": os.path.exists(project_dir) if project_dir else False
        })
    except Exception as e:
        logger.error(f"[API] Error integrating project: {str(e)}")
        return jsonify({"status": "error", "detail": f"Error integrating project: {str(e)}"}), 500


# Deployment Endpoint
@app.route("/api/deploy-project", methods=["POST"])
def deploy_project_endpoint():
    """
    Deploy a generated project to local servers
    
    Expected JSON body:
        project_dir: str - Path to the project directory
        
    Returns:
        Deployment status with backend and frontend URLs
    """
    async def _deploy_project(project_dir):
        agent = StandaloneDeployerAgent()
        await agent.start()
        result = await agent.deploy_project(project_dir)
        # Store agent for later stopping
        import uuid
        deployment_id = str(uuid.uuid4())
        active_deployer_agents[deployment_id] = agent
        result["deployment_id"] = deployment_id
        return result
    
    try:
        data = request.get_json()
        if not data or "project_dir" not in data:
            return jsonify({"status": "error", "detail": "Missing 'project_dir' field"}), 400
        
        project_dir = data["project_dir"]
        
        logger.info(f"[API] Deploying project: {project_dir}")
        result = run_async(_deploy_project(project_dir))
        return jsonify(result)
    except Exception as e:
        logger.error(f"[API] Error deploying project: {str(e)}")
        return jsonify({"status": "error", "detail": f"Error deploying project: {str(e)}"}), 500


# Full Workflow Endpoint (all-in-one)
@app.route("/api/generate-full-project", methods=["POST"])
def generate_full_project_endpoint():
    """
    Complete workflow: Analyze requirements -> Generate code -> Generate UI -> Integrate -> Deploy
    
    Expected JSON body:
        message: str - The user requirements message
        
    Returns:
        Complete project information including deployment URLs
    """
    async def _full_workflow(message):
        code_agent = None
        ui_agent = None
        integrator_agent = None
        deployer_agent = None
        
        # Step 1: Analyze requirements
        logger.info("[API] Step 1: Analyzing requirements")
        text_analysis, json_analysis = await analyze_and_format_for_code_generation(message)
        logger.info(f"[API] Step 1 complete: Analysis length - {len(text_analysis)} chars")
        
        # Step 2: Generate backend code
        logger.info("[API] Step 2: Generating backend code")
        code_agent = StandaloneCodeGenerationAgent()
        await code_agent.start()
        try:
            requirements_input = json_analysis if isinstance(json_analysis, dict) else message
            backend_code = await code_agent.generate_code(requirements_input)
            logger.info(f"[API] Step 2 complete: Backend code length - {len(backend_code)} chars")
        finally:
            await code_agent.stop()
        
        # Step 3: Check if UI is needed and generate
        ui_code = None
        combined_text = message.lower() + " " + text_analysis.lower()
        if isinstance(json_analysis, dict):
            combined_text += " " + str(json_analysis).lower()
        
        ui_keywords = ["ui", "interface", "frontend", "react", "vue", "angular", "web page", "website", 
                     "chatbot", "chat", "conversational", "user interface", "dashboard", "bot", 
                     "create", "build", "generate", "make"]
        chatbot_keywords = ["chatbot", "chat bot", "conversational", "bot", "assistant"]
        is_chatbot_request = any(keyword in combined_text for keyword in chatbot_keywords)
        needs_ui = is_chatbot_request or any(keyword in combined_text for keyword in ui_keywords)
        
        if needs_ui:
            logger.info("[API] Step 3: Generating UI code")
            ui_agent = StandaloneUIGenerationAgent()
            await ui_agent.start()
            try:
                requirements_input = json_analysis if isinstance(json_analysis, dict) else message
                ui_code = await ui_agent.generate_ui_code(requirements_input)
                logger.info(f"[API] Step 3 complete: UI code length - {len(ui_code)} chars")
            except Exception as e:
                logger.warning(f"[API] Step 3 failed, continuing without UI: {str(e)}")
                ui_code = None
            finally:
                await ui_agent.stop()
        else:
            logger.info("[API] Step 3: Skipping UI generation (not needed)")
        
        # Step 4: Integrate project
        logger.info("[API] Step 4: Integrating project")
        integrator_agent = StandaloneIntegratorAgent()
        await integrator_agent.start()
        try:
            project_dir = await integrator_agent.integrate_project(
                backend_code,
                ui_code or "",
                json_analysis if isinstance(json_analysis, dict) else {}
            )
            logger.info(f"[API] Step 4 complete: Project directory - {project_dir}")
            
            # Get GCS path if available
            gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "")
            gcs_path = None
            if project_dir and gcs_bucket_name:
                project_name = os.path.basename(project_dir)
                gcs_path = f"gs://{gcs_bucket_name}/projects/{project_name}/"
        finally:
            await integrator_agent.stop()
        
        # Step 5: Deploy project
        deployment_result = {}
        try:
            logger.info("[API] Step 5: Deploying project")
            deployer_agent = StandaloneDeployerAgent()
            await deployer_agent.start()
            deployment_result = await deployer_agent.deploy_project(project_dir)
            # Store agent for later stopping
            import uuid
            deployment_id = str(uuid.uuid4())
            active_deployer_agents[deployment_id] = deployer_agent
            deployment_result["deployment_id"] = deployment_id
            logger.info(f"[API] Step 5 complete: Deployment successful")
        except Exception as e:
            logger.warning(f"[API] Step 5 failed: {str(e)}")
            deployment_result = {
                "status": "error",
                "error": str(e),
                "message": "Project generated but deployment failed"
            }
        
        return {
            "status": "success",
            "requirements_analysis": {
                "text": text_analysis,
                "json": json_analysis
            },
            "generated_code": {
                "backend": backend_code,
                "ui": ui_code,
                "backend_length": len(backend_code),
                "ui_length": len(ui_code) if ui_code else 0
            },
            "project": {
                "directory": project_dir,
                "exists": os.path.exists(project_dir) if project_dir else False,
                "gcs_path": gcs_path if 'gcs_path' in locals() else None
            },
            "deployment": deployment_result
        }
    
    try:
        # Better error handling for JSON parsing
        if not request.is_json and request.content_type and 'application/json' not in request.content_type:
            logger.error(f"[API] Request is not JSON. Content-Type: {request.content_type}")
            return jsonify({"status": "error", "detail": "Request must be JSON"}), 400
        
        try:
            data = request.get_json(force=True)
        except Exception as json_error:
            logger.error(f"[API] Failed to parse JSON: {str(json_error)}")
            logger.error(f"[API] Request data preview: {str(request.data[:500]) if request.data else 'No data'}")
            return jsonify({"status": "error", "detail": f"Invalid JSON: {str(json_error)}"}), 400
        
        if not data or "message" not in data:
            return jsonify({"status": "error", "detail": "Missing 'message' field"}), 400
        
        message = data["message"]
        
        # Truncate very long messages to prevent memory issues
        max_message_length = 15000
        if len(message) > max_message_length:
            logger.warning(f"[API] Message is very long ({len(message)} chars), truncating to {max_message_length}")
            message = message[:max_message_length] + "\n\n[Message truncated for processing...]"
        
        logger.info(f"[API] Starting full project generation workflow (message length: {len(message)})")
        result = run_async(_full_workflow(message))
        return jsonify(result)
    except Exception as e:
        logger.error(f"[API] Unexpected error in full project generation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "detail": f"Error generating full project: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "5000"))  # Default to 5000 to match React frontend
    app.run(host="0.0.0.0", port=port, debug=True)
