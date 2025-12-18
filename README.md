# QA Agent
Live URL: https://qualityautomation.streamlit.app/

This project is an autonomous QA agent capable of generating test cases and Selenium scripts from documentation and HTML files.

## Prerequisites

- Python 3.8+
- Chrome Browser (for Selenium)
- Virtual Environment (created in setup)
- API Keys:
  - Groq API Key (for LLM)
  - Pinecone API Key (for vector storage)

## Environment Setup

Create a `.env` file in the project root with the following variables:

```env
# Groq LLM Configuration
GROQ_API_KEY=your_groq_api_key_here

# Pinecone Vector Store Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=qa-agent-index
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# Backend URL
BACKEND_URL=http://localhost:8000
```

**Getting API Keys:**

1. **Groq API Key:**
   - Sign up at [console.groq.com](https://console.groq.com/)
   - Go to API Keys section
   - Create and copy your API key

2. **Pinecone API Key:**
   - Sign up at [pinecone.io](https://www.pinecone.io/) (free tier available)
   - Create a project
   - Copy your API key from the dashboard


## Starting the Application

1.  **Open a terminal** and navigate to the project root `qa-agent/`.
2.  **Activate the virtual environment**:
    *   Windows: `venv\Scripts\activate`
    *   Mac/Linux: `source venv/bin/activate`
```
   pip install -r requirements.txt
```

3.  **Start the Backend (FastAPI)**:
    ```bash
    uvicorn backend.main:app --reload
    ```
    *   The backend will run at `http://localhost:8000`.
    *   Health check: `http://localhost:8000/health`

4.  **Start the Frontend (Streamlit)**:
    *   Open a **new terminal**, activate `venv`, and run:
    ```bash
    streamlit run frontend/streamlit_app.py
    ```
    *   The UI will open in your browser at `http://localhost:8501`.

## How to Test (End-to-End Workflow)

We will use the generated assets in `test_assets/` to test the agent.

### 1. Populate Knowledge Base
1.  Go to the **Knowledge Base** tab in the Streamlit UI.
2.  **Upload Documents**:
    *   Select `test_assets/product_specs.md`, `test_assets/ui_ux_guide.txt`, and `test_assets/api_endpoints.json`.
    *   Click "Upload Documents".
3.  **Upload HTML**:
    *   Select `test_assets/checkout.html`.
    *   Click "Upload HTML".

### 2. Generate Test Cases
1.  Go to the **Test Cases** tab.
2.  Enter a requirement query, for example:
    > "Generate end-to-end test cases for the checkout flow, including valid purchase and invalid email validation."
3.  Click "Generate Test Cases".
4.  Review the generated test cases.
5.  **Select a test case** from the dropdown menu at the bottom.

### 3. Generate Selenium Script
1.  Go to the **Selenium Scripts** tab.
2.  Verify the selected test case is displayed.
3.  Click "Generate Selenium Script".
4.  The agent will generate a Python script.
5.  **Download** the script (e.g., `test_checkout.py`).

### 4. Run the Selenium Script
1.  Open the downloaded script in your editor.
2.  **Important**: Check the `driver.get("...")` line.
    *   Ensure it points to the correct location of `checkout.html`.
    *   If testing locally, you can use the absolute path: `file:///C:/path/to/qa-agent/test_assets/checkout.html`.
3.  Run the script:
    ```bash
    python test_checkout.py
    ```
4.  Watch the browser automate the test!
