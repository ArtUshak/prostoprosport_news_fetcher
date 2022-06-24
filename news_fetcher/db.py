"""Database common functions."""
import os

import tortoise


async def init_db() -> None:
    await tortoise.Tortoise.init(
        db_url=os.getenv('DATABASE_URL'),
        modules={'models': ['models']}
    )
    await tortoise.Tortoise.generate_schemas()
