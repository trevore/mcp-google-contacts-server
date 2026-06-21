"""Resource-server auth tests: JWT validation (aud/iss/exp/signature) + build_auth wiring.

Uses a local RSA keypair and a static public key (no network/JWKS fetch), so these
run without a live Auth0 tenant.
"""
import asyncio
import time

import jwt  # PyJWT
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from mcp_google_contacts_server.auth import build_auth

ISSUER = "https://test-tenant.us.auth0.com/"
AUDIENCE = "https://gcontacts.ellermann.net/mcp"


def _keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv, pub


@pytest.fixture(scope="module")
def keys():
    return _keypair()


def _verifier(pub_pem):
    return JWTVerifier(public_key=pub_pem, issuer=ISSUER, audience=AUDIENCE, algorithm="RS256")


def _mint(priv_pem, **override):
    now = int(time.time())
    claims = {"iss": ISSUER, "aud": AUDIENCE, "sub": "auth0|owner", "iat": now, "exp": now + 300}
    claims.update(override)
    return jwt.encode(claims, priv_pem, algorithm="RS256")


def _verify(verifier, token):
    return asyncio.run(verifier.verify_token(token))


def test_valid_token_accepted(keys):
    priv, pub = keys
    assert _verify(_verifier(pub), _mint(priv)) is not None


def test_wrong_audience_rejected(keys):
    priv, pub = keys
    assert _verify(_verifier(pub), _mint(priv, aud="https://attacker.example/mcp")) is None


def test_wrong_issuer_rejected(keys):
    priv, pub = keys
    assert _verify(_verifier(pub), _mint(priv, iss="https://evil.example/")) is None


def test_expired_token_rejected(keys):
    priv, pub = keys
    assert _verify(_verifier(pub), _mint(priv, exp=int(time.time()) - 10)) is None


def test_token_signed_by_other_key_rejected(keys):
    _, pub = keys
    other_priv, _ = _keypair()
    assert _verify(_verifier(pub), _mint(other_priv)) is None


def test_build_auth_none_without_env():
    assert build_auth({}) is None


def test_build_auth_returns_resource_provider_with_env():
    provider = build_auth({
        "AUTH0_ISSUER": ISSUER,
        "AUTH0_JWKS_URI": ISSUER + ".well-known/jwks.json",
        "AUTH0_AUDIENCE": AUDIENCE,
        "MCP_BASE_URL": "https://gcontacts.ellermann.net",
    })
    assert isinstance(provider, RemoteAuthProvider)
