from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from database import get_all_current_prompts

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def homepage(request: Request):
    # get prompts
    prompts = get_all_current_prompts()

    return templates.TemplateResponse("home.html", {
        "request": request,
        "prompts": prompts
    })

@router.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("about.html", { "request": request })