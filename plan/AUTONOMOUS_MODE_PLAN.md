# Autonomous QA Agent Plan (LangGraph)

This document outlines the architecture for the **Autonomous Mode**, enabling the QA Agent to handle the entire testing lifecycle with minimal user intervention.

## 1. System Architecture

We will use **LangGraph** to orchestrate a stateful workflow. The graph will manage the flow of data between strict "nodes" representing each stage of the QA process.

### **Core Components**
- **StateGraph**: Manages legitimacy and transition between steps.
- **Shared State**: A strictly typed `TypedDict` containing:
  - `project_id`: str
  - `files`: List[str] (Paths to source code/docs)
  - `test_plan`: List[Dict] (Generated test cases)
  - `scripts`: List[Dict] (Generated Selenium scripts)
  - `results`: List[Dict] (Execution outputs)
  - `errors`: List[Dict]
  - `retry_count`: int
  - `status`: str

## 2. Workflow Nodes

### **A. Knowledge Ingestion (`node_ingest`)**
- **Input**: Project ID / Files.
- **Action**: 
  - Triggers existing embedding service.
  - Indexes code and documentation into ChromaDB.
- **Output**: Updated vector store status.

### **B. Test Planning (`node_plan_tests`)**
- **Input**: Vector store context.
- **Action**:
  - queries LLM to understand application structure.
  - Generates a list of logical test cases (ID, Description, Steps, Expected Result).
- **Output**: Populates `test_plan` in state.

### **C. Script Generation (`node_gen_scripts`)**
- **Input**: `test_plan`.
- **Action**:
  - Iterates through test cases.
  - Queries LLM (using `selenium_service` prompt) to generate Python code.
  - Validates code syntax.
- **Output**: Populates `scripts` in state.

### **D. Execution (`node_execute`)**
- **Input**: `scripts`.
- **Action**:
  - Executes scripts in parallel or batch using `BatchExecutionService`.
  - Captures video/screenshots.
- **Output**: Populates `results` in state.

### **E. Analysis & Correction (`node_analyze`)**
- **Input**: `results`.
- **Action**:
  - Checks for failures.
  - **Self-Healing**: If failure is due to "Element Not Found", queries LLM with HTML snapshot to fix selector.
  - Decides whether to `Retry` (Edge -> `node_execute`) or `Proceed`.
- **Output**: Updated `results` or modified `scripts`.

### **F. Reporting (`node_report`)**
- **Input**: Final `results`.
- **Action**:
  - Generates a markdown/HTML summary.
  - Calculates metrics (Pass/Fail rate).
- **Output**: Final Report artifact.

## 3. Implementation Steps

### **Phase 7.1: Setup & Dependencies**
- [ ] Install `langgraph`, `langchain-groq`.
- [ ] Define `AgentState` schema.
- [ ] Create `backend/agent/graph.py` to define the graph.

### **Phase 7.2: Node Implementation**
- [ ] Implement `ingest_node` (reuse `project_api`).
- [ ] Implement `planner_node` (reuse `agent_api` logic but automated).
- [ ] Implement `script_gen_node` (looping script generator).
- [ ] Implement `execution_node` (calling `batch_execution_service`).

### **Phase 7.3: API & Frontend**
- [ ] Create `POST /api/autonomous/start`.
- [ ] Create `GET /api/autonomous/status` (Stream graph events).
- [ ] Frontend: "Autonomous Mode" Tab.
  - File uploader / Repo selector.
  - "Start Agent" button.
  - Live Step Visualizer (using a Stepper or Flowchart UI).

## 4. Technology Stack
- **Orchestration**: LangGraph
- **LLM**: Groq (Llama 3 70B)
- **Backend**: FastAPI
- **Frontend**: React + Lucide Icons
