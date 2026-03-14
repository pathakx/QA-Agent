# QA Agent - Complete Project Structure & Function Documentation

## 📁 Project Overview

This is an **Autonomous QA Agent** that generates test cases and Selenium automation scripts from documentation and HTML files using RAG (Retrieval-Augmented Generation) and LLM technology. The project has evolved into a full-stack application with a **React** frontend, **FastAPI** backend, and **Supabase** for authentication and data persistence. It now includes multi-user project support, autonomous execution modes, test suites, and real-time WebSocket updates.

---

## 🏗️ Architecture

```
qa-agent/
├── backend/                    # FastAPI backend server
│   ├── agent/                 # Autonomous agent workflows (LangGraph)
│   ├── api/                   # API route handlers
│   ├── auth/                  # Authentication dependencies
│   ├── core/                  # Core functionality & configuration
│   ├── db/                    # Database models (SQLite/Legacy)
│   ├── parsers/               # Document & HTML parsers
│   └── services/              # Business logic services
├── frontend/                  # React + Vite UI
│   ├── public/
│   └── src/
│       ├── components/        # React components
│       ├── contexts/          # State management (Auth, Project)
│       ├── hooks/             # Custom React hooks
│       └── lib/               # API utilities
├── test_assets/               # Sample test files
├── chroma_db/                 # Vector database storage (Project-isolated)
└── supabase_schema.sql        # Production Database Schema
```

---

## 📄 Detailed File Breakdown

### **Backend Entry Point**

#### `backend/main.py`
**Purpose:** FastAPI application entry point, WebSocket configuration, and Router mounting.

**Key Features:**
- **FastAPI App**: Initializes API with CORS and Exception Handlers.
- **Socket.IO**: Mounts `socket_app` at `/ws` for real-time logs and execution updates.
- **Router Mounting**: Includes routers for Auth, Projects, KB, Agent, Execution, Suites, Scheduler, and Autonomous modes.
- **Static Files**: Serves the React frontend `dist` (or `static`) for production-like access.

---

### **Authentication & Project Management**

#### `backend/auth/dependencies.py`
**Purpose:** Supabase JWT Verification.
- **`get_current_user`**: Verifies `Bearer` token against Supabase Auth, returns user context.

#### `backend/api/auth_api.py`
**Purpose:** User Authentication endpoints.
- **Endpoints**: Login, Signup (proxies to Supabase), Profile management.

#### `backend/api/project_api.py`
**Purpose:** Project CRUD operations.
- **`create_project`**: Creates new project in Supabase + unique ChromaDB collection.
- **`get_user_projects`**: Lists projects for current user.
- **`get_project_stats`**: Returns counts of tests, scripts, and KB files.

---

### **API Layer** (`backend/api/`)

#### `backend/api/docs_api.py`
**Purpose:** Knowledge Base management (Project-scoped).
- **`upload_doc` / `upload_html`**: Uploads files to project-specific storage.
- **`kb_build` / `kb_status`**: Manages embeddings for the specific project.

#### `backend/api/agent_api.py`
**Purpose:** Test Case and Script Generation.
- **`testcase_generation`**: Generates tests using RAG.
- **`create_script`**: Generates Selenium Python scripts.

#### `backend/api/execution_api.py`
**Purpose:** Test Execution Management.
- **`execute_test`**: Triggers Selenium script execution.
- **`get_execution_status`**: Returns pass/fail/running status and logs.

#### `backend/api/suite_api.py`
**Purpose:** Test Suite Management.
- **`create_suite`**: Groups test cases into executable suites.
- **`execute_suite`**: Runs all tests in a suite concurrently or sequentially.

#### `backend/api/autonomous_api.py`
**Purpose:** Autonomous Agent triggers.
- **`start_autonomous`**: Starts the LangGraph autonomous workflow in background.

---

### **Services Layer** (`backend/services/`)

#### `backend/services/project_kb_service.py`
**Purpose:** Multi-tenant Knowledge Base Service.
- Manages ChromaDB collections per project.
- Handles document ingestion and embedding creation (using `sentence-transformers`).

#### `backend/services/project_testcase_service.py`
**Purpose:** RAG-based Test Generation.
- Retrieves context from project's vector store.
- Prompts LLM (Gemini/Groq) to generate JSON test cases.
- Saves generated tests to Supabase.

#### `backend/services/selenium_service.py`
**Purpose:** Selenium Script Generation.
- Generates Python code from Test Case + HTML Context.
- Ensures valid selectors and error handling.

#### `backend/services/execution_service.py`
**Purpose:** Test Execution logic.
- Runs generated Python scripts in a subprocess or protected environment.
- Captures `stdout`/`stderr` and updates execution status in DB.
- Emits real-time progress via WebSockets.

#### `backend/services/batch_execution_service.py`
**Purpose:** Bulk Execution logic.
- Manages execution of Test Suites.
- Aggregates results for Batch Runs.

#### `backend/services/video_recorder.py` & `screenshot_service.py`
**Purpose:** Visual Validation.
- Captures execution artifacts (screenshots/videos) for debugging.

---

### **Database Layer**

#### **Primary: Supabase (PostgreSQL)**
**Schema:** `supabase_schema.sql`, `supabase_migration_phase4.sql`
- **`projects`**: Project metadata.
- **`testcases`**: Generated test scenarios (JSONB steps).
- **`selenium_scripts`**: Generated Python code.
- **`test_executions`**: History of individual test runs.
- **`test_suites`**: Groups of test cases.
- **`batch_runs`**: History of suite executions.
- **`kb_files`** & **`document_chunks`**: Knowledge base tracking.
- **`profiles`**: User profiles.

#### **Legacy/Local: SQLite**
- `backend/db/database.py`: SQLAlchemy models (`TestCase`, `SeleniumScript`) used for local development or fallback.

---

### **Autonomous Agent** (`backend/agent/`)

#### `backend/agent/workflow.py`
**Purpose:** LangGraph State Machine.
**Workflow:**
1. **Plan**: Analyze requirements.
2. **Generate**: Create test cases.
3. **Script**: Generate automation code.
4. **Execute**: Run scripts.
5. **Critique/Repair**: Fix failing scripts loop.

---

### **Frontend** (`frontend/`)

**Tech Stack:** React, Vite, TailwindCSS, Framer Motion, Lucide Icons.

#### `frontend/src/App.jsx`
**Purpose:** Main application layout and routing.
- Context Providers: `AuthProvider`, `ProjectProvider`.
- Main Layout: Sidebar + Content Area.

#### `frontend/src/components/`
- **`AuthPage.jsx`**: Login/Signup form.
- **`ProjectSwitcher.jsx`**: Dropdown to switch active project.
- **`TestSuites.jsx`**: Create and run test suites.
- **`AutonomousMode.jsx`**: Interface for autonomous agent visualization.
- **`ExecutionHistory.jsx`**: Dashboard of past run results.

#### Inline Components (`frontend/src/App.jsx`)
- **`KnowledgeBase`**: File upload and Build KB interface.
- **`TestGenerator`**: AI Prompt interface for creating tests.
- **`ScriptGenerator`**: Script viewer, execution controls, and logs.

---

## 🔄 Data Flow

### 1. **Auth & Project Flow**
```
User Login (Supabase) → Get JWT
Select/Create Project → Backend creates Chroma Collection + DB Entry
All subsequent API calls send Project ID + JWT
```

### 2. **Knowledge Base Build Flow**
```
Upload Files → Saved to `backend/data/<project_id>/`
Click "Build" → `project_kb_service`
Parsers Extract Text → Chunking → Embeddings (ChromaDB `project_collection`)
Metadata saved to Supabase `kb_files`
```

### 3. **Test Generation Flow**
```
User Query → `project_testcase_service`
RAG Retrieve (ChromaDB) → LLM Prompt (Gemini/Groq)
Generate JSON → Save to Supabase `testcases` table
Return to Frontend
```

### 4. **Execution Flow (Real-time)**
```
User Click "Run" → `execution_api`
Backend spawns process → `execution_service`
Updates Supabase `test_executions` status="running"
WebSockets (`sio`) emit logs to Frontend console
Completion → Update Status (pass/fail) + Save Artifacts
```

---

## 🔑 Key Technologies

- **Backend:** FastAPI, Python 3.10+
- **Frontend:** React 18, Vite, TailwindCSS
- **Database:** Supabase (PostgreSQL + Auth), SQLite (Local), ChromaDB (Vector)
- **AI/LLM:** Google Gemini 2.5 Flash, Groq Llama 3.3
- **Automation:** Selenium WebDriver, LangGraph (Autonomous Agents)
- **Real-time:** Socket.IO, WebSockets
