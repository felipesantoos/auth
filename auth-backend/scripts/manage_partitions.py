#!/usr/bin/env python3
"""
Partition Management Script
Manage PostgreSQL table partitions for audit_log table

Usage:
    python scripts/manage_partitions.py create-next      # Create next month's partition
    python scripts/manage_partitions.py list             # List all partitions
    python scripts/manage_partitions.py drop-old --months 24   # Drop partitions older than 24 months
"""
import asyncio
import sys
from datetime import datetime, timedelta
from typing import List, Dict
import argparse

# Add parent directory to path
sys.path.insert(0, '.')

from sqlalchemy import text
from infra.database.database import AsyncSessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PartitionManager:
    """Manages database table partitions for audit logs"""
    
    def __init__(self):
        self.table_name = "audit_log"
    
    async def create_next_partition(self) -> str:
        """
        Create partition for next month.
        
        Returns:
            Name of created partition
        """
        async with AsyncSessionLocal() as session:
            try:
                # Calculate next month
                next_month = datetime.now().replace(day=1) + timedelta(days=32)
                next_month = next_month.replace(day=1)
                month_after = (next_month + timedelta(days=32)).replace(day=1)
                
                # Generate partition name
                partition_name = f"audit_log_{next_month.strftime('%Y_%m')}"
                
                # Create partition
                create_sql = f"""
                CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF {self.table_name}
                FOR VALUES FROM ('{next_month.strftime('%Y-%m-%d')}') 
                TO ('{month_after.strftime('%Y-%m-%d')}')
                """
                
                await session.execute(text(create_sql))
                
                # Create indexes
                indexes = [
                    f"CREATE INDEX IF NOT EXISTS idx_{partition_name}_user_id ON {partition_name}(user_id)",
                    f"CREATE INDEX IF NOT EXISTS idx_{partition_name}_client_id ON {partition_name}(client_id)",
                    f"CREATE INDEX IF NOT EXISTS idx_{partition_name}_user_event ON {partition_name}(user_id, event_type)",
                    f"CREATE INDEX IF NOT EXISTS idx_{partition_name}_entity ON {partition_name}(resource_type, resource_id)",
                    f"CREATE INDEX IF NOT EXISTS idx_{partition_name}_category ON {partition_name}(event_category)",
                ]
                
                for index_sql in indexes:
                    await session.execute(text(index_sql))
                
                await session.commit()
                
                logger.info(f"✓ Created partition: {partition_name}")
                logger.info(f"  Range: {next_month.strftime('%Y-%m-%d')} to {month_after.strftime('%Y-%m-%d')}")
                
                return partition_name
                
            except Exception as e:
                logger.error(f"✗ Error creating partition: {e}")
                await session.rollback()
                raise
    
    async def list_partitions(self) -> List[Dict]:
        """
        List all existing partitions.
        
        Returns:
            List of partition info dicts
        """
        async with AsyncSessionLocal() as session:
            try:
                query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                        pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
                    FROM pg_tables
                    WHERE tablename LIKE 'audit_log_%'
                    AND tablename NOT LIKE 'audit_log_old'
                    ORDER BY tablename DESC
                """)
                
                result = await session.execute(query)
                partitions = []
                
                print("\n📊 Audit Log Partitions:\n")
                print(f"{'Partition Name':<30} {'Size':<15} {'Size (bytes)':<15}")
                print("-" * 60)
                
                for row in result:
                    partition_info = {
                        "schema": row.schemaname,
                        "name": row.tablename,
                        "size": row.size,
                        "size_bytes": row.size_bytes
                    }
                    partitions.append(partition_info)
                    print(f"{row.tablename:<30} {row.size:<15} {row.size_bytes:<15,}")
                
                print(f"\nTotal partitions: {len(partitions)}\n")
                
                return partitions
                
            except Exception as e:
                logger.error(f"✗ Error listing partitions: {e}")
                raise
    
    async def drop_old_partitions(self, months_old: int = 24, dry_run: bool = True) -> List[str]:
        """
        Drop partitions older than specified months.
        
        WARNING: This deletes data! Make sure data is archived first!
        
        Args:
            months_old: Drop partitions older than this (default: 24 months)
            dry_run: If True, only show what would be dropped (don't actually drop)
            
        Returns:
            List of dropped partition names
        """
        async with AsyncSessionLocal() as session:
            try:
                # Calculate cutoff date
                cutoff_date = datetime.now() - timedelta(days=months_old * 30)
                cutoff_date = cutoff_date.replace(day=1)
                
                # Find partitions to drop
                query = text("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE tablename LIKE 'audit_log_%'
                    AND tablename NOT LIKE 'audit_log_old'
                    ORDER BY tablename
                """)
                
                result = await session.execute(query)
                all_partitions = [row.tablename for row in result]
                
                dropped = []
                
                for partition_name in all_partitions:
                    # Extract date from partition name (e.g., audit_log_2023_01)
                    try:
                        parts = partition_name.replace("audit_log_", "").split("_")
                        year = int(parts[0])
                        month = int(parts[1])
                        partition_date = datetime(year, month, 1)
                        
                        if partition_date < cutoff_date:
                            if dry_run:
                                logger.info(f"[DRY RUN] Would drop: {partition_name} ({partition_date.strftime('%Y-%m')})")
                            else:
                                drop_sql = f"DROP TABLE IF EXISTS {partition_name}"
                                await session.execute(text(drop_sql))
                                logger.warning(f"✓ Dropped partition: {partition_name}")
                            
                            dropped.append(partition_name)
                    
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse partition date from: {partition_name}")
                        continue
                
                if not dry_run:
                    await session.commit()
                
                print(f"\n{'DRY RUN: ' if dry_run else ''}Dropped {len(dropped)} partition(s) older than {months_old} months")
                
                return dropped
                
            except Exception as e:
                logger.error(f"✗ Error dropping partitions: {e}")
                await session.rollback()
                raise
    
    async def get_partition_stats(self) -> Dict:
        """
        Get statistics about partitions.
        
        Returns:
            Stats dict with counts and sizes
        """
        async with AsyncSessionLocal() as session:
            try:
                # Total size across all partitions
                query = text("""
                    SELECT 
                        COUNT(*) as partition_count,
                        pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) AS total_size,
                        SUM(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size_bytes
                    FROM pg_tables
                    WHERE tablename LIKE 'audit_log_%'
                    AND tablename NOT LIKE 'audit_log_old'
                """)
                
                result = await session.execute(query)
                row = result.first()
                
                stats = {
                    "partition_count": row.partition_count,
                    "total_size": row.total_size,
                    "total_size_bytes": row.total_size_bytes
                }
                
                print(f"\n📈 Partition Statistics:")
                print(f"  Total Partitions: {stats['partition_count']}")
                print(f"  Total Size: {stats['total_size']}")
                print()
                
                return stats
                
            except Exception as e:
                logger.error(f"✗ Error getting partition stats: {e}")
                raise


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Manage audit_log table partitions")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # create-next command
    subparsers.add_parser("create-next", help="Create next month's partition")
    
    # list command
    subparsers.add_parser("list", help="List all partitions")
    
    # drop-old command
    drop_parser = subparsers.add_parser("drop-old", help="Drop old partitions")
    drop_parser.add_argument("--months", type=int, default=24, help="Drop partitions older than N months")
    drop_parser.add_argument("--confirm", action="store_true", help="Actually drop (not dry-run)")
    
    # stats command
    subparsers.add_parser("stats", help="Show partition statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = PartitionManager()
    
    try:
        if args.command == "create-next":
            partition_name = await manager.create_next_partition()
            print(f"\n✓ Successfully created partition: {partition_name}\n")
        
        elif args.command == "list":
            await manager.list_partitions()
        
        elif args.command == "drop-old":
            dry_run = not args.confirm
            if not dry_run:
                confirm = input(f"\n⚠️  WARNING: This will DROP partitions older than {args.months} months!\nType 'yes' to confirm: ")
                if confirm != "yes":
                    print("Cancelled.")
                    return
            
            dropped = await manager.drop_old_partitions(
                months_old=args.months,
                dry_run=dry_run
            )
            
            if dry_run:
                print("\n💡 Use --confirm to actually drop partitions\n")
        
        elif args.command == "stats":
            await manager.get_partition_stats()
        
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

