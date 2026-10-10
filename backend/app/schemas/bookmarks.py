from datetime import datetime
from typing import Literal

from pydantic import BaseModel

BookmarkType = Literal["verse", "hadith", "dua"]


class BookmarkCreate(BaseModel):
    type: BookmarkType
    target_id: int


class BookmarkOut(BaseModel):
    id: int
    type: BookmarkType
    target_id: int
    created_at: datetime
