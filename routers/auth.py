

from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from models import ACCESS_TOKEN_EXPIRE_MINUTES, Token, User, auth_this_user, create_access_token, get_current_user, hash_this_password


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/landing")
@router.post("/landing")
async def landing(request: Request):
    return templates.TemplateResponse("noauth.html", { "request": request })

@router.post("/authme")
async def authme(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = auth_this_user(form_data.username, form_data.password)
    print(user)

    if not user:
        # raise HTTPException(
        #     status_code=status.HTTP_401_UNAUTHORIZED,
        #     detail="Incorrect username or password",
        #     headers={"WWW-Authenticate": "Bearer"},
        # )
        return RedirectResponse(url="/landing")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.get("/users/me")
async def test(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    return current_user