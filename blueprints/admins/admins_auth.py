"""
Authentification de l'espace admin.

Principe : on s'appuie sur Supabase Auth (email/mot de passe) plutôt que sur
un système maison, pour que les policies RLS `is_admin()` de schema.sql
fonctionnent telles quelles (elles vérifient `auth.uid()`).

- Le login se fait avec le client "anonyme" partagé (connexion.supabase).
- Une fois connecté, on garde le token d'accès dans la session Flask et on
  construit, à chaque requête, un client Supabase "scopé" sur cet
  utilisateur (build_scoped_client). C'est CE client qu'il faut utiliser
  pour toutes les écritures admin, sinon les policies RLS bloquent tout.
- On ne touche jamais au client global `connexion.supabase` : il reste
  anonyme pour le reste du site public.
"""
import os
import time
from functools import wraps

from flask import session, redirect, url_for, request, flash, g
from supabase import create_client

from connexion import supabase as public_supabase

SUPABASE_URL = os.environ.get("SUPABASE_URL")
# Utilise la même clé "anon" que le reste du site : la sécurité vient de la
# session utilisateur (JWT) + des policies RLS, pas de la clé elle-même.
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY")


def build_scoped_client(access_token: str, refresh_token: str = None):
    """Crée un client Supabase indépendant, authentifié comme l'admin connecté.

    Un client par requête (plutôt que de muter le client global) évite les
    conditions de course entre requêtes concurrentes de plusieurs admins.
    """
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(access_token)
    # Nécessaire pour que client.storage / client.auth utilisent aussi ce token
    try:
        client.auth.set_session(access_token, refresh_token or access_token)
    except Exception:
        pass
    return client


def _refresh_session():
    """Rafraîchit le token d'accès avec le refresh_token stocké en session.
    Retourne True si le rafraîchissement a réussi."""
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        return False
    try:
        auth_res = public_supabase.auth.refresh_session(refresh_token)
    except Exception:
        return False
    if not auth_res or not auth_res.session:
        return False
    session["access_token"] = auth_res.session.access_token
    session["refresh_token"] = auth_res.session.refresh_token
    session["expires_at"] = auth_res.session.expires_at
    return True


def login_admin(email: str, password: str):
    """Tente de connecter un admin. Retourne (admin_dict, error_message)."""
    try:
        auth_res = public_supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except Exception:
        return None, "Identifiants incorrects."

    if not auth_res or not auth_res.session or not auth_res.user:
        return None, "Identifiants incorrects."

    access_token = auth_res.session.access_token
    refresh_token = auth_res.session.refresh_token
    user_id = auth_res.user.id

    scoped = build_scoped_client(access_token, refresh_token)
    row = (
        scoped.table("admins")
        .select("id, first_name, last_name, role, is_active, avatar_url")
        .eq("id", user_id)
        .execute()
        .data
    )

    if not row:
        return None, "Ce compte n'a pas accès à l'administration."

    admin = row[0]
    if not admin.get("is_active", False):
        return None, "Ce compte administrateur a été désactivé."

    session["admin_id"] = admin["id"]
    session["admin_name"] = f"{admin['first_name']} {admin['last_name']}"
    session["admin_role"] = admin["role"]
    session["admin_avatar"] = admin.get("avatar_url")
    session["access_token"] = access_token
    session["refresh_token"] = refresh_token
    session["expires_at"] = auth_res.session.expires_at
    session.permanent = True

    return admin, None


def logout_admin():
    try:
        public_supabase.auth.sign_out()
    except Exception:
        pass
    session.clear()


def current_admin():
    if "admin_id" not in session:
        return None
    return {
        "id": session["admin_id"],
        "name": session.get("admin_name"),
        "role": session.get("admin_role"),
        "avatar_url": session.get("admin_avatar"),
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "admin_id" not in session:
            flash("Connecte-toi pour accéder à l'administration.", "error")
            return redirect(url_for("admins.login", next=request.path))

        # Rafraîchit le token avant qu'il expire (durée de vie Supabase ~1h).
        # Couvre aussi les sessions ouvertes avant ce correctif (pas
        # d'"expires_at" en session) en tentant un refresh au premier appel
        # raté plus bas.
        expires_at = session.get("expires_at")
        if expires_at and time.time() >= expires_at - 60:
            if not _refresh_session():
                session.clear()
                flash("Ta session a expiré, reconnecte-toi.", "error")
                return redirect(url_for("admins.login", next=request.path))

        g.db = build_scoped_client(session["access_token"], session.get("refresh_token"))

        # Revalide le compte à chaque requête (actif ? rôle toujours le
        # même ?) — protège aussi contre le cas où on te désactive pendant
        # que tu es déjà connecté : tu ne restes pas connecté à agir.
        try:
            row = (
                g.db.table("admins")
                .select("id, first_name, last_name, role, is_active, avatar_url")
                .eq("id", session["admin_id"])
                .execute()
                .data
            )
        except Exception:
            # Le token a pu expirer entre-temps (session ouverte avant ce
            # correctif) : un seul essai de rafraîchissement puis on relit.
            row = None
            if _refresh_session():
                g.db = build_scoped_client(session["access_token"], session.get("refresh_token"))
                try:
                    row = (
                        g.db.table("admins")
                        .select("id, first_name, last_name, role, is_active, avatar_url")
                        .eq("id", session["admin_id"])
                        .execute()
                        .data
                    )
                except Exception:
                    row = None

        if not row or not row[0].get("is_active", False):
            session.clear()
            flash("Ce compte n'a plus accès à l'administration.", "error")
            return redirect(url_for("admins.login"))

        admin = row[0]
        session["admin_name"] = f"{admin['first_name']} {admin['last_name']}"
        session["admin_role"] = admin["role"]
        session["admin_avatar"] = admin.get("avatar_url")

        g.admin = current_admin()
        return view(*args, **kwargs)
    return wrapped


def super_admin_required(view):
    @login_required
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("admin_role") != "super_admin":
            flash("Réservé aux super-administrateurs.", "error")
            return redirect(url_for("admins.dashboard"))
        return view(*args, **kwargs)
    return wrapped
