"""Database common functions."""
import os
from typing import Optional

import tortoise


async def init_db(db_url: Optional[str] = None) -> None:
    await tortoise.Tortoise.init(
        db_url=db_url or os.getenv('DATABASE_URL'),
        modules={'models': ['models']}
    )
    await tortoise.Tortoise.generate_schemas()
