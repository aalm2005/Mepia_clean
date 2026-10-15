"""Sesiones Supabase y propiedad explícita; nunca confiar en el business_id solo."""
from dataclasses import dataclass, field
from functools import cached_property
from urllib.parse import urlparse
from uuid import UUID

import jwt
from fastapi import HTTPException


@dataclass(frozen=True)
class AuthService:
    supabase_url: str
    jwt_secret: str = field(default="", repr=False)
    algorithm: str = "HS256"

    def validate_configuration(self) -> None:
        url = urlparse(self.supabase_url)
        if (url.scheme != "https" or not url.hostname or url.username or url.password
                or url.path not in ("", "/") or url.query or url.fragment
                or self.algorithm not in ("HS256", "ES256")):
            raise RuntimeError("Configura la URL y el algoritmo de sesión del proyecto")
        if self.algorithm == "HS256" and len(self.jwt_secret.encode()) < 32:
            raise RuntimeError("Configura SUPABASE_JWT_SECRET para sesiones HS256")

    @cached_property
    def _jwks_client(self):
        # Solo el origen del servidor; nunca jku/x5u ni una URL del token.
        # Sin cache permanente de claves: respeta la caducidad del conjunto.
        return jwt.PyJWKClient(
            self.supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json",
            cache_keys=False, lifespan=300, timeout=5, cooldown_duration=30,
        )

    def user_id(self, token: str) -> str:
        try:
            self.validate_configuration()
        except RuntimeError:
            raise HTTPException(503, "Autenticación no disponible") from None
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != self.algorithm:
                raise jwt.InvalidTokenError()
            key = self.jwt_secret
            if self.algorithm == "ES256":
                kid = header.get("kid")
                if not isinstance(kid, str) or not kid or len(kid) > 256:
                    raise jwt.InvalidTokenError()
                try:
                    signing_key = self._jwks_client.get_signing_key_from_jwt(token)
                except (jwt.PyJWKClientConnectionError, jwt.PyJWKSetError, jwt.PyJWKError, ValueError):
                    raise HTTPException(503, "Autenticación no disponible") from None
                if signing_key.algorithm_name != "ES256":
                    raise jwt.InvalidTokenError()
                key = signing_key.key
            payload = jwt.decode(
                token, key, algorithms=[self.algorithm],
                audience="authenticated", issuer=self.supabase_url.rstrip("/") + "/auth/v1",
                options={"require": ["exp", "iat", "sub", "iss", "aud", "role"]},
            )
            if (payload["role"] != "authenticated" or payload.get("is_anonymous", False) is not False
                    or type(payload["exp"]) is not int or type(payload["iat"]) is not int):
                raise jwt.InvalidTokenError()
            return str(UUID(payload["sub"]))
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token expirado", headers={"WWW-Authenticate": "Bearer"}) from None
        except (jwt.InvalidTokenError, jwt.PyJWKClientError, ValueError, TypeError, AttributeError):
            raise HTTPException(401, "Sesión inválida", headers={"WWW-Authenticate": "Bearer"}) from None

    @staticmethod
    def verify_business_access(db, user_id: str, business_id: str) -> None:
        try:
            rows = (db.table("businesses").select("id,owner_id")
                    .eq("id", business_id).eq("owner_id", user_id).limit(1).execute()).data
        except Exception:
            raise HTTPException(503, "Permisos no disponibles") from None
        if (not isinstance(rows, list) or len(rows) != 1
                or not isinstance(rows[0], dict)
                or str(rows[0].get("id")) != business_id
                or str(rows[0].get("owner_id")) != user_id):
            # No distinguir negocio inexistente, ajeno o sin propietario.
            raise HTTPException(403, "Sin acceso a este negocio")
