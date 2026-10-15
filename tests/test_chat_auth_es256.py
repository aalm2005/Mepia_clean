"""Firma asimétrica real; descubrimiento sustituido sin llamadas externas."""
import json
from time import time
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException

from api.core.auth import AuthService


URL = "https://synthetic-project.supabase.co"
KEY = ec.generate_private_key(ec.SECP256R1())
OTHER_KEY = ec.generate_private_key(ec.SECP256R1())
USER = str(uuid4())


def token(*, key=KEY, headers=None, **overrides):
    claims = {"sub": USER, "iss": URL + "/auth/v1", "aud": "authenticated",
              "role": "authenticated", "iat": int(time()) - 1, "exp": int(time()) + 300}
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="ES256", headers=headers or {"kid": "current-test-key"})


@pytest.fixture
def auth(monkeypatch):
    jwk = json.loads(jwt.algorithms.ECAlgorithm.to_jwk(KEY.public_key()))
    jwk.update(kid="current-test-key", alg="ES256", use="sig")
    calls = []
    def fetch(client):
        calls.append(client.uri)
        return {"keys": [jwk]}
    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", fetch)
    return AuthService(URL, algorithm="ES256"), calls


def test_real_signature_uses_only_configured_project_even_with_jku(auth):
    service, calls = auth
    service.validate_configuration()
    assert service.user_id(token(headers={"kid": "current-test-key", "jku": "https://attacker.invalid/keys"})) == USER
    assert calls == [URL + "/auth/v1/.well-known/jwks.json"]


@pytest.mark.parametrize("claims", [{"iss": "https://other.invalid/auth/v1"}, {"aud": "anon"},
    {"role": "service_role"}, {"is_anonymous": True}, {"exp": int(time()) - 100},
    {"sub": "invalid"}, {"iat": int(time()) + 300}])
def test_signed_invalid_claims_still_rejected(auth, claims):
    with pytest.raises(HTTPException) as error:
        auth[0].user_id(token(**claims))
    assert error.value.status_code == 401


def test_other_private_key_fails_signature(auth):
    with pytest.raises(HTTPException) as error:
        auth[0].user_id(token(key=OTHER_KEY))
    assert error.value.status_code == 401


@pytest.mark.parametrize("kid", [None, "", [], "x" * 257])
def test_invalid_kid_never_contacts_discovery(auth, kid):
    headers = {} if kid is None else {"kid": kid}
    # PyJWT itself refuses non-string kid when encoding; craft the header locally.
    raw = token().split(".")
    from jwt.utils import base64url_encode
    raw[0] = base64url_encode(json.dumps({"alg": "ES256", **headers}).encode()).decode()
    with pytest.raises(HTTPException) as error:
        auth[0].user_id(".".join(raw))
    assert error.value.status_code == 401 and auth[1] == []


def test_unknown_kid_is_401(auth):
    with pytest.raises(HTTPException) as error:
        auth[0].user_id(token(headers={"kid": "other-test-key"}))
    assert error.value.status_code == 401


def test_hs256_does_not_fallback_in_es256_mode(auth):
    forged = jwt.encode({"sub": USER}, "synthetic-secret-32-bytes-long-only", algorithm="HS256")
    with pytest.raises(HTTPException) as error:
        auth[0].user_id(forged)
    assert error.value.status_code == 401 and auth[1] == []


@pytest.mark.parametrize("failure", [jwt.PyJWKClientConnectionError, jwt.PyJWKSetError])
def test_discovery_errors_fail_closed_without_raw_exception(auth, monkeypatch, failure):
    def fail(_client):
        raise failure("synthetic-private-message-must-not-leak")
    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", fail)
    with pytest.raises(HTTPException) as error:
        auth[0].user_id(token())
    assert error.value.status_code == 503
    assert error.value.detail == "Autenticación no disponible"


@pytest.mark.parametrize("url", ["http://test.invalid", "https://test.invalid/path", "https://user:pass@test.invalid"])
def test_unsafe_project_origins_rejected_before_discovery(url):
    with pytest.raises(RuntimeError):
        AuthService(url, algorithm="ES256").validate_configuration()
