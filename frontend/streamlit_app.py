import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="QA Agent", layout="wide", page_icon="🤖")

# Custom CSS for professional styling
st.markdown("""
<style>
/* Main button styling */
div.stButton > button {
    width: 100%;
    border-radius: 8px;
    height: 3em;
    font-weight: 500;
    transition: all 0.3s ease;
}

/* Sidebar navigation styling */
[data-testid="stSidebar"] {
    background-color: var(--background-color);
}

/* Navigation button container */
.nav-button {
    margin-bottom: 8px;
}

/* Custom navigation button styling */
.stButton > button[kind="secondary"] {
    background-color: transparent;
    border: 1px solid rgba(128, 128, 128, 0.2);
    color: var(--text-color);
    text-align: left;
    padding-left: 1rem;
    font-size: 1rem;
    transition: all 0.2s ease;
}

.stButton > button[kind="secondary"]:hover {
    background-color: rgba(128, 128, 128, 0.1);
    border-color: rgba(128, 128, 128, 0.3);
    transform: translateX(2px);
}

/* Active navigation button */
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #1f77b4 0%, #2a9fd6 100%);
    color: white;
    border: none;
    text-align: left;
    padding-left: 1rem;
    font-size: 1rem;
    font-weight: 600;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(90deg, #1a6ca8 0%, #2589c2 100%);
    box-shadow: 0 3px 6px rgba(0,0,0,0.15);
}

/* Expander styling for side-by-side layout */
.streamlit-expanderHeader {
    font-weight: 600;
}

/* Metrics styling */
[data-testid="stMetricValue"] {
    font-size: 1.5rem;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ---------------------- SESSION STATE ----------------------
if "uploaded_docs" not in st.session_state:
    st.session_state["uploaded_docs"] = []
if "uploaded_html" not in st.session_state:
    st.session_state["uploaded_html"] = []
if "full_testcases" not in st.session_state:
    st.session_state["full_testcases"] = {}
if "selected_test" not in st.session_state:
    st.session_state["selected_test"] = None
if "nav_selection" not in st.session_state:
    st.session_state["nav_selection"] = "Knowledge Base"

# ---------------------- SIDEBAR NAV ----------------------
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    st.markdown("")
    
    # Navigation buttons with active state
    current_page = st.session_state["nav_selection"]
    
    # Knowledge Base button
    kb_type = "primary" if current_page == "Knowledge Base" else "secondary"
    if st.button("📚 Knowledge Base", key="nav_kb", type=kb_type, help="Upload and manage project files", width="stretch"):
        st.session_state["nav_selection"] = "Knowledge Base"
        st.rerun()
    
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    
    # Test Cases button
    tc_type = "primary" if current_page == "Test Cases" else "secondary"
    if st.button("🧪 Test Cases", key="nav_tc", type=tc_type, help="Generate and view test cases", width="stretch"):
        st.session_state["nav_selection"] = "Test Cases"
        st.rerun()
    
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    
    # Selenium Scripts button
    sel_type = "primary" if current_page == "Selenium Scripts" else "secondary"
    if st.button("💻 Selenium Scripts", key="nav_sel", type=sel_type, help="Generate automation scripts", width="stretch"):
        st.session_state["nav_selection"] = "Selenium Scripts"
        st.rerun()
    
    st.markdown("---")
    
    # Progress Dashboard
    st.markdown("### 📊 Progress Status")
    
    # Fetch real-time status from backend
    try:
        status = requests.get(f"{BACKEND_URL}/kb/status", timeout=2).json()
        doc_count = status.get("doc_count", 0)
        html_count = len(status.get("html_files", []))
        embedding_count = status.get("embedding_count", 0)
    except:
        doc_count = 0
        html_count = 0
        embedding_count = 0
    
    test_count = len(st.session_state["full_testcases"])
    
    st.metric("Documents", doc_count)
    st.metric("HTML Files", html_count)
    st.metric("Embeddings", embedding_count)
    st.metric("Test Cases", test_count)
    
    # Workflow progress indicator
    st.markdown("---")
    st.markdown("### 🎯 Workflow")
    step1 = "✅" if doc_count > 0 or html_count > 0 else "⬜"
    step2 = "✅" if test_count > 0 else "⬜"
    step3 = "✅" if st.session_state.get("selected_test") else "⬜"
    
    st.markdown(f"""
    {step1} **Step 1:** Upload Files  
    {step2} **Step 2:** Generate Test Cases  
    {step3} **Step 3:** Generate Scripts
    """)

menu = st.session_state["nav_selection"]

# ---------------------- MAIN HEADER ----------------------
st.title("🤖 QA Agent")
st.markdown("*Autonomous Test Case & Selenium Script Generator*")
st.markdown("---")

# ==========================================================
# --------------------- KNOWLEDGE BASE ---------------------
# ==========================================================
if menu == "Knowledge Base":
    st.header("📚 Knowledge Base")
    st.caption("Upload project files, build context, and reset if testing a new application.")
    st.markdown("")

    # ---- Two Column Layout ----
    col_left, col_right = st.columns(2)

    # -------------------- Left Panel --------------------
    with col_left:
        with st.expander("📄 Upload Requirements Documents", expanded=True):
            st.write("Upload project documentation (PDF, TXT, MD, JSON)")
            docs = st.file_uploader(
                "Select files:",
                accept_multiple_files=True,
                key="docs_uploader",
                help="Supported formats: .txt, .md, .pdf, .json"
            )

            if st.button("📤 Upload Documents", key="btn_upload_docs", type="primary"):
                if docs:
                    with st.spinner("Uploading documents..."):
                        for f in docs:
                            requests.post(
                                f"{BACKEND_URL}/kb/docs/upload",
                                files={"file": (f.name, f.read(), f.type)}
                            )
                    st.success(f"✅ Uploaded {len(docs)} document(s)")
                    st.rerun()
                else:
                    st.warning("Please select files first")


    # -------------------- Right Panel --------------------
    with col_right:
        with st.expander("🌐 Upload Application HTML", expanded=True):
            st.write("Upload the app's main HTML UI file")
            html_file = st.file_uploader(
                "Select HTML file:",
                type=["html", "htm"],
                key="html_uploader",
                help="Upload checkout.html or UI template"
            )

            if st.button("📤 Upload HTML", key="btn_upload_html", type="primary"):
                if html_file:
                    with st.spinner("Uploading HTML..."):
                        requests.post(
                            f"{BACKEND_URL}/kb/html/upload",
                            files={"file": (html_file.name, html_file.read(), html_file.type)}
                        )

                    st.success("✅ HTML uploaded successfully")
                    st.rerun()
                else:
                    st.warning("Please select an HTML file first")

    st.markdown("---")

    
    # Display uploaded files in tables
    st.subheader("📂 Uploaded Files")
    
    try:
        status = requests.get(f"{BACKEND_URL}/kb/status").json()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 Documents**")
            doc_files = status.get("doc_files", [])
            if doc_files:
                df_docs = pd.DataFrame({"Filename": doc_files})
                st.dataframe(df_docs, width="stretch", hide_index=True)
            else:
                st.info("No documents uploaded yet")
        
        with col2:
            st.markdown("**🌐 HTML Files**")
            html_files = status.get("html_files", [])
            if html_files:
                df_html = pd.DataFrame({"Filename": html_files})
                st.dataframe(df_html, width="stretch", hide_index=True)
            else:
                st.info("No HTML files uploaded yet")
    except:
        st.error("Could not fetch status from backend")
    
    st.markdown("---")
    
    # Action buttons
    st.subheader("⚙️ Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔨 Build Knowledge Base", type="primary", key="btn_build_kb", width="stretch"):
            with st.spinner("Building Knowledge Base..."):
                resp = requests.get(f"{BACKEND_URL}/kb/build")
                if resp.status_code == 200:
                    st.success("✅ Knowledge Base built successfully!")
                else:
                    st.error("❌ Failed to build Knowledge Base")
    
    with col2:
        if st.button("🗑️ Reset Knowledge Base", type="secondary", key="btn_reset_kb", width="stretch"):
            if st.session_state.get("confirm_reset"):
                with st.spinner("Resetting..."):
                    requests.post(f"{BACKEND_URL}/kb/reset")
                    st.session_state["full_testcases"] = {}
                    st.session_state["selected_test"] = None
                    st.session_state["confirm_reset"] = False
                st.success("✅ Knowledge Base reset successfully")
                st.rerun()
            else:
                st.session_state["confirm_reset"] = True
                st.warning("⚠️ Click Reset again to confirm")

# ==========================================================
# --------------------- TEST CASES -------------------------
# ==========================================================
elif menu == "Test Cases":
    st.header("🧪 Test Case Generation")
    st.caption("Generate comprehensive test cases based on your Knowledge Base.")
    st.markdown("")
    
    # Generation controls
    with st.expander("🎯 Generate Test Cases", expanded=True):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            auto_gen = st.button("✨ Auto-Generate All", key="btn_auto_gen", type="primary", width="stretch")
        
        with col2:
            manual_query = st.text_input(
                "Or enter specific requirement:",
                placeholder="e.g., Test the discount code feature",
                help="Describe what you want to test"
            )
            manual_gen = st.button("🔍 Generate from Query", key="btn_manual_gen", width="stretch")
        
        if auto_gen or (manual_gen and manual_query):
            query = manual_query if manual_gen and manual_query else "Generate comprehensive positive and negative test cases for the entire application described in the documentation."
            
            with st.spinner("🤖 Generating test cases... This may take a moment."):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/agent/testcases",
                        json={"query": query}
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        
                        # Check if there's an error message (e.g., empty KB)
                        if data.get("error"):
                            st.error(f"❌ {data['error']}")
                            if data.get("empty_kb"):
                                st.info("💡 **Tip:** Go to the **Knowledge Base** tab and upload documents, then click **Build Knowledge Base**.")
                        elif isinstance(data.get("testcases"), list):
                            st.session_state["full_testcases"] = {tc["test_id"]: tc for tc in data["testcases"]}
                            st.success(f"✅ Generated {len(data['testcases'])} test cases successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Model returned invalid JSON structure")
                            st.write(data)
                    else:
                        st.error(f"❌ Backend Error ({resp.status_code})")
                        try:
                            error_data = resp.json()
                            if error_data.get("detail"):
                                st.error(error_data["detail"])
                        except:
                            st.text(resp.text)
                except Exception as e:
                    st.error(f"❌ Request Failed: {e}")
    
    st.markdown("---")
    
    # Display test cases
    if st.session_state["full_testcases"]:
        st.subheader(f"📋 Test Cases ({len(st.session_state['full_testcases'])})")
        
        # Search and filter
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 Search test cases:", placeholder="Search by ID, feature, or scenario...")
        
        # Filter test cases
        test_ids = list(st.session_state["full_testcases"].keys())
        filtered_ids = test_ids
        
        if search_query:
            filtered_ids = [
                tid for tid in test_ids
                if search_query.lower() in tid.lower() 
                or search_query.lower() in st.session_state["full_testcases"][tid].get("feature", "").lower()
                or search_query.lower() in st.session_state["full_testcases"][tid].get("scenario", "").lower()
            ]
        
        st.write(f"Showing {len(filtered_ids)} of {len(test_ids)} test cases")
        
        st.markdown("")
        
        # Test case selector
        if filtered_ids:
            def format_test_option(test_id):
                tc = st.session_state["full_testcases"].get(test_id, {})
                return f"{test_id}: {tc.get('scenario', 'No scenario')}"
            
            selected = st.selectbox(
                "Select test case to view or generate script:",
                filtered_ids,
                format_func=format_test_option,
                key="tc_select"
            )
            st.session_state["selected_test"] = selected
            
            # Show details
            tc = st.session_state["full_testcases"][selected]
            
            with st.expander("📖 View Test Case Details", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Test ID:** `{tc.get('test_id')}`")
                    st.markdown(f"**Feature:** {tc.get('feature')}")
                    st.markdown(f"**Scenario:** {tc.get('scenario')}")
                
                with col2:
                    st.markdown(f"**Expected Result:**")
                    st.info(tc.get('expected_result'))
                
                st.markdown("**Full Details:**")
                st.json(tc)
            
            st.markdown("")
            st.info("💡 **Tip:** Go to the **Selenium Scripts** tab to generate automation code for this test case.")
        else:
            st.warning("No test cases match your search")
    else:
        st.info("👆 Generate test cases to get started")

# ==========================================================
# ----------------- SELENIUM SCRIPT PAGE -------------------
# ==========================================================
elif menu == "Selenium Scripts":
    st.header("💻 Selenium Script Generator")
    st.caption("Generate executable Python Selenium scripts from your test cases.")
    st.markdown("")
    
    # Check if test cases exist
    if not st.session_state["full_testcases"]:
        st.warning("⚠️ Please generate test cases first from the 'Test Cases' tab.")
        st.stop()
    
    # Test case selector
    st.subheader("📋 Select Test Case")
    test_ids = list(st.session_state["full_testcases"].keys())
    
    def format_test_option(test_id):
        tc = st.session_state["full_testcases"].get(test_id, {})
        return f"{test_id}: {tc.get('scenario', 'No scenario')}"
    
    selected = st.selectbox(
        "Choose a test case to generate Selenium script:",
        test_ids,
        format_func=format_test_option,
        key="selenium_tc_select"
    )
    
    st.session_state["selected_test"] = selected
    
    # Show test case details
    tc = st.session_state["full_testcases"][selected]
    
    with st.expander("📖 Test Case Details"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Feature:** {tc.get('feature')}")
            st.markdown(f"**Scenario:** {tc.get('scenario')}")
        with col2:
            st.markdown(f"**Expected Result:**")
            st.info(tc.get('expected_result'))
    
    st.markdown("---")
    
    # Generate button
    if st.button("🚀 Generate Selenium Script", type="primary", key="btn_gen_selenium_exec", width="stretch"):
        with st.spinner("🤖 Generating Selenium script... This may take a moment."):
            response = requests.post(
                f"{BACKEND_URL}/agent/selenium-script",
                json={"testcase": tc}
            )
            
            if response.status_code == 200:
                script = response.json()["script"]
                st.session_state["generated_script"] = script
                st.session_state["script_test_id"] = selected
                st.success("✅ Script generated successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to generate script. Check backend logs.")
                st.text(response.text)
    
    # Display generated script
    if st.session_state.get("generated_script") and st.session_state.get("script_test_id") == selected:
        st.markdown("---")
        st.subheader("📝 Generated Script")
        
        script = st.session_state["generated_script"]
        
        # Code display
        st.code(script, language="python")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="💾 Download Script",
                data=script,
                file_name=f"{selected}.py",
                mime="text/plain",
                key="download_script",
                width="stretch",
                type="primary"
            )
        
        with col2:
            if st.button("🔄 Regenerate", key="btn_regenerate", width="stretch"):
                st.session_state["generated_script"] = None
                st.rerun()

# ---------------------- FOOTER ----------------------
st.markdown("---")

# Backend health check
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=2)
    if response.status_code == 200:
        st.caption("🟢 Backend Connected")
    else:
        st.caption("🟡 Backend reachable but not healthy")
except Exception:
    st.caption("🔴 Backend not reachable")
