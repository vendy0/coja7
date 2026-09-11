"""
Admin area authentication.

Design: we rely on Supabase Auth (email/password) instead of a homegrown
system, so that the RLS policies using `is_admin()` (see schema.sql) work
unmodified — they check `auth.uid()`, which only exists for requests made
with a real Supabase-issued JWT.

- Login happens through the shared "anonymous" client (connexion.supabase).
- Once logged in, we keep the access token in the Flask session and build,
  on every request, a Supabase client "scoped" to that user
  (build_scoped_client). This is the client that MUST be used for all admin
  writes — using the anonymous client instead would make every write get
  silently rejected by RLS.
- We never mutate the global `connexion.supabase` client: it stays
  anonymous for the rest of the public site, regardless of what happens
  in the admin area.
"""
import os
import time
import secrets
from functools import wraps

from flask import session, redirect, url_for, request, flash, g
from supabase import create_client

from connexion import supabase as public_supabase

SUPABASE_URL = os.environ.get("SUPABASE_URL")
# Same "anon" key as the rest of the site: security comes from the user's
# session (JWT) + RLS policies, not from the key itself.
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY")


def build_scoped_client(access_token: str, refresh_token: str = None):
    """Create an independent Supabase client, authenticated as the logged-in admin.

    One client per request (rather than mutating a shared global one)
    avoids race conditions between concurrent requests from different admins.
    """
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(access_token)
    # Needed so that client.storage / client.auth also use this token
    try:
        client.auth.set_session(access_token, refresh_token or access_token)
    except Exception:
        pass
    return client


def _refresh_session():
    """Refresh the access token using the refresh_token stored in the session.
    Returns True if the refresh succeeded."""
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
    """Attempt to log an admin in. Returns (admin_dict, error_message)."""
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

    # Scoped client (not the anonymous one): reading the `admins` table
    # requires auth.uid() to resolve, per the RLS policy on that table.
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
    """Sign out of Supabase Auth and drop the whole Flask session."""
    try:
        public_supabase.auth.sign_out()
    except Exception:
        pass
    session.clear()


def current_admin():
    """Lightweight admin info from the session only — no DB round trip.
    Used to populate g.admin for templates; the per-request freshness
    check (active? same role?) happens separately in login_required."""
    if "admin_id" not in session:
        return None
    return {
        "id": session["admin_id"],
        "name": session.get("admin_name"),
        "role": session.get("admin_role"),
        "avatar_url": session.get("admin_avatar"),
    }


def login_required(view):
    """Gatekeeper for every protected admin view.

    Beyond the basic "is someone logged in" check, this also:
    - transparently refreshes the Supabase access token before it expires
      (~1h lifetime), so a long admin session doesn't get cut off mid-task
    - re-checks the admin's `is_active` flag and role on every single
      request (not just at login) — this is what makes account
      deactivation take effect immediately, even for someone already
      logged in, instead of only on their next login
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "admin_id" not in session:
            flash("Connecte-toi pour accéder à l'administration.", "error")
            return redirect(url_for("admins.login", next=request.path))

        expires_at = session.get("expires_at")
        if expires_at and time.time() >= expires_at - 60:
            if not _refresh_session():
                session.clear()
                flash("Ta session a expiré, reconnecte-toi.", "error")
                return redirect(url_for("admins.login", next=request.path))

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
            # The token may have expired between requests (e.g. a session
            # that predates the proactive refresh above). One retry after
            # a forced refresh before giving up.
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

        # Keep the session's cached name/role/avatar in sync with the DB —
        # covers the case where a super_admin changes this admin's role
        # while they're mid-session.
        admin = row[0]
        session["admin_name"] = f"{admin['first_name']} {admin['last_name']}"
        session["admin_role"] = admin["role"]
        session["admin_avatar"] = admin.get("avatar_url")

        g.admin = current_admin()
        return view(*args, **kwargs)
    return wrapped


def super_admin_required(view):
    """Same as login_required, plus a role check. Order matters: login_required
    must run first so that g.db / g.admin / session are populated before we
    can even check the role."""
    @login_required
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("admin_role") != "super_admin":
            flash("Réservé aux super-administrateurs.", "error")
            return redirect(url_for("admins.dashboard"))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# CSRF protection
#
# No external dependency (Flask-WTF): a random per-session token, checked on
# every POST via the blueprint's before_request (see admins_routes.py).
# Exposed to templates as the Jinja function csrf_token(), and to JS via a
# <meta> tag in base_admin.html — any fetch() call that doesn't build its
# body from FormData(form) (which already includes the hidden field
# automatically) must read that token itself and send it in the
# X-CSRF-Token header.
# ---------------------------------------------------------------------------

def get_csrf_token():
    """Return this session's CSRF token, generating one on first use."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def verify_csrf_token(submitted):
    """Constant-time comparison against the session's token — avoids leaking
    timing information that could help guess a valid token byte by byte."""
    expected = session.get("csrf_token")
    if not expected or not submitted:
        return False
    return secrets.compare_digest(expected, submitted)