

from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
import jwt

from models import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY, Token, User, auth_this_user, create_access_token, get_current_user, hash_this_password


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/landing")
@router.post("/landing")
async def landing(request: Request, response: Response):
    token = request.cookies.get("access_token")
    if token is not None:
        # test if its a valid token
        r = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        try:
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.InvalidTokenError:
            r = RedirectResponse(url="/landing", status_code=status.HTTP_303_SEE_OTHER)
            r.delete_cookie("access_token")
        return r
    
    return templates.TemplateResponse("noauth.html", { "request": request })

@router.post("/token")
async def authme(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Response:
    user = auth_this_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=301, headers={"Location": "/landing", "WWW-Authenticate": "Bearer"}, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    token = Token(access_token=access_token, token_type="bearer")

    # Set the cookie in the response
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token", 
        value=token.access_token, 
        httponly=True, 
        secure=True, # Use Secure in production (HTTPS)
        samesite="Strict" # Helps prevent CSRF
    )

    return response

@router.get("/logout")
async def logout(resp: Response):
    resp = RedirectResponse(url="/landing", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie(key="access_token", path="/")
    return resp

@router.get("/users/me")
async def test(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    return current_user