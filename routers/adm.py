from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from database import adminify_user, delete_user
from models import get_current_admin
from utils import get_db


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/deleteuser")
async def deleteuser(req: Request,
                     res: Response,
                     userid: Annotated[str, Form()],
                     admin = Depends(get_current_admin),
                     con = Depends(get_db)):
    # delete the user
    userIdParsed = int(userid)
    try:
        response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
        delete_user(con, userIdParsed)
        response.set_cookie("alert", "User Id "+userid+" has been deleted successfully")
    except:
        response.set_cookie("alert", "Something went wrong deleting that user")
    return response

@router.post("/adminuser")
async def deleteuser(req: Request,
                     res: Response,
                     userid: Annotated[str, Form()],
                     admin = Depends(get_current_admin),
                     con = Depends(get_db)):
    userIdParsed = int(userid)
    isOK = adminify_user(con, userIdParsed)
    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("alert", "User Id "+userid+" has been made an administrator")
    return response