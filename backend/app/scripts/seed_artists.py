"""
Seed script — 将 18 位画家池灌入 PostgreSQL artists 表

用法（在服务器 /opt/dream-recorder/backend 执行）:
  source venv/bin/activate
  python -m app.scripts.seed_artists
"""
import asyncio
import sys
import os

# 确保 app 能被 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import async_session, engine, Base
from app.models.models import Artist
from sqlalchemy import select

OSS_ARTIST_BASE = "https://dream-recorder-media.oss-ap-southeast-5.aliyuncs.com/artists"

SEED_ARTISTS = [
    # 超现实主义核心
    {"key": "DALI", "name": "Salvador Dalí", "style": "melting forms, warped time-space, impossibly detailed renderings of impossible things, soft clocks dripping", "masterwork_url": f"{OSS_ARTIST_BASE}/dali/masterwork.jpg", "painting": "The Persistence of Memory", "category": "surrealism_core", "sort_order": 1},
    {"key": "MAGRITTE", "name": "René Magritte", "style": "calm paradoxes in impossible situations, philosophical mystery, uncanny stillness, objects defying logic", "masterwork_url": f"{OSS_ARTIST_BASE}/magritte/masterwork.jpg", "painting": "The Son of Man", "category": "surrealism_core", "sort_order": 2},
    {"key": "ERNST", "name": "Max Ernst", "style": "collage textures, organic alien forms, jungle-like otherworlds, frottage surfaces, biomorphic strangeness", "masterwork_url": f"{OSS_ARTIST_BASE}/ernst/masterwork.jpg", "painting": "The Elephant Celebes", "category": "surrealism_core", "sort_order": 3},
    {"key": "VARO", "name": "Remedios Varo", "style": "alchemical machinery, spiral architecture, feminine mysticism, mechanical dreamscapes, intricate vessels", "masterwork_url": f"{OSS_ARTIST_BASE}/varo/masterwork.jpg", "painting": "Creation of the Birds", "category": "surrealism_core", "sort_order": 4},
    {"key": "CARRINGTON", "name": "Leonora Carrington", "style": "magical creatures, Celtic mythology, alchemical dreamscapes, hybrid beings, enchanted interiors", "masterwork_url": f"{OSS_ARTIST_BASE}/carrington/masterwork.jpg", "painting": "Self-Portrait (Inn of the Dawn Horse)", "category": "surrealism_core", "sort_order": 5},
    # 表现主义/情绪扭曲
    {"key": "MUNCH", "name": "Edvard Munch", "style": "emotions distorting reality, expressionist anxiety screaming through color, undulating forms, raw psychic energy", "masterwork_url": f"{OSS_ARTIST_BASE}/munch/masterwork.jpg", "painting": "The Scream", "category": "expressionism", "sort_order": 1},
    {"key": "SCHIELE", "name": "Egon Schiele", "style": "twisted bodies, raw emotional linework, exposed vulnerability, angular tension, nervous energy", "masterwork_url": f"{OSS_ARTIST_BASE}/schiele/masterwork.jpg", "painting": "Self-Portrait with Physalis", "category": "expressionism", "sort_order": 2},
    {"key": "BACON", "name": "Francis Bacon", "style": "distorted flesh, caged screaming forms, violent blurring, visceral smeared humanity, existential horror", "masterwork_url": f"{OSS_ARTIST_BASE}/bacon/masterwork.jpg", "painting": "Study after Velázquez's Portrait of Pope Innocent X", "category": "expressionism", "sort_order": 3},
    # 诗意梦幻/失重
    {"key": "CHAGALL", "name": "Marc Chagall", "style": "weightless floating, jewel-tone colors, poetic tenderness bathed in stained-glass light, lovers drifting above villages", "masterwork_url": f"{OSS_ARTIST_BASE}/chagall/masterwork.jpg", "painting": "I and the Village", "category": "poetic_weightless", "sort_order": 1},
    {"key": "REDON", "name": "Odilon Redon", "style": "pastel dreamscapes, floating eyeballs, faces emerging from flowers, luminous color fields, soft numinous forms", "masterwork_url": f"{OSS_ARTIST_BASE}/redon/masterwork.jpg", "painting": "The Cyclops", "category": "poetic_weightless", "sort_order": 2},
    {"key": "KLIMT", "name": "Gustav Klimt", "style": "gold-leaf ornamentation, erotic patterning, Byzantine dream surfaces, mosaic-like skin, decorative ecstasy", "masterwork_url": f"{OSS_ARTIST_BASE}/klimt/masterwork.jpg", "painting": "The Kiss", "category": "poetic_weightless", "sort_order": 3},
    {"key": "MUCHA", "name": "Alphonse Mucha", "style": "Art Nouveau flowing lines, floral halos, soft luminous glow, ornamental feminine silhouettes, circular compositions", "masterwork_url": f"{OSS_ARTIST_BASE}/mucha/masterwork.jpg", "painting": "Job", "category": "poetic_weightless", "sort_order": 4},
    # 神秘/象征主义
    {"key": "BOSCH", "name": "Hieronymus Bosch", "style": "hellish fantasy, densely packed creatures, medieval nightmare imagery, bizarre hybrid beings, teeming surreal detail", "masterwork_url": f"{OSS_ARTIST_BASE}/bosch/masterwork.jpg", "painting": "The Garden of Earthly Delights", "category": "mystical_symbolism", "sort_order": 1},
    {"key": "BLAKE", "name": "William Blake", "style": "divine visions, muscular angels, cosmic radiance, prophetic illumination, spiritual enormity", "masterwork_url": f"{OSS_ARTIST_BASE}/blake/masterwork.jpg", "painting": "The Ancient of Days", "category": "mystical_symbolism", "sort_order": 2},
    {"key": "BEKSINSKI", "name": "Zdzisław Beksiński", "style": "bone-like architecture, apocalyptic wastelands, organic horror beauty, skeletal cathedrals, amber decay", "masterwork_url": f"{OSS_ARTIST_BASE}/beksinski/masterwork.jpg", "painting": "Untitled (1984)", "category": "mystical_symbolism", "sort_order": 3},
    # 现代梦境/数字感
    {"key": "KUSAMA", "name": "Yayoi Kusama", "style": "infinite polka dots, mirrored infinity rooms, cosmic endless repetition, obsessive patterning, dissolving self into universe", "masterwork_url": f"{OSS_ARTIST_BASE}/kusama/masterwork.jpg", "painting": "Pumpkin", "category": "modern_dream", "sort_order": 1},
    {"key": "DE_CHIRICO", "name": "Giorgio de Chirico", "style": "metaphysical empty plazas, long impossible shadows, architectural unease, melancholic stillness, enigmatic mannequins", "masterwork_url": f"{OSS_ARTIST_BASE}/de_chirico/masterwork.jpg", "painting": "The Disquieting Muses", "category": "modern_dream", "sort_order": 2},
    {"key": "SAGE", "name": "Kay Sage", "style": "desolate geometric dreamscapes, draped architectural forms, grey-toned silence, angular fabric structures, lonely horizons", "masterwork_url": f"{OSS_ARTIST_BASE}/sage/masterwork.jpg", "painting": "Tomorrow is Never", "category": "modern_dream", "sort_order": 3},
]


async def seed():
    # 建表（如果不存在）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        for data in SEED_ARTISTS:
            # 检查是否已存在
            existing = await session.scalar(
                select(Artist).where(Artist.key == data["key"])
            )
            if existing:
                # 更新已有记录
                for field, value in data.items():
                    setattr(existing, field, value)
                print(f"  Updated: {data['key']} ({data['name']})")
            else:
                # 插入新记录
                artist = Artist(**data, active=True)
                session.add(artist)
                print(f"  Created: {data['key']} ({data['name']})")

        await session.commit()
        print(f"\nDone! {len(SEED_ARTISTS)} artists seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
