-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.admins (
  id uuid NOT NULL,
  first_name character varying NOT NULL,
  last_name character varying NOT NULL,
  phone character varying,
  avatar_url text,
  role character varying DEFAULT 'admin'::character varying CHECK (role::text = ANY (ARRAY['super_admin'::character varying, 'admin'::character varying, 'editor'::character varying]::text[])),
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT admins_pkey PRIMARY KEY (id),
  CONSTRAINT admins_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id)
);
CREATE TABLE public.events (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  title character varying NOT NULL,
  description text,
  start_date timestamp with time zone NOT NULL,
  end_date timestamp with time zone,
  time_label character varying,
  location text,
  department character varying,
  status character varying DEFAULT 'upcoming'::character varying,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  hero_media_url text,
  CONSTRAINT events_pkey PRIMARY KEY (id)
);
CREATE TABLE public.communications (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  reference_number character varying,
  title character varying NOT NULL,
  subtitle character varying,
  department character varying,
  author character varying,
  content text,
  hero_media_type character varying CHECK (hero_media_type::text = ANY (ARRAY['image'::character varying, 'video'::character varying]::text[])),
  hero_media_url text,
  download_url text,
  event_id uuid,
  published_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  federation text,
  hero_media_description text DEFAULT 'Illustration du communiqué'::text,
  download_type text,
  CONSTRAINT communications_pkey PRIMARY KEY (id),
  CONSTRAINT communications_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id)
);
CREATE TABLE public.rubrics (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  title character varying NOT NULL,
  category character varying,
  speaker character varying,
  description text,
  youtube_id character varying NOT NULL,
  published_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT rubrics_pkey PRIMARY KEY (id)
);
CREATE TABLE public.sermons (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  title character varying NOT NULL,
  subtitle character varying,
  reference character varying,
  content text,
  author character varying,
  hero_media_type character varying CHECK (hero_media_type::text = ANY (ARRAY['image'::character varying, 'video'::character varying]::text[])),
  hero_media_url text,
  audio_url text,
  pdf_url text,
  event_id uuid,
  published_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT sermons_pkey PRIMARY KEY (id),
  CONSTRAINT sermons_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id)
);
CREATE TABLE public.galleries (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  title character varying NOT NULL,
  department character varying,
  description text,
  cover_image_url text,
  event_date date,
  event_id uuid,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT galleries_pkey PRIMARY KEY (id),
  CONSTRAINT galleries_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id)
);
CREATE TABLE public.media_items (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  gallery_id uuid,
  type character varying CHECK (type::text = ANY (ARRAY['photo'::character varying, 'video'::character varying]::text[])),
  media_url text NOT NULL,
  thumbnails_url text,
  credit character varying,
  display_order integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT media_items_pkey PRIMARY KEY (id),
  CONSTRAINT media_items_gallery_id_fkey FOREIGN KEY (gallery_id) REFERENCES public.galleries(id)
);
CREATE TABLE public.featured_content (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  content_type character varying NOT NULL CHECK (content_type::text = ANY (ARRAY['event'::character varying, 'sermon'::character varying, 'communication'::character varying, 'rubric'::character varying]::text[])),
  content_id uuid NOT NULL,
  display_order integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT featured_content_pkey PRIMARY KEY (id)
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
