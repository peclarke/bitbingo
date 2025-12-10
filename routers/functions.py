import duckdb
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from database import create_new_bingo_game
from utils import get_db
from log import logger

router = APIRouter(prefix="/api")

class Click(BaseModel):
    clicks: int
    user_id: int

@router.post("/clicks")
async def clicks(clicks: Click):
    # body = await request.body()
    # print(clicks)
    # foo = request.get("clicks")
    # print(dict(body))
    pass

@router.post("/newgame")
async def newgame(_: Request, con: duckdb.DuckDBPyConnection = Depends(get_db)):
    create_new_bingo_game(con)
    logger.info("New bingo game created")
    return "done"

@router.post("/resetcurrent")
async def resetgame(_: Request, con: duckdb.DuckDBPyConnection = Depends(get_db)):
    pass