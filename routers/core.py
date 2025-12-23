from typing import Annotated, List
import duckdb
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from database import create_prompt, get_all_bingo_games, get_all_current_prompts, get_all_invites, get_all_prompts, get_all_usernames, get_bingo_game, get_completed_bingo_prompts_for_user, get_count_of_completed_prompts, get_leaderboard_users, get_user_info_by_username, get_username_by_id, is_user_admin, set_completed_prompts_for_user
from models import Bingo, User, get_current_admin, get_current_user
from utils import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DEFAULT_AVATAR_URL = "https://www.shutterstock.com/image-vector/blank-avatar-photo-placeholder-flat-600nw-1151124605.jpg"

@router.get("/")
@router.post("/")
async def homepage(request: Request, con: duckdb.DuckDBPyConnection = Depends(get_db), user: User = Depends(get_current_user)):
    isMyWin = False # only updates after you win after submitting a prompt change

    currentGame: Bingo = get_bingo_game(con)
    myCompletedPrompts = get_completed_bingo_prompts_for_user(con, currentGame.id, user.id)

    if (request.method == "POST"):
        # handle selection of indexes
        formData = await request.form()
        selected = formData.get('selected')
        if selected is not None:
            if len(selected) == 0:
                isMyWin = set_completed_prompts_for_user(con, currentGame.id, user.id, [])
                # set to new completed prompts
                myCompletedPrompts = []
            else:
                # convert to integer list
                indexesStr = selected.split(",")
                indexes = [int(x) for x in indexesStr]

                isMyWin = set_completed_prompts_for_user(con, currentGame.id, user.id, indexes)
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
    amIAdmin = is_user_admin(con, user.id)

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
        "winner": get_username_by_id(con, currentGame.victor) if currentGame.victor is not None else None,
        "amIAdmin": amIAdmin
    })

@router.get("/vote")
async def vote(request: Request):
    return templates.TemplateResponse("vote.html", { "request": request })

@router.get("/stats")
@router.post("/stats")
async def stats(request: Request, con: duckdb.DuckDBPyConnection = Depends(get_db), user: User = Depends(get_current_user)):
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
    # convert all the victor IDs to usernames
    for i in range(len(allBingoGames)):
        victor = allBingoGames[i].victor 
        if victor is not None:
            username = get_username_by_id(con, victor)
            allBingoGames[i].victor = username

    return templates.TemplateResponse("stats.html", { 
        "request": request,
        "usernames": usernames,
        "user": reqInfo,
        "profImgUrl": profImgUrl,
        "bingoGames": allBingoGames
    })

@router.get("/admin")
@router.post("/admin")
async def admin(request: Request, 
                con: duckdb.DuckDBPyConnection = Depends(get_db), 
                user: User = Depends(get_current_admin)):
    
    if (request.method == "POST"):
        # handle selection of indexes
        formData = await request.form()
        reqPrompt = formData.get('prompt')
        if reqPrompt is not None and len(reqPrompt) > 0:
            # add it to the prompts
            _isOk = create_prompt(con, reqPrompt)
    
    prompts = get_all_prompts(con)
    parsedPrompts: List[str] = list(map(lambda prompt: prompt[0], prompts))

    # get all invites
    invites = get_all_invites(con)
    makeUrl = lambda token : "http://127.0.0.1:5000/join/" + token
    parsedInvites: List[tuple] = list(map(lambda invite: (invite[1], makeUrl(invite[0]), invite[2].strftime("%Y-%m-%d %H:%M:%S"), invite[3]), invites))

    return templates.TemplateResponse("admin.html", { 
        "request": request,
        "amIAdmin": user.is_admin,
        "prompts": parsedPrompts,
        "invites": parsedInvites
    })

@router.get("/leaderboard")
def leaderboard(request: Request, con: duckdb.DuckDBPyConnection = Depends(get_db), user: User = Depends(get_current_user)):
    userPointLdb: List[User] = get_leaderboard_users(con)
    userGamesWnLdb: List[User] = get_leaderboard_users(con, "number_games_won")

    return templates.TemplateResponse("leaderboard.html", { 
        "request": request,
        "points": userPointLdb,
        "gamesWon": userGamesWnLdb
    })

def get_profile_context(
    req: Request,
    user: User = Depends(get_current_user),
):
    return {
        "request": req,
        "user": user,
        "profImgUrl": user.prof_img_url or DEFAULT_AVATAR_URL,
    }

@router.get("/profile")
def profile(req: Request, ctx: dict = Depends(get_profile_context)):
    alert = req.cookies.get("alert")
    ctx["alert"] = alert
    r = templates.TemplateResponse("profile.html", ctx)
    r.delete_cookie("alert")
    return r

@router.post("/updatepicture")
def updatepicture(
    pictureUrl: Annotated[str, Form()],
    con: duckdb.DuckDBPyConnection = Depends(get_db),
    ctx: dict = Depends(get_profile_context),
):
    if not pictureUrl:
        ctx["alert"] = "No URL given"
        return templates.TemplateResponse("profile.html", ctx)

    con.sql(f"UPDATE users SET prof_img_url = '{pictureUrl}' WHERE username = '{ctx["user"].username}'")

    ctx["profImgUrl"] = pictureUrl
    ctx["alert"] = "Profile picture updated"
    return templates.TemplateResponse("profile.html", ctx)
    
