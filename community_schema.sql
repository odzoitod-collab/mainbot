-- Community system tables for Supabase

-- Communities table
CREATE TABLE IF NOT EXISTS communities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    chat_link VARCHAR(500) NOT NULL,
    creator_id BIGINT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    members_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by BIGINT
);

-- Community members table
CREATE TABLE IF NOT EXISTS community_members (
    id SERIAL PRIMARY KEY,
    community_id INTEGER REFERENCES communities(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(community_id, user_id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_communities_status ON communities(status);
CREATE INDEX IF NOT EXISTS idx_communities_creator ON communities(creator_id);
CREATE INDEX IF NOT EXISTS idx_communities_active ON communities(is_active);
CREATE INDEX IF NOT EXISTS idx_community_members_community ON community_members(community_id);
CREATE INDEX IF NOT EXISTS idx_community_members_user ON community_members(user_id);

-- Function to update members count
CREATE OR REPLACE FUNCTION update_community_members_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE communities 
        SET members_count = members_count + 1 
        WHERE id = NEW.community_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE communities 
        SET members_count = members_count - 1 
        WHERE id = OLD.community_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update members count
DROP TRIGGER IF EXISTS trigger_update_community_members_count ON community_members;
CREATE TRIGGER trigger_update_community_members_count
    AFTER INSERT OR DELETE ON community_members
    FOR EACH ROW EXECUTE FUNCTION update_community_members_count();

-- Function to get communities with user membership status
CREATE OR REPLACE FUNCTION get_communities_for_user(p_user_id BIGINT)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR(100),
    description TEXT,
    chat_link VARCHAR(500),
    creator_id BIGINT,
    status VARCHAR(20),
    members_count INTEGER,
    is_active BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE,
    is_member BOOLEAN,
    creator_name TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        c.description,
        c.chat_link,
        c.creator_id,
        c.status,
        c.members_count,
        c.is_active,
        c.created_at,
        CASE WHEN cm.user_id IS NOT NULL THEN true ELSE false END as is_member,
        COALESCE(u.full_name, u.username, 'Неизвестный') as creator_name
    FROM communities c
    LEFT JOIN community_members cm ON c.id = cm.community_id AND cm.user_id = p_user_id AND cm.is_active = true
    LEFT JOIN users u ON c.creator_id = u.id
    WHERE c.is_active = true AND c.status = 'approved'
    ORDER BY c.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending communities for admin
CREATE OR REPLACE FUNCTION get_pending_communities()
RETURNS TABLE (
    id INTEGER,
    name VARCHAR(100),
    description TEXT,
    chat_link VARCHAR(500),
    creator_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE,
    creator_name TEXT,
    creator_username TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        c.description,
        c.chat_link,
        c.creator_id,
        c.created_at,
        u.full_name as creator_name,
        u.username as creator_username
    FROM communities c
    LEFT JOIN users u ON c.creator_id = u.id
    WHERE c.status = 'pending' AND c.is_active = true
    ORDER BY c.created_at ASC;
END;
$$ LANGUAGE plpgsql;

-- RLS policies (if needed)
ALTER TABLE communities ENABLE ROW LEVEL SECURITY;
ALTER TABLE community_members ENABLE ROW LEVEL SECURITY;

-- Allow all operations for service role
CREATE POLICY "Allow all for service role" ON communities FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON community_members FOR ALL USING (true);