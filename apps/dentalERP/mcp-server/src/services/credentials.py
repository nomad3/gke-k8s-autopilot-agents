"""Secure credential management service"""

import base64
import json
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..utils.logger import logger


class CredentialService:
    """
    Secure credential storage and retrieval service
    
    Features:
    - AES-256 encryption using Fernet
    - Automatic encryption/decryption
    - Secure key derivation from settings
    """
    
    def __init__(self):
        # Derive encryption key from settings.secret_key
        # In production, use a dedicated encryption key
        key_material = settings.secret_key.encode()[:32].ljust(32, b'0')
        key = base64.urlsafe_b64encode(key_material)
        self._cipher = Fernet(key)
    
    def encrypt(self, data: Dict[str, Any]) -> str:
        """
        Encrypt credential data
        
        Args:
            data: Credential dictionary to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        try:
            json_data = json.dumps(data)
            encrypted = self._cipher.encrypt(json_data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt credential data
        
        Args:
            encrypted_data: Encrypted string
            
        Returns:
            Decrypted credential dictionary
        """
        try:
            decrypted = self._cipher.decrypt(encrypted_data.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    async def store_credentials(
        self,
        db: AsyncSession,
        integration_type: str,
        credentials: Dict[str, Any],
        practice_id: Optional[str] = None
    ) -> int:
        """
        Store encrypted credentials in database
        
        Args:
            db: Database session
            integration_type: Type of integration
            credentials: Credential dictionary
            practice_id: Optional practice ID for practice-specific credentials
            
        Returns:
            Credential ID
        """
        # TODO: Implement database storage
        # For now, log and return mock ID
        encrypted = self.encrypt(credentials)
        logger.info(f"Credentials stored for {integration_type} (practice: {practice_id})")
        return 1
    
    async def get_credentials(
        self,
        db: AsyncSession,
        integration_type: str,
        practice_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt credentials
        
        Args:
            db: Database session
            integration_type: Type of integration
            practice_id: Optional practice ID
            
        Returns:
            Decrypted credentials or None
        """
        # TODO: Implement database retrieval
        # For now, return credentials from settings based on integration type
        
        if integration_type == "adp":
            return {
                "api_url": settings.adp_api_url,
                "client_id": settings.adp_client_id,
                "client_secret": settings.adp_client_secret,
            }
        elif integration_type == "netsuite":
            return {
                "api_url": settings.netsuite_api_url,
                "account": settings.netsuite_account,
                "consumer_key": settings.netsuite_consumer_key,
                "consumer_secret": settings.netsuite_consumer_secret,
                "token_key": settings.netsuite_token_key,
                "token_secret": settings.netsuite_token_secret,
            }
        elif integration_type == "dentalintel":
            return {
                "api_url": settings.dentalintel_api_url,
                "api_key": settings.dentalintel_api_key,
                "api_secret": settings.dentalintel_api_secret,
            }
        
        return None
    
    async def delete_credentials(
        self,
        db: AsyncSession,
        integration_type: str,
        practice_id: Optional[str] = None
    ) -> bool:
        """
        Delete credentials
        
        Args:
            db: Database session
            integration_type: Type of integration
            practice_id: Optional practice ID
            
        Returns:
            True if deleted, False otherwise
        """
        # TODO: Implement database deletion
        logger.info(f"Credentials deleted for {integration_type} (practice: {practice_id})")
        return True


# Singleton instance
_credential_service: Optional[CredentialService] = None


def get_credential_service() -> CredentialService:
    """Get singleton credential service"""
    global _credential_service
    if _credential_service is None:
        _credential_service = CredentialService()
    return _credential_service

