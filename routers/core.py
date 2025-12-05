from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from database import get_all_current_prompts, get_bingo_game, get_count_of_completed_prompts

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def homepage(request: Request):
    # get all bingo information
    prompts = get_all_current_prompts()
    currentGame = get_bingo_game()
    teamCompletedPrompts = get_count_of_completed_prompts()

    return templates.TemplateResponse("home.html", {
        "request": request,
        "prompts": prompts,
        "victor": str(currentGame[2]),
        "started": currentGame[3].strftime("%Y-%m-%d %H:%M:%S"),
        "week": currentGame[3].strftime("%d/%m"),
        "teamComplete": teamCompletedPrompts,
        "bingoId": currentGame[0]
    })

@router.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("about.html", { "request": request })