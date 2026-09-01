-- 1. EXTENSION UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- TABLE : ADMINS
-- ==========================================
CREATE TABLE admins (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(30),
    avatar_url TEXT,
    role VARCHAR(50) DEFAULT 'admin' CHECK (role IN ('super_admin', 'admin', 'editor')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- ==========================================
-- TABLE : EVENTS
-- ==========================================
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE,
    time_label VARCHAR(100),
    location TEXT,
    department VARCHAR(100),
    status VARCHAR(50) DEFAULT 'upcoming',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- TABLE : COMMUNICATIONS
-- ==========================================
CREATE TABLE communications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_number VARCHAR(100),
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    department VARCHAR(100),
    author VARCHAR(150),
    content TEXT,
    hero_media_type VARCHAR(20) CHECK (hero_media_type IN ('image', 'video')),
    hero_media_url TEXT,
    pdf_url TEXT,
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- TABLE : RUBRICS
-- ==========================================
CREATE TABLE rubrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    speaker VARCHAR(150),
    description TEXT,
    youtube_id VARCHAR(50) NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- TABLE : SERMONS
-- ==========================================
CREATE TABLE sermons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    reference VARCHAR(255),
    content TEXT,
    author VARCHAR(150),
    hero_media_type VARCHAR(20) CHECK (hero_media_type IN ('image', 'video')),
    hero_media_url TEXT,
    audio_url TEXT,
    pdf_url TEXT,
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- TABLE : GALLERIES
-- ==========================================
CREATE TABLE galleries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    description TEXT,
    cover_image_url TEXT,
    event_date DATE,
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- TABLE : MEDIA_ITEMS
-- ==========================================
CREATE TABLE media_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gallery_id UUID REFERENCES galleries(id) ON DELETE CASCADE,
    type VARCHAR(20) CHECK (type IN ('photo', 'video')),
    media_url TEXT NOT NULL,
    thumbnails_url TEXT,
    credit VARCHAR(150),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- TABLE : FEATURED_CONTENT
-- ==========================================
CREATE TABLE featured_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('event', 'sermon', 'communication', 'rubric')),
    content_id UUID NOT NULL,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_featured_item UNIQUE (content_type, content_id)
);

-- ==========================================
-- INDEX
-- ==========================================
-- Clés étrangères
CREATE INDEX idx_communications_event_id ON communications(event_id);
CREATE INDEX idx_sermons_event_id ON sermons(event_id);
CREATE INDEX idx_galleries_event_id ON galleries(event_id);
CREATE INDEX idx_media_items_gallery_id ON media_items(gallery_id);

-- Featured content
CREATE INDEX idx_featured_content_order ON featured_content(display_order ASC);
CREATE INDEX idx_featured_content_lookup ON featured_content(content_type, content_id);

-- Tris et recherches
CREATE INDEX idx_events_start_date ON events(start_date);
CREATE INDEX idx_sermons_published_at ON sermons(published_at);
CREATE INDEX idx_communications_published_at ON communications(published_at);
CREATE INDEX idx_events_department ON events(department);
CREATE INDEX idx_communications_department ON communications(department);


-- ==========================================
-- 1. ACTIVATION DU RLS SUR TOUTES LES TABLES
-- ==========================================
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE communications ENABLE ROW LEVEL SECURITY;
ALTER TABLE rubrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE sermons ENABLE ROW LEVEL SECURITY;
ALTER TABLE galleries ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE featured_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;

-- ==========================================
-- 2. RÈGLES DE LECTURE PUBLIQUE (Tout le monde peut lire)
-- ==========================================
CREATE POLICY "Lecture publique des événements" ON events FOR SELECT USING (true);
CREATE POLICY "Lecture publique des communications" ON communications FOR SELECT USING (true);
CREATE POLICY "Lecture publique des rubriques" ON rubrics FOR SELECT USING (true);
CREATE POLICY "Lecture publique des sermons" ON sermons FOR SELECT USING (true);
CREATE POLICY "Lecture publique des galeries" ON galleries FOR SELECT USING (true);
CREATE POLICY "Lecture publique des médias" ON media_items FOR SELECT USING (true);
CREATE POLICY "Lecture publique du contenu à la une" ON featured_content FOR SELECT USING (true);

-- Les profils admins ne sont lisibles que par les admins eux-mêmes
CREATE POLICY "Lecture des admins par les admins" ON admins 
FOR SELECT USING (auth.uid() IN (SELECT id FROM admins));

-- ==========================================
-- 3. RÈGLES D'ÉCRITURE (Réservées aux Admins)
-- ==========================================
-- Fonction utilitaire pour vérifier si l'utilisateur connecté est admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM admins WHERE id = auth.uid() AND is_active = true
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Politiques d'écriture globale pour les admins
CREATE POLICY "Gestion admins des événements" ON events FOR ALL USING (is_admin());
CREATE POLICY "Gestion admins des communications" ON communications FOR ALL USING (is_admin());
CREATE POLICY "Gestion admins des rubriques" ON rubrics FOR ALL USING (is_admin());
CREATE POLICY "Gestion admins des sermons" ON sermons FOR ALL USING (is_admin());
CREATE POLICY "Gestion admins des galeries" ON galleries FOR ALL USING (is_admin());
CREATE POLICY "Gestion admins des médias" ON media_items FOR ALL USING (is_admin());
CREATE POLICY "Gestion admins du contenu à la une" ON featured_content FOR ALL USING (is_admin());
CREATE POLICY "Gestion de la table admins" ON admins FOR ALL USING (is_admin());
