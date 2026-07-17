CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    namespace STRING NOT NULL,
    resource_name STRING NOT NULL,
    resource_kind STRING NOT NULL,
    issue_type STRING NOT NULL,
    description STRING NOT NULL,
    raw_details JSONB,
    embedding VECTOR(1024),
    suggested_fix STRING,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_incidents_namespace_issue ON incidents (namespace, issue_type);

CREATE VECTOR INDEX IF NOT EXISTS idx_incidents_embedding ON incidents (embedding);