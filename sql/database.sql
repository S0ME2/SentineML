-- Fresh-install-only schema. Refuse existing objects; never reset user data.
BEGIN;

CREATE TYPE run_status AS ENUM (
    'waiting',
    'running',
    'completed',
    'failed',
    'cancelled'
);


CREATE TABLE projects (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT
);


CREATE TABLE datasets (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(255) NOT NULL,
    description TEXT,
    dataset_hash VARCHAR(255),
    source TEXT,
    metadata TEXT,

    CONSTRAINT uq_datasets_name_version UNIQUE (name, version)
);


CREATE TABLE models (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(255) NOT NULL,
    description TEXT,
    model_type VARCHAR(255),
    metadata TEXT,

    CONSTRAINT uq_models_name_version UNIQUE (name, version)
);


CREATE TABLE metric_directions (
    name VARCHAR(255) PRIMARY KEY,
    maximize BOOLEAN NOT NULL
);


CREATE TABLE runs (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id INTEGER NOT NULL,
    dataset_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,

    status run_status NOT NULL DEFAULT 'waiting',

    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,

    notes TEXT,

    is_ignored BOOLEAN NOT NULL DEFAULT FALSE,
    ignore_reason TEXT,
    reason TEXT,

    CONSTRAINT fk_runs_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,

    CONSTRAINT fk_runs_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES datasets(id)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,

    CONSTRAINT fk_runs_model
        FOREIGN KEY (model_id)
        REFERENCES models(id)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION
);


CREATE TABLE parameters (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    value VARCHAR(255) NOT NULL,
    value_type VARCHAR(100),
    notes TEXT,

    CONSTRAINT fk_parameters_run
        FOREIGN KEY (run_id)
        REFERENCES runs(id)
        ON DELETE CASCADE
        ON UPDATE NO ACTION,

    CONSTRAINT uq_parameters_run_name UNIQUE (run_id, name)
);


CREATE TABLE metrics (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    notes TEXT,

    CONSTRAINT fk_metrics_run
        FOREIGN KEY (run_id)
        REFERENCES runs(id)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,

    CONSTRAINT fk_metrics_direction
        FOREIGN KEY (name)
        REFERENCES metric_directions(name)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,

    CONSTRAINT uq_metrics_run_name UNIQUE (run_id, name)
);

-- Existing unique (run_id, name) indexes cover parameter/metric run lookups.
CREATE INDEX ix_runs_project_id ON runs (project_id);
CREATE INDEX ix_runs_dataset_id ON runs (dataset_id);
CREATE INDEX ix_runs_model_id ON runs (model_id);
CREATE INDEX ix_runs_rankable_project ON runs (project_id, id)
    WHERE status = 'completed' AND is_ignored IS FALSE;
CREATE INDEX ix_metrics_name_value_run ON metrics (name, value, run_id);

COMMIT;
