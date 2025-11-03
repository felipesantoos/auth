"""
Workspace Domain Model
Represents a workspace/organization in the system
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from core.exceptions import MissingRequiredFieldException, InvalidValueException
import re


@dataclass
class Workspace:
    """
    Domain model for workspace (organization/company/group).
    
    This is pure business logic with no framework dependencies.
    A workspace represents a team, company, or organization.
    Users can belong to multiple workspaces with different roles.
    """
    id: Optional[str]
    name: str
    slug: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """
        Validate workspace according to business rules.
        
        Raises:
            MissingRequiredFieldException: If required fields are missing
            InvalidValueException: If field values are invalid
        """
        # Required fields
        if not self.name or not self.name.strip():
            raise MissingRequiredFieldException("name")
        
        if not self.slug or not self.slug.strip():
            raise MissingRequiredFieldException("slug")
        
        # Name length
        if len(self.name) < 2:
            raise InvalidValueException("name", self.name, "must be at least 2 characters")
        
        if len(self.name) > 200:
            raise InvalidValueException("name", self.name, "must not exceed 200 characters")
        
        # Slug validation
        if len(self.slug) < 2:
            raise InvalidValueException("slug", self.slug, "must be at least 2 characters")
        
        if len(self.slug) > 100:
            raise InvalidValueException("slug", self.slug, "must not exceed 100 characters")
        
        # Slug should be lowercase alphanumeric with hyphens and underscores
        slug_pattern = r'^[a-z0-9_-]+$'
        if not re.match(slug_pattern, self.slug):
            raise InvalidValueException(
                "slug", 
                self.slug, 
                "can only contain lowercase letters, numbers, hyphens, and underscores"
            )
        
        # Description length (if provided)
        if self.description and len(self.description) > 1000:
            raise InvalidValueException(
                "description", 
                self.description, 
                "must not exceed 1000 characters"
            )
    
    def activate(self) -> None:
        """Business operation to activate workspace"""
        self.active = True
    
    def deactivate(self) -> None:
        """Business operation to deactivate workspace"""
        self.active = False
    
    def update_name(self, new_name: str) -> None:
        """
        Update workspace name with validation.
        
        Args:
            new_name: New workspace name
            
        Raises:
            MissingRequiredFieldException: If name is empty
            InvalidValueException: If name is invalid
        """
        if not new_name or not new_name.strip():
            raise MissingRequiredFieldException("name")
        
        if len(new_name) < 2 or len(new_name) > 200:
            raise InvalidValueException("name", new_name, "must be between 2 and 200 characters")
        
        self.name = new_name
    
    def update_slug(self, new_slug: str) -> None:
        """
        Update workspace slug with validation.
        
        Args:
            new_slug: New workspace slug
            
        Raises:
            MissingRequiredFieldException: If slug is empty
            InvalidValueException: If slug is invalid
        """
        if not new_slug or not new_slug.strip():
            raise MissingRequiredFieldException("slug")
        
        if len(new_slug) < 2 or len(new_slug) > 100:
            raise InvalidValueException("slug", new_slug, "must be between 2 and 100 characters")
        
        slug_pattern = r'^[a-z0-9_-]+$'
        if not re.match(slug_pattern, new_slug):
            raise InvalidValueException(
                "slug",
                new_slug,
                "can only contain lowercase letters, numbers, hyphens, and underscores"
            )
        
        self.slug = new_slug
    
    def update_description(self, new_description: Optional[str]) -> None:
        """
        Update workspace description.
        
        Args:
            new_description: New description (can be None)
        """
        if new_description and len(new_description) > 1000:
            raise InvalidValueException("description", new_description, "must not exceed 1000 characters")
        
        self.description = new_description
    
    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """
        Update workspace settings.
        
        Args:
            new_settings: New settings dictionary
        """
        self.settings = new_settings
    
    @staticmethod
    def generate_slug_from_name(name: str) -> str:
        """
        Generate a URL-friendly slug from workspace name.
        
        Args:
            name: Workspace name
            
        Returns:
            Generated slug
        """
        # Convert to lowercase
        slug = name.lower()
        
        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        
        # Strip hyphens from start and end
        slug = slug.strip('-')
        
        return slug[:100]  # Limit to max length

