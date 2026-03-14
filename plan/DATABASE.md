# Database Integration - QA Agent

## Overview
The QA Agent now persists all generated test cases and Selenium scripts to a SQLite database, ensuring data is preserved across sessions.

## Database Schema

### Test Cases Table (`testcases`)
- `id`: Auto-incrementing primary key
- `test_id`: Unique identifier (e.g., TC-001)
- `feature`: Feature being tested
- `scenario`: Test scenario description
- `preconditions`: Required preconditions
- `steps`: JSON array of test steps
- `test_data`: JSON object of test data
- `expected_result`: Expected outcome
- `grounded_in`: JSON array of documentation references
- `created_at`: Timestamp of creation

### Selenium Scripts Table (`selenium_scripts`)
- `id`: Auto-incrementing primary key
- `test_case_id`: Reference to test case
- `script_content`: Python/Selenium script code
- `created_at`: Timestamp of creation

## Features

### Automatic Persistence
- **Test Cases**: Automatically saved when generated (both manual and "Generate All")
- **Scripts**: Automatically saved when created for a test case
- **Deduplication**: Test cases with same `test_id` are updated instead of duplicated

### Data Retrieval
- **Load on Startup**: Frontend automatically loads all saved test cases when app starts
- **Persistent Scripts**: Generated scripts are stored and can be retrieved later

## API Endpoints

### Test Cases
- `POST /api/agent/testcases` - Generate and save new test cases
- `GET /api/agent/testcases` - Retrieve all saved test cases
- `DELETE /api/agent/testcases/{test_id}` - Delete a specific test case

### Scripts
- `POST /api/agent/selenium-script` - Generate and save a script
- `GET /api/agent/selenium-scripts` - Retrieve all scripts
- `GET /api/agent/selenium-scripts/{test_case_id}` - Get script for specific test case

## Database Location
- **File**: `qa_agent.db` (SQLite database in project root)
- **Backup**: You can copy this file to backup all test data

## Benefits
1. **Session Persistence**: Test cases survive application restarts
2. **History Tracking**: Keep track of all generated test cases with timestamps
3. **Script Versioning**: Multiple script versions per test case can be maintained
4. **Easy Export**: SQLite database can be easily exported or migrated
5. **No Setup Required**: SQLite requires no separate database server

## Migration Notes
- Database is created automatically on first run
- Existing test cases in memory are not auto-migrated (regenerate to save)
- Database schema is version-controlled through SQLAlchemy models
