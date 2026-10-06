CREATE TABLE login_attempts (
    key text PRIMARY KEY,
    failed_attempts integer NOT NULL DEFAULT 0 CHECK (failed_attempts >= 0),
    window_started_at timestamptz NOT NULL
);
