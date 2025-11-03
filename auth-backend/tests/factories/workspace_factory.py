"""Factory for creating test workspace instances"""
import uuid
from datetime import datetime
from core.domain.workspace.workspace import Workspace
from core.domain.workspace.workspace_member import WorkspaceMember
from core.domain.workspace.workspace_role import WorkspaceRole
from infra.database.models.workspace import DBWorkspace
from infra.database.models.workspace_member import DBWorkspaceMember


class WorkspaceFactory:
    """Factory for creating workspace test instances"""
    
    @staticmethod
    def create_workspace(
        id: str = None,
        name: str = "Test Workspace",
        slug: str = "test-workspace",
        description: str = "A test workspace",
        settings: dict = None,
        active: bool = True
    ) -> Workspace:
        """Create a workspace domain model for testing"""
        return Workspace(
            id=id or str(uuid.uuid4()),
            name=name,
            slug=slug,
            description=description,
            settings=settings or {},
            active=active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @staticmethod
    def create_db_workspace(
        id: str = None,
        name: str = "Test Workspace",
        slug: str = "test-workspace",
        description: str = "A test workspace",
        active: bool = True
    ) -> DBWorkspace:
        """Create a DB workspace for testing"""
        return DBWorkspace(
            id=id or str(uuid.uuid4()),
            name=name,
            slug=slug,
            description=description,
            settings={},
            active=active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )


class WorkspaceMemberFactory:
    """Factory for creating workspace member test instances"""
    
    @staticmethod
    def create_member(
        id: str = None,
        user_id: str = None,
        workspace_id: str = None,
        role: WorkspaceRole = WorkspaceRole.USER,
        active: bool = True
    ) -> WorkspaceMember:
        """Create a workspace member domain model for testing"""
        return WorkspaceMember(
            id=id or str(uuid.uuid4()),
            user_id=user_id or str(uuid.uuid4()),
            workspace_id=workspace_id or str(uuid.uuid4()),
            role=role,
            active=active,
            joined_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @staticmethod
    def create_db_member(
        id: str = None,
        user_id: str = None,
        workspace_id: str = None,
        role: str = "user",
        active: bool = True
    ) -> DBWorkspaceMember:
        """Create a DB workspace member for testing"""
        return DBWorkspaceMember(
            id=id or str(uuid.uuid4()),
            user_id=user_id or str(uuid.uuid4()),
            workspace_id=workspace_id or str(uuid.uuid4()),
            role=role,
            active=active,
            joined_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

