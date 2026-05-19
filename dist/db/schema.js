export const EMBEDDING_DIMENSION = 384;
export const DATABASE_SCHEMA_SQL = `
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS classes (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subjects (
  id BIGSERIAL PRIMARY KEY,
  class_id BIGINT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (class_id, name)
);

CREATE TABLE IF NOT EXISTS chapters (
  id BIGSERIAL PRIMARY KEY,
  subject_id BIGINT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (subject_id, name)
);

CREATE TABLE IF NOT EXISTS topics (
  id BIGSERIAL PRIMARY KEY,
  chapter_id BIGINT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (chapter_id, name)
);

INSERT INTO classes (name, sort_order)
VALUES
  ('Class 6', 6),
  ('Class 7', 7),
  ('Class 8', 8),
  ('Class 9', 9),
  ('Class 10', 10),
  ('Class 11', 11),
  ('Class 12', 12)
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS textbook_chunks (
  id BIGSERIAL PRIMARY KEY,
  class_id BIGINT REFERENCES classes(id) ON DELETE SET NULL,
  subject_id BIGINT REFERENCES subjects(id) ON DELETE SET NULL,
  chapter_id BIGINT REFERENCES chapters(id) ON DELETE SET NULL,
  topic_id BIGINT REFERENCES topics(id) ON DELETE SET NULL,
  class_name TEXT,
  subject TEXT,
  chapter TEXT,
  topic TEXT,
  content TEXT NOT NULL,
  source_file TEXT NOT NULL,
  page INTEGER NOT NULL,
  embedding vector(384) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE textbook_chunks
  ADD COLUMN IF NOT EXISTS class_id BIGINT REFERENCES classes(id) ON DELETE SET NULL;
ALTER TABLE textbook_chunks
  ADD COLUMN IF NOT EXISTS subject_id BIGINT REFERENCES subjects(id) ON DELETE SET NULL;
ALTER TABLE textbook_chunks
  ADD COLUMN IF NOT EXISTS chapter_id BIGINT REFERENCES chapters(id) ON DELETE SET NULL;
ALTER TABLE textbook_chunks
  ADD COLUMN IF NOT EXISTS topic_id BIGINT REFERENCES topics(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS tutor_threads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT 'New chat',
  class_id BIGINT REFERENCES classes(id) ON DELETE SET NULL,
  subject_id BIGINT REFERENCES subjects(id) ON DELETE SET NULL,
  chapter_id BIGINT REFERENCES chapters(id) ON DELETE SET NULL,
  topic_id BIGINT REFERENCES topics(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tutor_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_id UUID NOT NULL REFERENCES tutor_threads(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  citations JSONB NOT NULL DEFAULT '[]'::jsonb,
  retrieval_metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_progress (
  id BIGSERIAL PRIMARY KEY,
  session_id TEXT NOT NULL,
  class_id BIGINT REFERENCES classes(id) ON DELETE SET NULL,
  subject_id BIGINT REFERENCES subjects(id) ON DELETE SET NULL,
  chapter_id BIGINT REFERENCES chapters(id) ON DELETE SET NULL,
  topic_id BIGINT REFERENCES topics(id) ON DELETE SET NULL,
  questions_asked INTEGER NOT NULL DEFAULT 0,
  topics_explored INTEGER NOT NULL DEFAULT 0,
  completed_chapters INTEGER NOT NULL DEFAULT 0,
  current_streak INTEGER NOT NULL DEFAULT 0,
  xp INTEGER NOT NULL DEFAULT 0,
  confidence_score NUMERIC(6, 4) NOT NULL DEFAULT 0,
  last_question_on DATE,
  last_interacted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS user_progress_session_topic_idx
  ON user_progress (session_id, topic_id)
  WHERE topic_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS classes_sort_idx
  ON classes (sort_order ASC, name ASC);
CREATE INDEX IF NOT EXISTS subjects_class_idx
  ON subjects (class_id, sort_order ASC, name ASC);
CREATE INDEX IF NOT EXISTS chapters_subject_idx
  ON chapters (subject_id, sort_order ASC, name ASC);
CREATE INDEX IF NOT EXISTS topics_chapter_idx
  ON topics (chapter_id, sort_order ASC, name ASC);

CREATE INDEX IF NOT EXISTS textbook_chunks_lookup_idx
  ON textbook_chunks (class_id, subject_id, chapter_id, topic_id);

CREATE INDEX IF NOT EXISTS textbook_chunks_text_lookup_idx
  ON textbook_chunks (class_name, subject, chapter, topic);

CREATE INDEX IF NOT EXISTS textbook_chunks_created_at_idx
  ON textbook_chunks (created_at DESC);

CREATE INDEX IF NOT EXISTS textbook_chunks_embedding_hnsw_idx
  ON textbook_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS textbook_chunks_tsv_idx
  ON textbook_chunks
  USING GIN (
    to_tsvector(
      'english',
      coalesce(class_name, '') || ' ' ||
      coalesce(subject, '') || ' ' ||
      coalesce(chapter, '') || ' ' ||
      coalesce(topic, '') || ' ' ||
      coalesce(content, '')
    )
  );

CREATE UNIQUE INDEX IF NOT EXISTS textbook_chunks_dedup_idx
  ON textbook_chunks (
    (
      md5(
        coalesce(class_name, '') || '|' ||
        coalesce(subject, '') || '|' ||
        coalesce(chapter, '') || '|' ||
        coalesce(topic, '') || '|' ||
        coalesce(source_file, '') || '|' ||
        coalesce(page::text, '') || '|' ||
        coalesce(content, '')
      )
    )
  );

CREATE INDEX IF NOT EXISTS tutor_threads_session_updated_idx
  ON tutor_threads (session_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS tutor_messages_thread_created_idx
  ON tutor_messages (thread_id, created_at ASC);
CREATE INDEX IF NOT EXISTS user_progress_session_updated_idx
  ON user_progress (session_id, last_interacted_at DESC);
`;
export async function ensureDatabaseSchema(client) {
    await client.query(DATABASE_SCHEMA_SQL);
}
//# sourceMappingURL=schema.js.map