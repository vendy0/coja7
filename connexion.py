import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Chargement des variables d'environnement du fichier .env
load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Les variables SUPABASE_URL et SUPABASE_ANON_KEY doivent être définies dans le fichier .env")

# Instance du client Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

