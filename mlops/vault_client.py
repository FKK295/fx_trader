import logging
from typing import Any, Dict, Optional

import hvac
from cachetools import TTLCache, cached
from hvac.exceptions import VaultError
from tenacity import retry, stop_after_attempt, wait_exponential

from fx_trader.config import settings
from fx_trader.utils.logging import get_logger

logger = get_logger(__name__)

# Cache for secrets to reduce Vault calls
# TTL is based on settings, e.g., 5 minutes
secrets_cache = TTLCache(maxsize=100, ttl=settings.VAULT_CACHE_TTL_SECONDS)


class VaultClient:
    def __init__(
        self,
        addr: str = settings.VAULT_ADDR,
        role_id: Optional[str] = settings.VAULT_ROLE_ID,
        secret_id: Optional[str] = settings.VAULT_SECRET_ID,
        token: Optional[str] = settings.VAULT_TOKEN,
        kv_mount_point: str = settings.VAULT_KV_MOUNT_POINT,
    ):
        self.addr = addr
        self.role_id = role_id
        self.secret_id = secret_id
        self.token = token  # Can be used if AppRole is not set
        self.kv_mount_point = kv_mount_point
        self.client = hvac.Client(url=self.addr)
        self._authenticate()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _authenticate(self) -> None:
        """Authenticates the client with Vault using AppRole or Token."""
        if self.client.is_authenticated():
            logger.info("Already authenticated with Vault.")
            return

        try:
            if self.role_id and self.secret_id:
                logger.info(
                    f"Authenticating with Vault using AppRole: {self.role_id}")
                hvac.api.auth_methods.AppRole(self.client.adapter).login(
                    role_id=self.role_id,
                    secret_id=self.secret_id,
                )
            elif self.token:
                logger.info("Authenticating with Vault using Token.")
                self.client.token = self.token
            else:
                logger.error(
                    "Vault AppRole (RoleID/SecretID) or Token not configured.")
                raise VaultError(
                    "Vault authentication credentials not provided.")

            if not self.client.is_authenticated():
                logger.error("Vault authentication failed.")
                raise VaultError("Failed to authenticate with Vault.")

            logger.info("Successfully authenticated with Vault.")

            # TODO: Implement token renewal logic if using AppRole and long-lived operations
            # if settings.VAULT_RENEW_TOKEN and self.client.session.auth.client_token:
            #    self.client.renew_token(self.client.session.auth.client_token)

        except VaultError as e:
            logger.error(f"Vault authentication error: {e}")
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during Vault authentication: {e}")
            raise

    @cached(secrets_cache)  # Cache the result of this method
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_secret(self, path: str) -> Dict[str, Any]:
        """
        Retrieves a secret from Vault's KV store.
        Assumes KV version 2.

        :param path: Path to the secret (e.g., 'fx_trader/api_keys').
        :return: A dictionary containing the secret data.
        """
        if not self.client.is_authenticated():
            logger.warning(
                "Not authenticated with Vault. Attempting to re-authenticate.")
            self._authenticate()

        try:
            logger.debug(
                f"Fetching secret from Vault path: {self.kv_mount_point}/data/{path}")
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.kv_mount_point,
            )
            return response["data"]["data"]  # For KV v2
        except VaultError as e:
            logger.error(f"Error reading secret '{path}' from Vault: {e}")
            # Potentially clear cache for this specific key if error indicates staleness
            # secrets_cache.pop((self, path), None) # Requires making path hashable or using a wrapper
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while fetching secret '{path}': {e}")
            raise


# Global instance (optional, can be instantiated as needed)
# vault_client = VaultClient()

# Example usage:
# if __name__ == "__main__":
#     try:
#         api_keys = vault_client.get_secret(settings.VAULT_SECRET_PATH)
#         oanda_token = api_keys.get("OANDA_ACCESS_TOKEN")
#         print(f"OANDA Token (from Vault): {oanda_token[:5]}...")
#     except Exception as e:
#         print(f"Failed to get secrets: {e}")
