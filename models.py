from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class CustomBaseModel(BaseModel):
    @classmethod
    def from_list(cls, tpl):
        return cls(**{k: v for k, v in zip(cls.model_fields.keys(), tpl)})

class User(CustomBaseModel):
    id: Optional[int] = None
    username: str
    prof_img_url: Optional[str] = None
    is_admin: bool = False
    points: int = 0
    number_games_won: int = 0
    is_activated: bool = False
    created_at: Optional[datetime] = None


class Bingo(CustomBaseModel):
    id: Optional[int] = None
    completed: bool = False
    victor: Optional[int] = None  # FK -> users.id
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class UserBingoProgress(CustomBaseModel):
    user_id: int        # FK -> users.id
    bingo_id: int       # FK -> bingo.id
    completed_index: int


class UserWin(CustomBaseModel):
    user_id: int        # FK -> users.id
    bingo_id: int       # FK -> bingo.id


class UserGameClicks(CustomBaseModel):
    user_id: int        # FK -> users.id
    bingo_id: int       # FK -> bingo.id
    clicks: int = 1


class Prompt(CustomBaseModel):
    bingo_game: int     # FK -> bingo.id
    idx: int            # [0, 16] position on the board
    prompt: str
    created_at: Optional[datetime] = None
