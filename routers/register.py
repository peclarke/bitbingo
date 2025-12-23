import duckdb
import hashlib
import base64

from datetime import datetime
from typing import Annotated, List
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from database import create_new_user, get_all_prompts
from models import CustomBaseModel, User, get_current_admin, hash_this_password
from utils import get_db


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/join")
async def wrongjoin(req: Request):
    return RedirectResponse(url="/")

class Invitee(CustomBaseModel):
    token: str
    username: str
    expiresAt: datetime
    completed: bool

async def get_token_invitee(token: str, con = Depends(get_db)) -> Invitee | None:
    """
    Docstring for get_token_invitee
    
    :param token: Description
    :type token: str
    :param con: Description
    :type con: duckdb.DuckDBPyConnection
    :return: Description
    :rtype: Invitee | None
    """
    res = con.sql(f"SELECT * FROM invites WHERE token = '{token}'").fetchone()
    #TODO: validate that the expired time of this invite is within range


    if res is None:
        return res
    return Invitee.from_list(res)


@router.get("/join/{token}")
async def join(token: str, 
               req: Request,
               invitee: Invitee | None = Depends(get_token_invitee)):
    # make sure that there is actually an invitee associated with this token
    # and make sure that a user isn't already logged in
    access = req.cookies.get("access_token")
    if invitee is None or access is not None or invitee.completed:
        return RedirectResponse(url="/")

    return templates.TemplateResponse("register.html", {
        "request": req,
        "username": invitee.username,
        "token": token
    })

@router.post("/activate")
async def activate(req: Request, 
                   password: Annotated[str, Form()], 
                   confirm: Annotated[str, Form()], 
                   tokenconfirm: Annotated[str, Form()],
                   con = Depends(get_db)):
    invitee = await get_token_invitee(tokenconfirm, con)
    # make sure that it is a valid invite
    if invitee is None:
        return RedirectResponse(url="/")
    
    hashedPassword = hash_this_password(password)
    con.sql(f"INSERT INTO auth (username, hashpsw) VALUES ('{invitee.username}', '{hashedPassword}')")
    # update the invite to be completed
    con.sql(f"UPDATE invites SET completed = true WHERE token = '{invitee.token}'")
    # activate the user
    con.sql(f"UPDATE users SET is_activated = true WHERE username = '{invitee.username}'")

    return templates.TemplateResponse("noauth.html", {
        "request": req,
        "alert": "Account activated. Sign in to get started!"
    })


def make_token(username: str, dt: str, length: int = 8) -> str:
    # Combine inputs
    raw = f"{username}|{dt}".encode("utf-8")

    # Hash
    digest = hashlib.sha256(raw).digest()

    # Base64 encode (URL safe) and trim
    token = base64.urlsafe_b64encode(digest).decode("utf-8")
    return token[:length]

@router.post("/createinvite")
async def createinvite(req: Request, 
                       username: Annotated[str, Form()], 
                       con: duckdb.DuckDBPyConnection = Depends(get_db),
                       admin: User = Depends(get_current_admin)):
    # create deactivated user account
    create_new_user(con, username)
    # generate unique token
    dt = str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    token = make_token(username, dt)
    # insert into database
    con.sql(f"INSERT INTO invites (token, username) VALUES ('{token}','{username}')")

    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)

@router.post("/clearallinvites")
async def clearallinvites(con: duckdb.DuckDBPyConnection = Depends(get_db),
                          _ = Depends(get_current_admin)):
    """
    Docstring for clearallinvites
    
    :param req: Description
    :type req: Request
    :param con: Description
    :type con: duckdb.DuckDBPyConnection
    :param _: Description
    """
    con.sql(f"DELETE FROM invites")
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)