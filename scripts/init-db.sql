
-- CoFound.ai Database Initialization Script

-- Create tables for projects
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create tables for dreams/requests
CREATE TABLE IF NOT EXISTS dreams (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(255) REFERENCES projects(project_id),
    prompt_text TEXT NOT NULL,
    vision TEXT,
    objectives JSONB,
    tech_stack TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create tables for agent interactions
CREATE TABLE IF NOT EXISTS agent_interactions (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(255) REFERENCES projects(project_id),
    agent_name VARCHAR(100) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(50) DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_dreams_project_id ON dreams(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_interactions_project_id ON agent_interactions(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_interactions_agent_name ON agent_interactions(agent_name);

-- Insert sample data
INSERT INTO projects (project_id, user_id, name, description) 
VALUES ('sample-project', 'local-user', 'Sample Project', 'A sample project for testing CoFound.ai')
ON CONFLICT (project_id) DO NOTHING;
