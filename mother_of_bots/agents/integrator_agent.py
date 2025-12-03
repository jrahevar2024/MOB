import logging
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GCS configuration
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("google-cloud-storage not available. GCS upload will be skipped.")


class StandaloneIntegratorAgent:
    """Integrates backend and UI code into a deployable project structure."""

    def __init__(self, name: str = "StandaloneIntegratorAgent"):
        self.name = name
        self.running = False
        logger.info(f"StandaloneIntegratorAgent initialized: {name}")

    async def integrate_project(self, backend_code: str, ui_code: str, requirements: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate a project from backend and UI code."""
        logger.info("[Integrator] Starting project integration")

        if not backend_code or not ui_code:
            logger.error("Missing backend or UI code; cannot integrate project")
            return None

        try:
            import uuid

            project_name = f"generated_project_{uuid.uuid4().hex[:8]}"
            # Use /tmp for writable directory in Kubernetes (always writable)
            project_dir = os.path.join("/tmp", project_name)
            os.makedirs(project_dir, mode=0o755, exist_ok=True)

            backend_dir = os.path.join(project_dir, "backend")
            frontend_dir = os.path.join(project_dir, "frontend")
            os.makedirs(backend_dir, exist_ok=True)
            os.makedirs(frontend_dir, exist_ok=True)

            # Write backend code
            backend_path = os.path.join(backend_dir, "app.py")
            with open(backend_path, "w") as f:
                f.write(backend_code)
            logger.info(f"[Integrator] Backend code written to {backend_path}")

            # Generate backend requirements
            requirements_path = os.path.join(backend_dir, "requirements.txt")
            with open(requirements_path, "w") as f:
                f.write("fastapi>=0.100.0\nuvicorn>=0.23.0\nsqlalchemy>=2.0.0\npydantic>=2.0.0\npython-dotenv>=1.0.0\n")
                if "pandas" in backend_code.lower():
                    f.write("pandas>=2.0.0\n")
                if "numpy" in backend_code.lower():
                    f.write("numpy>=1.24.0\n")
                if "scikit-learn" in backend_code.lower() or "sklearn" in backend_code.lower():
                    f.write("scikit-learn>=1.3.0\n")
                if "matplotlib" in backend_code.lower():
                    f.write("matplotlib>=3.7.0\n")
                if "requests" in backend_code.lower():
                    f.write("requests>=2.31.0\n")
            logger.info(f"[Integrator] Backend requirements saved to {requirements_path}")

            # Write UI code
            ui_path = os.path.join(frontend_dir, "App.jsx")
            with open(ui_path, "w") as f:
                f.write(ui_code)
            logger.info(f"[Integrator] UI code written to {ui_path}")

            # Create index.html
            index_path = os.path.join(frontend_dir, "index.html")
            with open(index_path, "w") as f:
                f.write("""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Generated Application</title>
    <script src=\"https://unpkg.com/react@18/umd/react.development.js\"></script>
    <script src=\"https://unpkg.com/react-dom@18/umd/react-dom.development.js\"></script>
    <script src=\"https://unpkg.com/@babel/standalone/babel.min.js\"></script>
    <script src=\"https://cdn.tailwindcss.com\"></script>
    <script src=\"https://unpkg.com/axios/dist/axios.min.js\"></script>
</head>
<body class=\"bg-gray-100 min-h-screen\">
    <div id=\"root\" class=\"container mx-auto p-4\"></div>
    <script type=\"text/babel\" src=\"App.jsx\"></script>
    <script type=\"text/babel\">
        ReactDOM.render(
            <App />,
            document.getElementById('root')
        );
    </script>
</body>
</html>""")
            logger.info(f"[Integrator] Frontend index.html created at {index_path}")

            # package.json
            package_json_path = os.path.join(frontend_dir, "package.json")
            with open(package_json_path, "w") as f:
                package_json = {
                    "name": "bot-frontend",
                    "version": "0.1.0",
                    "private": True,
                    "dependencies": {
                        "react": "^18.2.0",
                        "react-dom": "^18.2.0",
                        "tailwindcss": "^3.3.0",
                        "axios": "^1.6.0",
                    },
                    "scripts": {
                        "start": "react-scripts start",
                        "build": "react-scripts build",
                    },
                }
                json.dump(package_json, f, indent=2)
            logger.info(f"[Integrator] package.json created at {package_json_path}")

            # README
            readme_path = os.path.join(project_dir, "README.md")
            with open(readme_path, "w") as f:
                f.write(
                    f"""# Generated Project

## Structure
- `backend/`: Python backend code
- `frontend/`: React frontend code

## Setup Instructions

### Backend
1. Navigate to the backend directory:
   ```
   cd {project_dir}/backend
   ```
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the backend server:
   ```
   uvicorn app:app --reload --host 0.0.0.0 --port 8001
   ```

### Frontend
1. Navigate to the frontend directory:
   ```
   cd {project_dir}/frontend
   ```
2. Start a simple HTTP server to serve the frontend:
   ```
   python -m http.server 3000
   ```

## Accessing the Application
- Backend API: http://localhost:8001
- Frontend UI: http://localhost:3000
"""
                )
            logger.info(f"[Integrator] README created at {readme_path}")

            # config.js for API calls
            config_path = os.path.join(frontend_dir, "config.js")
            with open(config_path, "w") as f:
                f.write("""// Configuration for API endpoints
export const API_BASE_URL = 'http://localhost:8001';

export const apiCall = async (endpoint, method = 'GET', data = null) => {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`);
  }
  return await response.json();
};
""")
            logger.info(f"[Integrator] config.js created at {config_path}")

            # Upload project to GCS bucket
            gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "")
            if gcs_bucket_name and GCS_AVAILABLE:
                try:
                    gcs_path = await self._upload_to_gcs(project_dir, project_name, gcs_bucket_name)
                    logger.info(f"[Integrator] Project uploaded to GCS: {gcs_path}")
                except Exception as e:
                    logger.error(f"[Integrator] Failed to upload to GCS: {str(e)}")
                    # Continue even if GCS upload fails
            elif gcs_bucket_name and not GCS_AVAILABLE:
                logger.warning("[Integrator] GCS bucket configured but google-cloud-storage not installed")

            logger.info("[Integrator] Project integration complete")
            return project_dir
        except Exception as exc:
            logger.error(f"Error integrating project: {exc}")
            return None
    
    async def _upload_to_gcs(self, project_dir: str, project_name: str, bucket_name: str) -> str:
        """Upload project directory to GCS bucket."""
        if not GCS_AVAILABLE:
            raise ImportError("google-cloud-storage is not installed")
        
        logger.info(f"[Integrator] Uploading project to GCS bucket: {bucket_name}")
        
        # Initialize GCS client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Upload all files in the project directory
        uploaded_files = []
        project_path = Path(project_dir)
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                # Get relative path from project directory
                relative_path = file_path.relative_to(project_path)
                # Create blob path: projects/{project_name}/{relative_path}
                blob_path = f"projects/{project_name}/{relative_path.as_posix()}"
                
                # Upload file
                blob = bucket.blob(blob_path)
                blob.upload_from_filename(str(file_path))
                uploaded_files.append(blob_path)
                logger.debug(f"[Integrator] Uploaded {relative_path} to gs://{bucket_name}/{blob_path}")
        
        logger.info(f"[Integrator] Uploaded {len(uploaded_files)} files to GCS")
        gcs_path = f"gs://{bucket_name}/projects/{project_name}/"
        return gcs_path

    async def start(self):
        logger.info(f"Starting StandaloneIntegratorAgent: {self.name}")
        self.running = True

    async def stop(self):
        logger.info(f"Stopping StandaloneIntegratorAgent: {self.name}")
        self.running = False

    def is_alive(self) -> bool:
        return self.running
