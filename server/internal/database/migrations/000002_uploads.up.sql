-- Files uploaded ahead of submitting a claim form, so the form submits
-- instantly. Attaching one to a claim copies it into core_file.
CREATE TABLE cashflow4_uploads (
    id           text PRIMARY KEY,
    uploader     text NOT NULL, -- username
    storage_key  text NOT NULL, -- under media/, as core_file.file
    filename     text NOT NULL,
    content_type text NOT NULL,
    size_bytes   bigint NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    attached_at  timestamptz
);
