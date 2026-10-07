BEGIN;

ALTER TABLE chatbots
    ADD COLUMN widget_settings json NOT NULL DEFAULT '{"primary_color":"#14a8ce","icon":"bot","welcome_message":"Hola, ¿en qué puedo ayudarte con este dashboard?"}';

COMMIT;
