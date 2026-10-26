BEGIN;

CREATE TABLE conversation_feedback (
    id uuid PRIMARY KEY,
    chatbot_id uuid NOT NULL REFERENCES chatbots (id) ON DELETE CASCADE,
    conversation_id uuid NOT NULL UNIQUE,
    offered_at timestamptz NOT NULL DEFAULT now(),
    submitted_at timestamptz,
    satisfaction_score smallint,
    resolution text,
    clarity_score smallint,
    comment text,
    CONSTRAINT feedback_satisfaction_check CHECK (satisfaction_score BETWEEN 1 AND 5),
    CONSTRAINT feedback_clarity_check CHECK (clarity_score BETWEEN 1 AND 5),
    CONSTRAINT feedback_resolution_check CHECK (resolution IN ('yes', 'partial', 'no')),
    CONSTRAINT feedback_comment_length_check CHECK (length(comment) <= 1000),
    CONSTRAINT feedback_submission_check CHECK (
        (submitted_at IS NULL AND satisfaction_score IS NULL AND resolution IS NULL
            AND clarity_score IS NULL AND comment IS NULL)
        OR (submitted_at IS NOT NULL AND satisfaction_score IS NOT NULL
            AND submitted_at >= offered_at)
    )
);

CREATE INDEX conversation_feedback_chatbot_offered_idx
    ON conversation_feedback (chatbot_id, offered_at);
CREATE INDEX conversation_feedback_comment_retention_idx
    ON conversation_feedback (submitted_at) WHERE comment IS NOT NULL;

COMMIT;
