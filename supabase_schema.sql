-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================================
-- 1. PROFILES TABLE (extends auth.users)
-- ================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================================
-- 2. PROJECTS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    chroma_collection_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- ================================================================
-- 3. TEST CASES TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS public.testcases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    test_id TEXT NOT NULL,
    feature TEXT,
    scenario TEXT,
    preconditions TEXT,
    steps JSONB,
    test_data JSONB,
    expected_result TEXT,
    grounded_in JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, test_id)
);

-- ================================================================
-- 4. SELENIUM SCRIPTS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS public.selenium_scripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    test_case_id TEXT,
    script_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================================
-- 5. KNOWLEDGE BASE FILES TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS public.kb_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT CHECK (file_type IN ('document', 'html')),
    file_hash TEXT NOT NULL,
    file_size INTEGER,
    storage_path TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, file_hash)
);

-- ================================================================
-- 6. DOCUMENT CHUNKS TABLE (for deduplication)
-- ================================================================
CREATE TABLE IF NOT EXISTS public.document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    kb_file_id UUID REFERENCES public.kb_files(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_hash TEXT NOT NULL,
    chunk_index INTEGER,
    metadata JSONB,
    embedding_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, chunk_hash)
);

-- ================================================================
-- 7. TEST SUITES TABLE (Added from Phase 4)
-- ================================================================
CREATE TABLE IF NOT EXISTS public.test_suites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================================
-- 8. SUITE TEXT MAPPING TABLE (Added from Phase 4)
-- ================================================================
CREATE TABLE IF NOT EXISTS public.suite_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    suite_id UUID NOT NULL REFERENCES public.test_suites(id) ON DELETE CASCADE,
    test_case_id TEXT NOT NULL, -- Logical ID like TC-001
    execution_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================================
-- 9. BATCH RUNS TABLE (Added from Phase 4)
-- ================================================================
CREATE TABLE IF NOT EXISTS public.batch_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    suite_id UUID REFERENCES public.test_suites(id) ON DELETE SET NULL,
    name TEXT, -- "Run #5" or "Nightly Build"
    status TEXT CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    total_tests INTEGER DEFAULT 0,
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    error_tests INTEGER DEFAULT 0,
    total_duration_seconds FLOAT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================================
-- 10. TEST EXECUTIONS TABLE
-- ================================================================
CREATE TABLE IF NOT EXISTS public.test_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    test_case_id TEXT NOT NULL,
    status TEXT CHECK (status IN ('pending', 'running', 'passed', 'failed', 'error')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT,
    error_message TEXT,
    logs TEXT,
    screenshot_path TEXT,
    video_path TEXT, -- Added from Phase 6
    batch_run_id UUID REFERENCES public.batch_runs(id) ON DELETE SET NULL, -- Added from Phase 4
    browser TEXT,
    browser_version TEXT,
    os_info TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_executions_project_id ON public.test_executions(project_id);
CREATE INDEX IF NOT EXISTS idx_executions_test_case_id ON public.test_executions(test_case_id);

-- ================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- ================================================================
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_active ON public.projects(is_active);
CREATE INDEX IF NOT EXISTS idx_testcases_project_id ON public.testcases(project_id);
CREATE INDEX IF NOT EXISTS idx_scripts_project_id ON public.selenium_scripts(project_id);
CREATE INDEX IF NOT EXISTS idx_kb_files_project_id ON public.kb_files(project_id);
CREATE INDEX IF NOT EXISTS idx_kb_files_hash ON public.kb_files(file_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_project_id ON public.document_chunks(project_id);
CREATE INDEX IF NOT EXISTS idx_chunks_hash ON public.document_chunks(chunk_hash);

-- ================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ================================================================

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.testcases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.selenium_scripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kb_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.test_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.test_suites ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.suite_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.batch_runs ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON public.profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- Projects policies
CREATE POLICY "Users can view own projects" ON public.projects FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create projects" ON public.projects FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own projects" ON public.projects FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own projects" ON public.projects FOR DELETE USING (auth.uid() = user_id);

-- Test cases policies
CREATE POLICY "Users can view test cases in their projects" ON public.testcases FOR SELECT USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can create test cases in their projects" ON public.testcases FOR INSERT WITH CHECK (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can update test cases in their projects" ON public.testcases FOR UPDATE USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can delete test cases in their projects" ON public.testcases FOR DELETE USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));

-- Selenium scripts policies
CREATE POLICY "Users can view scripts in their projects" ON public.selenium_scripts FOR SELECT USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can create scripts in their projects" ON public.selenium_scripts FOR INSERT WITH CHECK (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can update scripts in their projects" ON public.selenium_scripts FOR UPDATE USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can delete scripts in their projects" ON public.selenium_scripts FOR DELETE USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));

-- KB files policies
CREATE POLICY "Users can view files in their projects" ON public.kb_files FOR SELECT USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can upload files to their projects" ON public.kb_files FOR INSERT WITH CHECK (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can delete files in their projects" ON public.kb_files FOR DELETE USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));

-- Document chunks policies
CREATE POLICY "Users can view chunks in their projects" ON public.document_chunks FOR SELECT USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can create chunks in their projects" ON public.document_chunks FOR INSERT WITH CHECK (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can delete chunks in their projects" ON public.document_chunks FOR DELETE USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));

-- Test Executions Policies
CREATE POLICY "Users can view executions in their projects" ON public.test_executions FOR SELECT USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can create executions in their projects" ON public.test_executions FOR INSERT WITH CHECK (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can update executions in their projects" ON public.test_executions FOR UPDATE USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can delete executions in their projects" ON public.test_executions FOR DELETE USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));

-- Test Suites Policies
CREATE POLICY "Users can view suites in their projects" ON public.test_suites FOR SELECT USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can create suites in their projects" ON public.test_suites FOR INSERT WITH CHECK (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can update suites in their projects" ON public.test_suites FOR UPDATE USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can delete suites in their projects" ON public.test_suites FOR DELETE USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));

-- Suite Tests Policies
CREATE POLICY "Users can view suite tests" ON public.suite_tests FOR SELECT USING (suite_id IN (SELECT id FROM public.test_suites WHERE project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid())));
CREATE POLICY "Users can manage suite tests" ON public.suite_tests FOR ALL USING (suite_id IN (SELECT id FROM public.test_suites WHERE project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid())));

-- Batch Runs Policies
CREATE POLICY "Users can view batch runs in their projects" ON public.batch_runs FOR SELECT USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can create batch runs in their projects" ON public.batch_runs FOR INSERT WITH CHECK (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));
CREATE POLICY "Users can update batch runs in their projects" ON public.batch_runs FOR UPDATE USING (project_id IN (SELECT id FROM public.projects WHERE user_id = auth.uid()));

-- ================================================================
-- HELPER FUNCTIONS
-- ================================================================

-- Function to create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create profile
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for projects
DROP TRIGGER IF EXISTS set_projects_updated_at ON public.projects;
CREATE TRIGGER set_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Trigger for profiles
DROP TRIGGER IF EXISTS set_profiles_updated_at ON public.profiles;
CREATE TRIGGER set_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
