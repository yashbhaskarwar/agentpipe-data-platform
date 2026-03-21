CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              SERIAL PRIMARY KEY,
    pipeline_name   VARCHAR(100) NOT NULL,
    status          VARCHAR(20)  NOT NULL CHECK (status IN ('success', 'failed', 'running')),
    start_time      TIMESTAMP    NOT NULL,
    end_time        TIMESTAMP,                    
    rows_processed  INTEGER,
    error_message   TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_name    ON pipeline_runs (pipeline_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status  ON pipeline_runs (status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_start   ON pipeline_runs (start_time DESC);

-- Individual task steps within a run
CREATE TABLE IF NOT EXISTS pipeline_tasks (
    id               SERIAL PRIMARY KEY,
    run_id           INTEGER      NOT NULL REFERENCES pipeline_runs (id) ON DELETE CASCADE,
    task_name        VARCHAR(100) NOT NULL,
    status           VARCHAR(20)  NOT NULL CHECK (status IN ('success', 'failed', 'skipped')),
    duration_seconds NUMERIC(8,2),
    error_message    TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_tasks_run_id ON pipeline_tasks (run_id);

-- Data quality check results
CREATE TABLE IF NOT EXISTS data_quality_checks (
    id         SERIAL PRIMARY KEY,
    run_id     INTEGER      NOT NULL REFERENCES pipeline_runs (id) ON DELETE CASCADE,
    check_name VARCHAR(150) NOT NULL,
    passed     BOOLEAN      NOT NULL,
    details    TEXT,
    checked_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dq_checks_run_id    ON data_quality_checks (run_id);
CREATE INDEX IF NOT EXISTS idx_dq_checks_passed    ON data_quality_checks (passed);
CREATE INDEX IF NOT EXISTS idx_dq_checks_checked_at ON data_quality_checks (checked_at DESC);
