"""
Cache Headers Utilities
Helpers for adding ETag and Last-Modified headers for HTTP caching
"""
import hashlib
import json
from typing import Any, Optional
from datetime import datetime
from fastapi import Response
from pydantic import BaseModel


def generate_etag(data: Any) -> str:
    """
    Generate ETag from data.
    
    Creates a hash-based ETag for resource versioning.
    Clients can use this with If-None-Match header for conditional requests.
    
    Args:
        data: Data to hash (dict, BaseModel, or any JSON-serializable object)
    
    Returns:
        ETag string (quoted, e.g., '"abc123"')
    
    Example:
        >>> user_data = {"id": "123", "name": "John", "email": "john@example.com"}
        >>> etag = generate_etag(user_data)
        >>> print(etag)  # '"5d41402abc4b2a76b9719d911017c592"'
    """
    # Convert to JSON string for hashing
    if isinstance(data, BaseModel):
        json_str = data.json(sort_keys=True)
    elif isinstance(data, dict):
        json_str = json.dumps(data, sort_keys=True, default=str)
    elif isinstance(data, (list, tuple)):
        json_str = json.dumps(data, default=str)
    else:
        json_str = str(data)
    
    # Generate MD5 hash
    hash_obj = hashlib.md5(json_str.encode())
    etag = hash_obj.hexdigest()
    
    # Return quoted ETag (HTTP spec)
    return f'"{etag}"'


def add_etag_header(response: Response, data: Any) -> None:
    """
    Add ETag header to response.
    
    Args:
        response: FastAPI Response object
        data: Data to generate ETag from
    
    Example:
        >>> @router.get("/users/{user_id}")
        >>> async def get_user(user_id: str, response: Response):
        ...     user = await get_user_by_id(user_id)
        ...     add_etag_header(response, user)
        ...     return user
    """
    etag = generate_etag(data)
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-cache"  # Validate with server


def add_last_modified_header(response: Response, last_modified: datetime) -> None:
    """
    Add Last-Modified header to response.
    
    Clients can use this with If-Modified-Since header for conditional requests.
    
    Args:
        response: FastAPI Response object
        last_modified: Datetime when resource was last modified
    
    Example:
        >>> @router.get("/users/{user_id}")
        >>> async def get_user(user_id: str, response: Response):
        ...     user = await get_user_by_id(user_id)
        ...     add_last_modified_header(response, user.updated_at)
        ...     return user
    """
    # Format as HTTP date (RFC 7231)
    http_date = last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.headers["Last-Modified"] = http_date


def add_cache_headers(
    response: Response,
    data: Any,
    last_modified: Optional[datetime] = None,
    max_age: Optional[int] = None
) -> None:
    """
    Add comprehensive cache headers to response.
    
    Adds ETag, Last-Modified, and Cache-Control headers.
    
    Args:
        response: FastAPI Response object
        data: Data to generate ETag from
        last_modified: Optional datetime when resource was last modified
        max_age: Optional max-age in seconds for Cache-Control
    
    Example:
        >>> @router.get("/users/{user_id}")
        >>> async def get_user(user_id: str, response: Response):
        ...     user = await get_user_by_id(user_id)
        ...     add_cache_headers(
        ...         response,
        ...         data=user,
        ...         last_modified=user.updated_at,
        ...         max_age=300  # Cache for 5 minutes
        ...     )
        ...     return user
    """
    # Add ETag
    add_etag_header(response, data)
    
    # Add Last-Modified if provided
    if last_modified:
        add_last_modified_header(response, last_modified)
    
    # Set Cache-Control
    if max_age is not None:
        response.headers["Cache-Control"] = f"max-age={max_age}, must-revalidate"
    else:
        response.headers["Cache-Control"] = "no-cache"


def check_if_none_match(request_etag: Optional[str], current_etag: str) -> bool:
    """
    Check if If-None-Match header matches current ETag.
    
    Returns True if ETags match (resource not modified).
    
    Args:
        request_etag: ETag from If-None-Match header
        current_etag: Current resource ETag
    
    Returns:
        True if ETags match (return 304 Not Modified)
    
    Example:
        >>> @router.get("/users/{user_id}")
        >>> async def get_user(
        ...     user_id: str,
        ...     response: Response,
        ...     if_none_match: Optional[str] = Header(None)
        ... ):
        ...     user = await get_user_by_id(user_id)
        ...     current_etag = generate_etag(user)
        ...     
        ...     if check_if_none_match(if_none_match, current_etag):
        ...         return Response(status_code=304)  # Not Modified
        ...     
        ...     add_etag_header(response, user)
        ...     return user
    """
    if not request_etag:
        return False
    
    # Handle multiple ETags in If-None-Match
    request_etags = [tag.strip() for tag in request_etag.split(",")]
    return current_etag in request_etags or "*" in request_etags


def check_if_modified_since(
    request_date: Optional[datetime],
    last_modified: datetime
) -> bool:
    """
    Check if resource was modified since If-Modified-Since date.
    
    Returns True if resource was modified (return new content).
    
    Args:
        request_date: Datetime from If-Modified-Since header
        last_modified: Resource's last modified datetime
    
    Returns:
        True if resource was modified since request date
    
    Example:
        >>> from fastapi import Header
        >>> 
        >>> @router.get("/users/{user_id}")
        >>> async def get_user(
        ...     user_id: str,
        ...     if_modified_since: Optional[datetime] = Header(None)
        ... ):
        ...     user = await get_user_by_id(user_id)
        ...     
        ...     if not check_if_modified_since(if_modified_since, user.updated_at):
        ...         return Response(status_code=304)  # Not Modified
        ...     
        ...     return user
    """
    if not request_date:
        return True
    
    # Compare timestamps (ignore microseconds)
    return last_modified.replace(microsecond=0) > request_date.replace(microsecond=0)

