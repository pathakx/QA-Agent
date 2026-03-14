# Test Execution Engine - Implementation Plan

## 📋 Overview

Transform the QA Agent from a test case generator into a **complete testing solution** by adding the ability to execute Selenium scripts, capture results, and provide real-time feedback.

---

## 🎯 Goals

1. **Execute** generated Selenium scripts automatically
2. **Capture** screenshots, logs, and videos during execution
3. **Report** pass/fail status with detailed error messages
4. **Monitor** test execution in real-time
5. **Store** execution history for analysis

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Test List   │  │ Run Button   │  │ Results View    │   │
│  │ (Select)    │  │ (Trigger)    │  │ (Real-time)     │   │
│  └──────┬──────┘  └──────┬───────┘  └────────▲────────┘   │
└─────────┼────────────────┼──────────────────┼──────────────┘
          │                │                  │
          │     WebSocket for real-time updates
          │                │                  │
┌─────────▼────────────────▼──────────────────┼──────────────┐
│                      Backend API                            │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────┐   │
│  │ Execution    │  │ WebSocket      │  │ Results     │   │
│  │ Manager      │  │ Server         │  │ Storage     │   │
│  └──────┬───────┘  └────────────────┘  └─────▲───────┘   │
│         │                                      │           │
│  ┌──────▼──────────────────────────────────────┼───────┐  │
│  │           Selenium Runner Process            │       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────┴────┐  │  │
│  │  │ Browser  │  │Screenshot│  │ Video Recorder   │  │  │
│  │  │ Driver   │  │ Capture  │  │ (Optional)       │  │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Phase-by-Phase Implementation

### **Phase 1: Basic Execution (Week 1)** 🟢 CRITICAL

**Goal**: Run a single Selenium script and capture basic results

#### Backend Tasks:
- [ ] Install dependencies: `selenium`, `webdriver-manager`
- [ ] Create `execution_service.py` - core execution logic
- [ ] Add `TestExecution` database model (status, logs, timestamps)
- [ ] Create `/api/agent/execute/{test_id}` endpoint
- [ ] Implement basic script runner (Chrome only)
- [ ] Capture execution status (pass/fail)
- [ ] Store execution logs

#### Frontend Tasks:
- [ ] Add "Run Test" button to test case cards
- [ ] Show loading state during execution
- [ ] Display execution result (pass/fail badge)
- [ ] Show basic error messages

#### Database Schema:
```sql
CREATE TABLE test_executions (
    id INTEGER PRIMARY KEY,
    test_case_id VARCHAR(50),
    status VARCHAR(20),  -- 'running', 'passed', 'failed', 'error'
    started_at DATETIME,
    completed_at DATETIME,
    duration_seconds FLOAT,
    error_message TEXT,
    logs TEXT
);
```

#### Deliverables:
✅ Single test execution working  
✅ Results saved to database  
✅ UI shows pass/fail status

---

### **Phase 2: Advanced Execution (Week 2)** 🟡 HIGH PRIORITY

**Goal**: Add screenshots, better error handling, and execution details

#### Backend Tasks:
- [ ] Implement screenshot capture on failure
- [ ] Store screenshots in `./test_results/{test_id}/screenshots/`
- [ ] Capture detailed stack traces
- [ ] Add execution metadata (browser version, OS, etc.)
- [ ] Create `/api/agent/executions/{test_id}` - get execution history
- [ ] Add `/api/agent/executions/{execution_id}/screenshot` endpoint

#### Frontend Tasks:
- [ ] Create "Execution History" section per test
- [ ] Display screenshots in results view
- [ ] Show detailed error messages with stack traces
- [ ] Add timestamp and duration display
- [ ] Create modal for viewing execution details

#### Database Schema Updates:
```sql
ALTER TABLE test_executions ADD COLUMN screenshot_path TEXT;
ALTER TABLE test_executions ADD COLUMN browser_version VARCHAR(50);
ALTER TABLE test_executions ADD COLUMN os_info VARCHAR(100);
```

#### Deliverables:
✅ Screenshots on failure  
✅ Execution history view  
✅ Detailed error reporting

---

### **Phase 3: Real-time Execution (Week 3)** 🟡 HIGH PRIORITY

**Goal**: Stream execution progress and logs in real-time

#### Backend Tasks:
- [ ] Install `python-socketio`, `aiofiles`
- [ ] Create WebSocket server for real-time updates
- [ ] Emit events: `execution_started`, `execution_progress`, `execution_completed`
- [ ] Stream console logs during execution
- [ ] Add execution queue (prevent concurrent runs of same test)

#### Frontend Tasks:
- [ ] Install `socket.io-client`
- [ ] Connect to WebSocket server
- [ ] Create real-time execution status component
- [ ] Live log streaming view
- [ ] Progress indicator (% complete)

#### WebSocket Events:
```javascript
// Server -> Client
{
  event: "execution_started",
  data: { test_id: "TC-001", execution_id: 123 }
}

{
  event: "execution_progress", 
  data: { execution_id: 123, step: 3, total: 10, message: "Clicking login button" }
}

{
  event: "execution_completed",
  data: { execution_id: 123, status: "passed", duration: 12.5 }
}
```

#### Deliverables:
✅ Real-time execution updates  
✅ Live log streaming  
✅ Progress tracking

---

### **Phase 4: Batch Execution (Week 4)** 🟠 MEDIUM PRIORITY

**Goal**: Run multiple tests in sequence or parallel

#### Backend Tasks:
- [x] Create `TestSuite` model (group of tests) - **completed**
- [x] Implement sequential execution - **completed**
- [ ] Implement parallel execution - Deferred (Stick to sequential for stability)
- [x] Add `/api/agent/execute-all` endpoint - **completed**
- [x] Create execution summary reports - **completed**

#### Frontend Tasks:
- [x] Add "Run All Tests" button - **completed** (via Run Suite)
- [x] Create "Test Suite" management UI - **completed**
- [x] Show batch execution progress - **completed**
- [x] Display aggregate results (X passed, Y failed) - **completed**

#### Database Schema:
```sql
CREATE TABLE test_suites (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200),
    created_at DATETIME
);

CREATE TABLE suite_tests (
    suite_id INTEGER,
    test_case_id VARCHAR(50),
    execution_order INTEGER
);

CREATE TABLE suite_executions (
    id INTEGER PRIMARY KEY,
    suite_id INTEGER,
    started_at DATETIME,
    completed_at DATETIME,
    total_tests INTEGER,
    passed INTEGER,
    failed INTEGER
);
```

#### Deliverables:
✅ Batch test execution  
✅ Test suite management  
✅ Parallel execution support

---

### **Phase 5: Cross-browser Support (Week 5)** 🟠 MEDIUM PRIORITY

**Goal**: Execute tests on multiple browsers

#### Backend Tasks:
- [ ] Add browser selection parameter
- [ ] Support Chrome, Firefox, Edge
- [ ] Install respective WebDriver managers
- [ ] Add browser-specific configurations
- [ ] Handle browser-specific capabilities

#### Frontend Tasks:
- [ ] Add browser selector dropdown
- [ ] Display browser used in execution results
- [ ] Create browser compatibility matrix

#### Browser Configuration:
```python
SUPPORTED_BROWSERS = {
    'chrome': {
        'driver': 'chromedriver',
        'options': ['--headless', '--no-sandbox']
    },
    'firefox': {
        'driver': 'geckodriver',
        'options': ['-headless']
    },
    'edge': {
        'driver': 'msedgedriver',
        'options': ['--headless']
    }
}
```

#### Deliverables:
✅ Chrome, Firefox, Edge support  
✅ Browser selection UI  
✅ Browser-specific results

---

### **Phase 6: Advanced Features (Week 6+)** 🔵 NICE TO HAVE

**Goal**: Video recording, retry logic, scheduled runs

#### Features:
- [x] **Video Recording**: Record test execution using `opencv-python` - **completed**
- [x] **Retry on Failure**: Auto-retry failed tests (configurable) - **completed**
- [x] **Scheduled Runs**: Cron-like scheduler for periodic testing - **completed**
- [ ] **Email Notifications**: Send results via email - **deferred**
- [ ] **Custom Waits**: Configurable implicit/explicit waits - **deferred**
- [ ] **Test Data Injection**: Pass dynamic data to tests - **deferred**

---

## 🔧 Technical Specifications

### **Required Dependencies**

```txt
# Backend (add to requirements.txt)
selenium==4.16.0
webdriver-manager==4.0.1
python-socketio==5.11.0
aiofiles==23.2.1
opencv-python==4.9.0  # For video recording
pillow==10.2.0         # For screenshot processing
```

### **File Structure**
```
backend/
├── services/
│   ├── execution_service.py      # Core execution logic
│   ├── screenshot_service.py     # Screenshot capture
│   └── video_service.py          # Video recording
├── api/
│   └── execution_api.py          # Execution endpoints
├── models/
│   └── execution_models.py       # DB models
└── websocket/
    └── execution_socket.py       # WebSocket handlers

frontend/
└── src/
    ├── components/
    │   ├── ExecutionButton.jsx
    │   ├── ExecutionResults.jsx
    │   ├── ExecutionHistory.jsx
    │   └── LiveExecutionViewer.jsx
    └── hooks/
        └── useWebSocket.js       # WebSocket connection
```

---

## 📊 Database Schema (Complete)

```sql
-- Test Executions
CREATE TABLE test_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id VARCHAR(50) NOT NULL,
    execution_number INTEGER,  -- Which run (1st, 2nd, etc.)
    status VARCHAR(20) NOT NULL,
    started_at DATETIME NOT NULL,
    completed_at DATETIME,
    duration_seconds FLOAT,
    
    -- Results
    error_message TEXT,
    stack_trace TEXT,
    logs TEXT,
    
    -- Artifacts
    screenshot_path TEXT,
    video_path TEXT,
    
    -- Environment
    browser VARCHAR(20),
    browser_version VARCHAR(50),
    os_info VARCHAR(100),
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (test_case_id) REFERENCES testcases(test_id)
);

-- Test Suites
CREATE TABLE test_suites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Suite Tests (many-to-many)
CREATE TABLE suite_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suite_id INTEGER NOT NULL,
    test_case_id VARCHAR(50) NOT NULL,
    execution_order INTEGER,
    FOREIGN KEY (suite_id) REFERENCES test_suites(id),
    FOREIGN KEY (test_case_id) REFERENCES testcases(test_id)
);

-- Suite Executions
CREATE TABLE suite_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suite_id INTEGER NOT NULL,
    started_at DATETIME NOT NULL,
    completed_at DATETIME,
    total_tests INTEGER,
    passed INTEGER,
    failed INTEGER,
    skipped INTEGER,
    FOREIGN KEY (suite_id) REFERENCES test_suites(id)
);
```

---

## 🌐 API Endpoints (New)

### **Execution Endpoints**

```python
# Execute single test
POST /api/agent/execute/{test_id}
Body: {
    "browser": "chrome",  # optional, default: chrome
    "headless": true,     # optional, default: true
    "timeout": 30         # optional, default: 30
}
Response: {
    "execution_id": 123,
    "status": "running",
    "started_at": "2026-02-10T11:40:00Z"
}

# Get execution status
GET /api/agent/executions/{execution_id}
Response: {
    "id": 123,
    "test_case_id": "TC-001",
    "status": "passed",
    "duration": 12.5,
    "screenshot_path": "/results/TC-001/screenshot.png",
    "logs": "...",
    "started_at": "...",
    "completed_at": "..."
}

# Get execution history for a test
GET /api/agent/testcases/{test_id}/executions
Response: {
    "executions": [
        { "id": 123, "status": "passed", ... },
        { "id": 122, "status": "failed", ... }
    ],
    "total_runs": 10,
    "success_rate": 0.8
}

# Get screenshot
GET /api/agent/executions/{execution_id}/screenshot
Response: Binary image data

# Execute test suite
POST /api/agent/suites/{suite_id}/execute
Body: {
    "parallel": false,  # run in parallel?
    "browser": "chrome"
}
Response: {
    "suite_execution_id": 456,
    "status": "running"
}

# Stop running execution
POST /api/agent/executions/{execution_id}/stop
Response: {
    "status": "stopped"
}
```

---

## 🎨 UI/UX Design

### **Test Card Updates**
```
┌─────────────────────────────────────────────────┐
│ TC-001: Login Validation                        │
│ Feature: Authentication                         │
├─────────────────────────────────────────────────┤
│ Last Run: 2 hours ago - ✅ PASSED               │
│ Success Rate: 8/10 (80%)                        │
├─────────────────────────────────────────────────┤
│ [▶️ Run Test] [📊 History] [📋 View Details]    │
└─────────────────────────────────────────────────┘
```

### **Live Execution View**
```
┌─────────────────────────────────────────────────┐
│ 🔄 Executing TC-001: Login Validation           │
├─────────────────────────────────────────────────┤
│ Progress: [████████░░] 80% (Step 8/10)          │
├─────────────────────────────────────────────────┤
│ Live Logs:                                      │
│ ✓ Opening browser...                           │
│ ✓ Navigating to login page...                  │
│ ✓ Entering credentials...                      │
│ ⏳ Clicking submit button...                    │
├─────────────────────────────────────────────────┤
│ Duration: 12.3s                                 │
│ Browser: Chrome 120.0                           │
└─────────────────────────────────────────────────┘
```

### **Execution History**
```
┌─────────────────────────────────────────────────┐
│ Execution History - TC-001                      │
├─────────────────────────────────────────────────┤
│ #10  2h ago   ✅ PASSED  12.5s  [View] [📷]    │
│ #9   5h ago   ❌ FAILED  8.2s   [View] [📷]    │
│ #8   1d ago   ✅ PASSED  11.8s  [View] [📷]    │
│ #7   1d ago   ✅ PASSED  13.1s  [View] [📷]    │
└─────────────────────────────────────────────────┘
```

---

## ⚠️ Important Considerations

### **Security**
- ❗ Sanitize all script inputs before execution
- ❗ Run scripts in sandboxed environment
- ❗ Limit execution time (timeout)
- ❗ Prevent arbitrary code execution

### **Performance**
- ❗ Use headless browsers by default
- ❗ Implement execution queue to prevent overload
- ❗ Clean up old screenshots/videos periodically
- ❗ Limit concurrent executions

### **Error Handling**
- ❗ Gracefully handle browser crashes
- ❗ Timeout management
- ❗ Resource cleanup on failure
- ❗ Clear error messages to users

---

## 📈 Success Metrics

### Phase 1 Success:
- ✅ 100% of generated scripts are executable
- ✅ Execution results saved correctly
- ✅ UI updates reflect execution status

### Phase 3 Success:
- ✅ Real-time updates < 500ms latency
- ✅ No execution data loss
- ✅ Stable WebSocket connections

### Phase 6 Success:
- ✅ Support 3+ browsers
- ✅ Video recording works reliably
- ✅ Scheduled runs execute on time

---

## 🚀 Quick Start (After Phase 1)

1. **Generate a test case**
2. **Click "Run Test" button**
3. **Watch execution status update**
4. **View results with screenshots**

---

## 📝 Notes

- Start with **headless mode** for faster execution
- Store execution artifacts for **7 days** by default
- Implement **retry logic** (3 attempts) for flaky tests
- Add **execution timeout** (default: 60 seconds)

---

**Last Updated**: 2026-02-10  
**Version**: 1.0  
**Status**: Ready for Implementation
