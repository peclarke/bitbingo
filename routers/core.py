from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from database import get_all_current_prompts, get_bingo_game, get_completed_bingo_prompts_for_user, get_count_of_completed_prompts, set_completed_prompts_for_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
@router.post("/")
async def homepage(request: Request):
    currentGame = get_bingo_game()
    myCompletedPrompts = get_completed_bingo_prompts_for_user(currentGame[0], 1)

    if (request.method == "POST"):
        # handle selection of indexes
        formData = await request.form()
        selected = formData.get('selected')
        if selected is not None:
            if len(selected) == 0:
                set_completed_prompts_for_user(currentGame[0], 1, [])
                # set to new completed prompts
                myCompletedPrompts = []
            else:
                # convert to integer list
                indexesStr = selected.split(",")
                indexes = [int(x) for x in indexesStr]

                set_completed_prompts_for_user(currentGame[0], 1, indexes)
                # set to new completed prompts
                myCompletedPrompts = indexes

    # get all bingo information
    prompts = get_all_current_prompts()
    teamCompletedPrompts = get_count_of_completed_prompts()

    return templates.TemplateResponse("home.html", {
        "request": request,
        "prompts": prompts,
        "victor": str(currentGame[2]),
        "started": currentGame[3].strftime("%Y-%m-%d %H:%M:%S"),
        "week": currentGame[3].strftime("%d/%m"),
        "teamComplete": teamCompletedPrompts,
        "bingoId": currentGame[0],
        "completedPrompts": myCompletedPrompts
    })

@router.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("about.html", { "request": request })