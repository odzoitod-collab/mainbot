-- Create the ideas table for the IRL Team bot
-- This table stores user ideas and suggestions with voting functionality

CREATE TABLE IF NOT EXISTS ideas (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_name TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'Идея',
    votes_count INTEGER DEFAULT 0,
    liked_by TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ideas_votes ON ideas(votes_count DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_created ON ideas(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_category ON ideas(category);
CREATE INDEX IF NOT EXISTS idx_ideas_user ON ideas(user_id);

-- Enable Row Level Security
ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (since this is a team collaboration tool)
CREATE POLICY "Enable read access for all users" ON ideas FOR SELECT USING (true);
CREATE POLICY "Enable insert for all users" ON ideas FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for vote logic" ON ideas FOR UPDATE USING (true);

-- Add comments to the table and columns
COMMENT ON TABLE ideas IS 'Таблица идей и предложений от пользователей';
COMMENT ON COLUMN ideas.id IS 'Уникальный идентификатор идеи';
COMMENT ON COLUMN ideas.user_id IS 'ID пользователя в Telegram';
COMMENT ON COLUMN ideas.user_name IS 'Имя пользователя (username или first_name)';
COMMENT ON COLUMN ideas.content IS 'Текст идеи или предложения';
COMMENT ON COLUMN ideas.category IS 'Категория идеи (Идея, Сервис, Баг, и т.д.)';
COMMENT ON COLUMN ideas.votes_count IS 'Количество лайков/голосов';
COMMENT ON COLUMN ideas.liked_by IS 'Массив ID пользователей, которые лайкнули';
COMMENT ON COLUMN ideas.created_at IS 'Дата и время создания идеи';