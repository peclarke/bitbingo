from fastapi.templating import Jinja2Templates
import uvicorn

from database import setup_database
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from log import logger
from routers import adm, auth, core, functions, register

def configure_logger():
    # i.e. make it info or debug level
    pass

def init():
    configure_logger()

    logger.info("BitBingo has started, beginning setup checks")
    setup_database()

    logger.info("Starting server")

async def lifespan(app: FastAPI):
    # initialise the application
    init()
    yield

def start_web_server():
    app = FastAPI(lifespan=lifespan)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    # include all our routers
    app.include_router(functions.router)
    app.include_router(core.router)
    app.include_router(auth.router)
    app.include_router(register.router)
    app.include_router(adm.router)

    return app

app = start_web_server()

if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="debug")