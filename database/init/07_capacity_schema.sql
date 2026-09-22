CREATE TABLE IF NOT EXISTS capacity_measurements (
    id BIGSERIAL PRIMARY KEY,

    observed_at TIMESTAMPTZ NOT NULL,

    environment VARCHAR(50) NOT NULL,

    source VARCHAR(50) NOT NULL,

    target VARCHAR(255) NOT NULL,

    resource VARCHAR(255) NOT NULL DEFAULT '',

    metric VARCHAR(100) NOT NULL,

    value NUMERIC(20, 6) NOT NULL,

    unit VARCHAR(30) NOT NULL,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE UNIQUE INDEX IF NOT EXISTS
    ux_capacity_measurements_identity
ON capacity_measurements (
    environment,
    source,
    target,
    resource,
    metric,
    unit,
    observed_at
);


CREATE INDEX IF NOT EXISTS
    ix_capacity_measurements_lookup
ON capacity_measurements (
    environment,
    source,
    target,
    resource,
    metric,
    observed_at DESC
);


CREATE INDEX IF NOT EXISTS
    ix_capacity_measurements_observed_at
ON capacity_measurements (
    observed_at DESC
);
