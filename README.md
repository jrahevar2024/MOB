# 🤖 Mother of Bots - Multi-Agent Chat Interface

A powerful multi-agent system that creates chatbots and full-stack applications through natural language conversations. Built with Flask, React, and powered by Google Vertex AI (Gemini).

## 🌟 Features

- **Natural Language Requirements Analysis** - Describe what you want, and the system analyzes it
- **Automated Code Generation** - Generates both backend (Python/Flask) and frontend (React) code
- **Full Project Integration** - Combines code into a complete, deployable project
- **Automatic Deployment** - Deploys generated applications to local servers
- **Modern React UI** - Beautiful, responsive interface with real-time updates
- **Document Upload Support** - Upload PDFs, DOCX, TXT, XLSX files for context
- **Multi-Agent Architecture** - Specialized agents for different tasks

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│           (http://localhost:3000)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                   Flask API Backend                      │
│           (http://localhost:5000)                        │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  Requirements    │  │  Code Generation │            │
│  │  Analyzer Agent  │  │     Agent        │            │
│  └──────────────────┘  └──────────────────┘            │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  UI Generation   │  │   Integrator     │            │
│  │     Agent        │  │      Agent       │            │
│  └──────────────────┘  └──────────────────┘            │
│  ┌──────────────────┐                                   │
│  │   Deployer       │                                   │
│  │     Agent        │                                   │
│  └──────────────────┘                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Google Vertex AI (Gemini)                   │
│              gemini-2.5-flash                            │
└─────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Google Cloud Project** with Vertex AI API enabled
- **gcloud CLI** installed and configured

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd MOB-Project
```

### 2. Backend Setup (Python/Flask)

```bash
# Create and activate virtual environment
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup (React)

```bash
cd react-frontend
npm install
cd ..
```

### 4. Google Cloud Authentication

```bash
# Login to Google Cloud
gcloud auth application-default login

# Set your project (replace with your project ID)
gcloud config set project YOUR_PROJECT_ID
```

### 5. Environment Variables

Create a `.env` file in the root directory:

```env
# Google Cloud Configuration
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash

# API Configuration
API_BASE_URL=http://localhost:5000
API_PORT=5000
```

## 🎮 Running the Application

### Start Backend (Terminal 1)

```bash
# Make sure virtual environment is activated
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # macOS/Linux

# Start Flask API
python -m mother_of_bots.api
```

The Flask API will be available at: **http://localhost:5000**

### Start Frontend (Terminal 2)

```bash
cd react-frontend
npm run dev
```

The React frontend will be available at: **http://localhost:3000**

### Open in Browser

Navigate to **http://localhost:3000** and start creating chatbots!

## 📖 Usage

### Creating a Chatbot

1. Open the React frontend at http://localhost:3000
2. Type your request in the chat input:
   ```
   Create a hotel management chatbot for customer service
   ```
3. Click "Send" or press Enter
4. Watch as the system:
   - Analyzes your requirements
   - Generates backend code
   - Generates frontend UI
   - Integrates everything into a project
   - Deploys it automatically

### Uploading Documents

1. Click the file upload area or drag & drop files
2. Supported formats: PDF, DOCX, DOC, TXT, XLSX, XLS
3. The content will be included in your request for context

### Settings

- **Show requirements analysis**: Display detailed analysis in chat
- **Auto-generate code**: Automatically generate code when detected
- **Deploy generated projects**: Auto-deploy completed projects

## 📁 Project Structure

```
MOB-Project/
├── mother_of_bots/              # Backend Python code
│   ├── agents/                  # Agent modules
│   │   ├── requirements_analyzer.py
│   │   ├── code_generation_agent.py
│   │   ├── ui_generation_agent.py
│   │   ├── integrator_agent.py
│   │   └── deployer_agent.py
│   ├── api.py                   # Flask API
│   └── streamlit_app.py         # Legacy Streamlit frontend
├── react-frontend/              # React frontend (NEW!)
│   ├── src/
│   │   ├── App.jsx              # Main component
│   │   ├── App.css              # Styles
│   │   └── main.jsx             # Entry point
│   ├── package.json
│   └── vite.config.js
├── generated_project_*/         # Generated projects (gitignored)
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (gitignored)
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🔧 Technologies Used

### Backend
- **Flask** - Web framework for REST API
- **LangChain** - LLM orchestration framework
- **Google Vertex AI** - LLM provider (Gemini)
- **Python 3.13** - Core language

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **Lucide React** - Icon library
- **CSS3** - Modern styling

### AI/ML
- **Gemini 2.5 Flash** - Google's latest language model
- **Vertex AI** - Google Cloud's ML platform

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check API health status |
| `/api/analyze-requirements` | POST | Analyze user requirements |
| `/api/generate-code` | POST | Generate backend code |
| `/api/generate-ui` | POST | Generate UI code |
| `/api/integrate-project` | POST | Integrate code into project |
| `/api/deploy-project` | POST | Deploy project |
| `/api/generate-full-project` | POST | Complete workflow (all-in-one) |

## 🐛 Troubleshooting

### API Connection Error
```
Error: Cannot connect to Flask API
```
**Solution**: Make sure the Flask API is running on port 5000

### Google Cloud Authentication Error
```
503 Getting metadata from plugin failed
```
**Solution**: Re-authenticate with Google Cloud:
```bash
gcloud auth application-default login
```

### React Build Errors
```
npm error code ENOENT
```
**Solution**: Make sure you're in the `react-frontend` directory and run:
```bash
npm install
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Your Team Name
- Software Engineering - SEM 3
- FAU Assignments

## 🙏 Acknowledgments

- Google Cloud for Vertex AI
- LangChain for LLM orchestration
- React team for the amazing framework
- Flask team for the web framework

## 📮 Support

For issues and questions, please open an issue on GitHub.

---

**Made with ❤️ using React, Flask, and Google Gemini**
