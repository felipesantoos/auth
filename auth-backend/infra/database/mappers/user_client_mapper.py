"""
User Client Mapper
Maps between domain UserClient and database DBUserClient
Note: UserClient doesn't have a rich domain model yet, so this is a simpler mapper
"""
from typing import Optional
from infra.database.models.user_client import DBUserClient


class UserClientMapper:
    """Mapper for UserClient database model (no rich domain model yet)"""
    
    @staticmethod
    def to_db(
        user_id: str,
        client_id: str,
        workspace_id: Optional[str] = None,
        active: bool = True
    ) -> DBUserClient:
        """
        Create database model from parameters.
        
        Args:
            user_id: User ID
            client_id: Client ID
            workspace_id: Optional workspace ID (context)
            active: Whether access is active
            
        Returns:
            Database user client model
        """
        return DBUserClient(
            id=None,  # Will be generated
            user_id=user_id,
            client_id=client_id,
            workspace_id=workspace_id,
            active=active
        )

