"""
Admin invitation — the ONLY file in this project that touches
SUPABASE_SERVICE_ROLE_KEY.

That key bypasses Row Level Security entirely. Every other read/write in
the admin area goes through a client scoped to the logged-in admin's own
session (see admins_auth.build_scoped_client), which is what makes RLS
policies meaningful in the first place. This file exists to keep that one
exception contained and easy to audit — if you're looking for where the
service-role key is used, it's only ever here.

Why this needs the service key at all: creating a new Supabase Auth user
via invite_user_by_email() requires Supabase's admin Auth API, which
service_role-only. A regular authenticated client (even a super_admin's)
cannot call it.
"""
import os
from supabase import create_client

_SUPABASE_URL = os.environ.get("SUPABASE_URL")
_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")


def _get_service_client():
    if not _SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY manquante — impossible d'inviter un admin sans elle."
        )
    return create_client(_SUPABASE_URL, _SERVICE_ROLE_KEY)


def invite_admin(email, first_name, last_name, role="editor", redirect_to=None):
    """Send a Supabase Auth invite email (the recipient sets their own
    password via the link it contains), then create the matching row in
    `admins` so they actually have access once they log in.

    redirect_to must be in Supabase's allowlist (Authentication -> URL
    Configuration -> Redirect URLs) or Supabase silently falls back to the
    project's default Site URL instead of raising an error — if the invite
    link doesn't land where expected, that allowlist is the first thing to
    check, not this code.

    Both the invite call and the `admins` insert use the service-role
    client on purpose: a brand-new user has no session yet to scope a
    regular client to, and RLS on `admins` would block a non-admin from
    inserting into it anyway.
    """
    service_client = _get_service_client()

    options = {"redirect_to": redirect_to} if redirect_to else {}
    res = service_client.auth.admin.invite_user_by_email(email, options)
    user_id = res.user.id

    service_client.table("admins").insert({
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "role": role,
        "is_active": True,
    }).execute()

    return user_id
