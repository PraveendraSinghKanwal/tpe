from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import httpx
from datetime import datetime, timedelta

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Security scheme
security = HTTPBearer()

# Okta JWKS cache
_jwks_cache = {}
_jwks_cache_expiry = None


class OktaAuth:
    """Okta authentication handler."""
    
    def __init__(self):
        self.issuer = settings.okta_issuer
        self.client_id = settings.okta_client_id
        self.client_secret = settings.okta_client_secret
        self.audience = settings.okta_audience
    
    async def get_jwks(self) -> Dict[str, Any]:
        """Get Okta JWKS (JSON Web Key Set) for token validation."""
        global _jwks_cache, _jwks_cache_expiry
        
        # Check if cache is still valid
        if _jwks_cache and _jwks_cache_expiry and datetime.utcnow() < _jwks_cache_expiry:
            return _jwks_cache
        
        try:
            jwks_url = f"{self.issuer}/.well-known/jwks.json"
            async with httpx.AsyncClient() as client:
                response = await client.get(jwks_url)
                response.raise_for_status()
                jwks = response.json()
                
                # Cache for 1 hour
                _jwks_cache = jwks
                _jwks_cache_expiry = datetime.utcnow() + timedelta(hours=1)
                
                logger.info("JWKS cache updated", jwks_url=jwks_url)
                return jwks
                
        except Exception as e:
            logger.error("Failed to fetch JWKS", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
    
    def get_signing_key(self, token: str, jwks: Dict[str, Any]) -> str:
        """Get the signing key for token validation."""
        try:
            # Decode header without verification to get key ID
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get("kid")
            
            if not key_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token header"
                )
            
            # Find the key in JWKS
            for key in jwks.get("keys", []):
                if key.get("kid") == key_id:
                    return key
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Signing key not found"
            )
            
        except JWTError as e:
            logger.error("JWT header decode error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            # Get JWKS
            jwks = await self.get_jwks()
            
            # Get signing key
            signing_key = self.get_signing_key(token, jwks)
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer
            )
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            return payload
            
        except JWTError as e:
            logger.error("Token verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected authentication error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            )
    
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """Get current authenticated user from token."""
        token = credentials.credentials
        payload = await self.verify_token(token)
        
        # Extract user information
        user_info = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "preferred_username": payload.get("preferred_username"),
            "groups": payload.get("groups", []),
            "scopes": payload.get("scope", "").split() if payload.get("scope") else []
        }
        
        logger.info("User authenticated", user_id=user_info["sub"])
        return user_info


# Global Okta auth instance
okta_auth = OktaAuth()

# Dependency for getting current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency to get current authenticated user."""
    return await okta_auth.get_current_user(credentials)


def require_scope(required_scope: str):
    """Decorator to require specific scope for endpoint access."""
    def scope_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_scopes = current_user.get("scopes", [])
        if required_scope not in user_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {required_scope}"
            )
        return current_user
    return scope_checker
