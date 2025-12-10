from typing import List
import duckdb
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from database import get_all_bingo_games, get_all_current_prompts, get_all_usernames, get_bingo_game, get_completed_bingo_prompts_for_user, get_count_of_completed_prompts, get_game_winner, get_user_info_by_username, get_username_by_id, handle_victor, is_user_admin, set_completed_prompts_for_user
from models import Bingo, User
from utils import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
@router.post("/")
async def homepage(request: Request, con: duckdb.DuckDBPyConnection = Depends(get_db)):
    isMyWin = False # only updates after you win after submitting a prompt change

    currentGame: Bingo = get_bingo_game(con)
    myCompletedPrompts = get_completed_bingo_prompts_for_user(con, currentGame.id, 1)

    if (request.method == "POST"):
        # handle selection of indexes
        formData = await request.form()
        selected = formData.get('selected')
        if selected is not None:
            if len(selected) == 0:
                isMyWin = set_completed_prompts_for_user(con, currentGame.id, 1, [])
                # set to new completed prompts
                myCompletedPrompts = []
            else:
                # convert to integer list
                indexesStr = selected.split(",")
                indexes = [int(x) for x in indexesStr]

                isMyWin = set_completed_prompts_for_user(con, currentGame.id, 1, indexes)
                # set to new completed prompts
                myCompletedPrompts = indexes

            # handle the victory if in fact the last prompt was the user's winning one
            if isMyWin:
                # update the game variables
                currentGame: Bingo = get_bingo_game(con)

    # get all bingo information
    prompts = get_all_current_prompts(con)
    teamCompletedPrompts = get_count_of_completed_prompts(con)

    # TODO: come back to this with user auth
    amIAdmin = is_user_admin(con, 1)

    return templates.TemplateResponse("home.html", {
        "request": request,
        "prompts": prompts,
        "started": currentGame.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "week": currentGame.created_at.strftime("%d/%m"),
        "finished": currentGame.finished_at.strftime("%Y-%m-%d %H:%M:%S") if currentGame.finished_at is not None else "None",
        "teamComplete": teamCompletedPrompts,
        "bingoId": currentGame.id,
        "completedPrompts": myCompletedPrompts,
        "isMyWin": isMyWin,
        "winner": get_username_by_id(currentGame.victor) if currentGame.victor is not None else None,
        "amIAdmin": amIAdmin
    })

@router.get("/vote")
async def vote(request: Request):
    return templates.TemplateResponse("vote.html", { "request": request })

@router.get("/stats")
@router.post("/stats")
async def stats(request: Request, con: duckdb.DuckDBPyConnection = Depends(get_db)):
    usernames: List[str] = get_all_usernames(con)
    reqUser = usernames[0]

    if (request.method == "POST"):
        # handle selection of indexes
        formData = await request.form()
        reqUser = formData.get('username')
        
    # get information about requested user
    reqInfo: User = get_user_info_by_username(con, reqUser)

    # handle blank profile pictures
    profImgUrl = reqInfo.prof_img_url
    if profImgUrl is None:
        profImgUrl = "https://www.shutterstock.com/image-vector/blank-avatar-photo-placeholder-flat-600nw-1151124605.jpg"

    allBingoGames: List[Bingo] = get_all_bingo_games(con)

    return templates.TemplateResponse("stats.html", { 
        "request": request,
        "usernames": usernames,
        "user": reqInfo,
        "profImgUrl": profImgUrl,
        "bingoGames": allBingoGames
    })

@router.get("/admin")
def admin(request: Request, con: duckdb.DuckDBPyConnection = Depends(get_db)):
    amIAdmin = is_user_admin(con, 1)
    return templates.TemplateResponse("admin.html", { 
        "request": request,
        "amIAdmin": amIAdmin
    })