CREATE TABLE chatbot_documents (
    chatbot_id uuid NOT NULL REFERENCES chatbots (id) ON DELETE CASCADE,
    document_id uuid NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    PRIMARY KEY (chatbot_id, document_id)
);

INSERT INTO chatbot_documents (chatbot_id, document_id)
SELECT chatbot_id, id FROM documents
ON CONFLICT DO NOTHING;

CREATE INDEX chatbot_documents_document_id_idx ON chatbot_documents (document_id);
