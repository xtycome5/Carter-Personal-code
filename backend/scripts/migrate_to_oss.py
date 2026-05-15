"""
迁移脚本：将现有 generation.result_url (DashScope 临时链接) 迁移到 OSS 永久存储

使用方法：
  cd /opt/dream-recorder/backend
  source venv/bin/activate
  python -m scripts.migrate_to_oss

原理：
  1. 查询所有 status=completed 且 result_url 不为空的 generation 记录
  2. 跳过已经是 OSS URL 的记录
  3. 尝试下载临时 URL → 上传到 OSS → 更新 DB
  4. 如果下载失败（已过期），标记并跳过
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.storage_service import oss_storage_service


async def migrate():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select, text

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    if not oss_storage_service.enabled:
        print("ERROR: OSS is not configured. Set OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME in .env")
        return

    async with async_session() as session:
        # Get all completed generations with result_url
        result = await session.execute(
            text("""
                SELECT id, user_id, type, result_url
                FROM generations
                WHERE status = 'completed'
                  AND result_url IS NOT NULL
                  AND result_url != ''
                ORDER BY created_at DESC
            """)
        )
        rows = result.fetchall()
        
        total = len(rows)
        migrated = 0
        skipped = 0
        failed = 0

        print(f"Found {total} completed generations to check")
        print(f"OSS Bucket: {settings.OSS_BUCKET_NAME}")
        print(f"OSS Endpoint: {settings.OSS_ENDPOINT}")
        print("-" * 60)

        for row in rows:
            gen_id, user_id, gen_type, result_url = str(row[0]), str(row[1]), row[2], row[3]

            # Skip if already on OSS
            if settings.OSS_BUCKET_NAME in result_url:
                skipped += 1
                continue

            # Try to persist
            print(f"[{migrated + failed + 1}/{total - skipped}] {gen_type} {gen_id[:8]}... ", end="")
            
            permanent_url = await oss_storage_service.persist(
                temp_url=result_url,
                user_id=user_id,
                generation_id=gen_id,
                media_type=gen_type,
            )

            if permanent_url:
                # Update DB
                await session.execute(
                    text("UPDATE generations SET result_url = :url WHERE id = :id"),
                    {"url": permanent_url, "id": gen_id},
                )
                migrated += 1
                print(f"OK -> {permanent_url[:60]}...")
            else:
                failed += 1
                print("FAILED (expired or download error)")

        await session.commit()
        
        print("-" * 60)
        print(f"Done! Migrated: {migrated}, Skipped (already OSS): {skipped}, Failed: {failed}")


if __name__ == "__main__":
    asyncio.run(migrate())
