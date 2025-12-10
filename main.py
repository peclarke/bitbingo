from fastapi.templating import Jinja2Templates
import uvicorn

from database import setup_database
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from log import logger
from routers import core, functions

def configure_logger():
    # i.e. make it info or debug level
    pass

def start_web_server():
    app = FastAPI()
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(functions.router)
    app.include_router(core.router)
    return app

def init():
    configure_logger()

    logger.info("BitBingo has started, beginning setup checks")
    setup_database()

    logger.info("Starting server")

app = start_web_server()

if __name__ == "__main__":
    init()
    uvicorn.run("main:app", port=5000, log_level="debug")