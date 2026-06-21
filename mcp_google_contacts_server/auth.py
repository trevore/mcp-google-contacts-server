"""OAuth 2.1 resource-server auth for the Contacts MCP server.

When the AUTH0_* env vars are set, the HTTP MCP endpoint requires a valid Auth0
JWT access token (signature via JWKS, issuer, audience, expiry). Unauthenticated
requests get 401 + WWW-Authenticate, and the server advertises the authorization
server via RFC 9728 protected-resource metadata so Claude can discover it.

Single-user restriction is enforced UPSTREAM at Auth0 (a post-login Action that
denies everyone but the owner); this resource server binds the token audience.
Auth0 is the authorization server — Google federation is only the login.
"""
import os
from typing import Optional

from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier


def build_auth(env: Optional[dict] = None) -> Optional[RemoteAuthProvider]:
    """Build the resource-server auth provider from env, or None if unconfigured.

    Required env:
      AUTH0_ISSUER    https://<tenant>.<region>.auth0.com/  (trailing slash)
      AUTH0_JWKS_URI  the issuer's jwks_uri (copy verbatim from openid-configuration)
      AUTH0_AUDIENCE  the Auth0 API Identifier == the MCP connector URL
                      (https://gcontacts.ellermann.net/mcp)
      MCP_BASE_URL    public base URL of this server (https://gcontacts.ellermann.net)
    """
    env = env if env is not None else os.environ
    issuer = env.get("AUTH0_ISSUER")
    jwks_uri = env.get("AUTH0_JWKS_URI")
    audience = env.get("AUTH0_AUDIENCE")
    base_url = env.get("MCP_BASE_URL")
    if not (issuer and jwks_uri and audience and base_url):
        return None

    verifier = JWTVerifier(
        jwks_uri=jwks_uri,
        issuer=issuer,
        audience=audience,
        algorithm="RS256",
    )
    return RemoteAuthProvider(
        token_verifier=verifier,
        authorization_servers=[issuer],
        base_url=base_url,
        resource_name="Google Contacts MCP",
    )
