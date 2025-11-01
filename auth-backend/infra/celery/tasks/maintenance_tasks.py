"""
Maintenance Tasks
Periodic background tasks for system cleanup and maintenance
"""
import logging
import asyncio
from datetime import datetime, timedelta

from infra.celery.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name='cleanup_expired_sessions')
def cleanup_expired_sessions_task():
    """
    Cleanup expired user sessions.
    
    Runs daily at 3:00 AM.
    Removes sessions that have expired or been revoked.
    """
    try:
        logger.info("[Celery] Starting expired sessions cleanup")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_cleanup_expired_sessions())
        loop.close()
        
        logger.info(f"[Celery] Expired sessions cleanup completed: {result}")
        return result
    
    except Exception as e:
        logger.error(f"[Celery] Expired sessions cleanup failed: {e}", exc_info=True)
        raise


async def _cleanup_expired_sessions():
    """Async implementation of expired sessions cleanup"""
    from infra.database.database import AsyncSessionLocal
    from infra.database.models.user_session import DBUserSession
    from sqlalchemy import delete
    
    deleted_count = 0
    
    async with AsyncSessionLocal() as session:
        try:
            now = datetime.utcnow()
            
            # Delete sessions that are expired or revoked
            stmt = delete(DBUserSession).where(
                (DBUserSession.expires_at < now) |
                (DBUserSession.revoked_at.isnot(None))
            )
            
            result = await session.execute(stmt)
            deleted_count = result.rowcount
            await session.commit()
            
            logger.info(f"[Maintenance] Deleted {deleted_count} expired sessions")
        
        except Exception as e:
            logger.error(f"[Maintenance] Error cleaning expired sessions: {e}", exc_info=True)
            await session.rollback()
            raise
    
    return {
        "status": "success",
        "deleted_sessions": deleted_count,
        "timestamp": datetime.utcnow().isoformat()
    }


@celery_app.task(name='cleanup_expired_tokens')
def cleanup_expired_tokens_task():
    """
    Cleanup expired password reset and email verification tokens.
    
    Runs daily at 2:00 AM.
    Clears tokens that are older than 24 hours.
    """
    try:
        logger.info("[Celery] Starting expired tokens cleanup")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_cleanup_expired_tokens())
        loop.close()
        
        logger.info(f"[Celery] Expired tokens cleanup completed: {result}")
        return result
    
    except Exception as e:
        logger.error(f"[Celery] Expired tokens cleanup failed: {e}", exc_info=True)
        raise


async def _cleanup_expired_tokens():
    """Async implementation of expired tokens cleanup"""
    from infra.database.database import AsyncSessionLocal
    from infra.database.models.app_user import DBAppUser
    from sqlalchemy import update
    
    cleaned_count = 0
    
    async with AsyncSessionLocal() as session:
        try:
            # Clear expired email verification tokens (older than 24h)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            stmt = update(DBAppUser).where(
                DBAppUser.email_verification_sent_at < cutoff_time
            ).values(
                email_verification_token=None,
                email_verification_sent_at=None
            )
            
            result = await session.execute(stmt)
            email_tokens_cleared = result.rowcount
            
            # Clear expired magic link tokens (older than 15 minutes)
            magic_link_cutoff = datetime.utcnow() - timedelta(minutes=15)
            
            stmt = update(DBAppUser).where(
                DBAppUser.magic_link_sent_at < magic_link_cutoff
            ).values(
                magic_link_token=None,
                magic_link_sent_at=None
            )
            
            result = await session.execute(stmt)
            magic_tokens_cleared = result.rowcount
            
            cleaned_count = email_tokens_cleared + magic_tokens_cleared
            
            await session.commit()
            
            logger.info(
                f"[Maintenance] Cleared {email_tokens_cleared} email verification tokens "
                f"and {magic_tokens_cleared} magic link tokens"
            )
        
        except Exception as e:
            logger.error(f"[Maintenance] Error cleaning expired tokens: {e}", exc_info=True)
            await session.rollback()
            raise
    
    return {
        "status": "success",
        "cleared_tokens": cleaned_count,
        "timestamp": datetime.utcnow().isoformat()
    }


@celery_app.task(name='cleanup_old_audit_logs')
def cleanup_old_audit_logs_task(retention_days: int = 90):
    """
    Cleanup old audit logs.
    
    Runs weekly on Sunday at 4:00 AM.
    Removes audit logs older than retention period (default: 90 days).
    
    Args:
        retention_days: Number of days to retain audit logs (default: 90)
    """
    try:
        logger.info(f"[Celery] Starting old audit logs cleanup (retention: {retention_days} days)")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_cleanup_old_audit_logs(retention_days))
        loop.close()
        
        logger.info(f"[Celery] Old audit logs cleanup completed: {result}")
        return result
    
    except Exception as e:
        logger.error(f"[Celery] Old audit logs cleanup failed: {e}", exc_info=True)
        raise


async def _cleanup_old_audit_logs(retention_days: int = 90):
    """Async implementation of old audit logs cleanup"""
    from infra.database.database import AsyncSessionLocal
    from infra.database.models.audit_log import DBAuditLog
    from sqlalchemy import delete
    
    deleted_count = 0
    
    async with AsyncSessionLocal() as session:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Delete audit logs older than retention period
            stmt = delete(DBAuditLog).where(
                DBAuditLog.created_at < cutoff_date
            )
            
            result = await session.execute(stmt)
            deleted_count = result.rowcount
            await session.commit()
            
            logger.info(
                f"[Maintenance] Deleted {deleted_count} audit logs older than {retention_days} days"
            )
        
        except Exception as e:
            logger.error(f"[Maintenance] Error cleaning old audit logs: {e}", exc_info=True)
            await session.rollback()
            raise
    
    return {
        "status": "success",
        "deleted_logs": deleted_count,
        "retention_days": retention_days,
        "timestamp": datetime.utcnow().isoformat()
    }


@celery_app.task(name='cleanup_expired_api_keys')
def cleanup_expired_api_keys_task():
    """
    Cleanup expired API keys.
    
    Runs daily at 1:00 AM.
    Removes API keys that have expired.
    """
    try:
        logger.info("[Celery] Starting expired API keys cleanup")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_cleanup_expired_api_keys())
        loop.close()
        
        logger.info(f"[Celery] Expired API keys cleanup completed: {result}")
        return result
    
    except Exception as e:
        logger.error(f"[Celery] Expired API keys cleanup failed: {e}", exc_info=True)
        raise


async def _cleanup_expired_api_keys():
    """Async implementation of expired API keys cleanup"""
    from infra.database.database import AsyncSessionLocal
    from infra.database.models.api_key import DBApiKey
    from sqlalchemy import delete
    
    deleted_count = 0
    
    async with AsyncSessionLocal() as session:
        try:
            now = datetime.utcnow()
            
            # Delete expired API keys
            stmt = delete(DBApiKey).where(
                (DBApiKey.expires_at < now) & 
                (DBApiKey.expires_at.isnot(None))
            )
            
            result = await session.execute(stmt)
            deleted_count = result.rowcount
            await session.commit()
            
            logger.info(f"[Maintenance] Deleted {deleted_count} expired API keys")
        
        except Exception as e:
            logger.error(f"[Maintenance] Error cleaning expired API keys: {e}", exc_info=True)
            await session.rollback()
            raise
    
    return {
        "status": "success",
        "deleted_api_keys": deleted_count,
        "timestamp": datetime.utcnow().isoformat()
    }

