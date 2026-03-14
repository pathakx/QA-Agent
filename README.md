# QA Agent - AI Powered Testing Assistant

This project is an autonomous QA agent capable of generating test cases and Selenium scripts from documentation and HTML files using RAG (Retrieval-Augmented Generation) and LLM technology.

## 🚀 Key Features
- **Knowledge Base**: Upload requirements (PDF, MD, TXT) and HTML files.
- **AI Test Generator**: Create comprehensive test cases from requirements.
- **Script Automation**: Convert test cases into ready-to-run Selenium Python scripts.
- **Modern UI**: React + Tailwind CSS frontend served directly by the backend.

## Prerequisites

- Python 3.8+
- Node.js & NPM (for frontend development only)
- Chrome Browser (for Selenium)
- .env file with API keys:
    ```env
    GEMINI_API_KEY=YOUR_KEY
    # or
    GROQ_API_KEY=YOUR_KEY
    LLM_PROVIDER=gemini # or groq
    ```

## 🛠️ Quick Start

The application is now a single monolithic server. The React frontend is built and served automatically by the Python backend.

1.  **Open a terminal** in the project root.

2.  **Activate the virtual environment**:
    *   Windows: `.venv\Scripts\activate` or `venv\Scripts\activate`
    *   Mac/Linux: `source venv/bin/activate`

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Start the App**:
    ```bash
    python -m backend.main
    ```

5.  **Access the Interface**:
    *   Open your browser to: `http://localhost:8000`

---

## 👨‍💻 Development

If you want to modify the React Frontend:

1.  Navigate to `frontend/`:
    ```bash
    cd frontend
    npm install
    ```
2.  Start the dev server:
    ```bash
    npm run dev
    ```
3.  Build for production (updates the backend static files):
    ```bash
    npm run build
    ```

