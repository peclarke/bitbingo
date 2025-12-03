from database import setup_database
from log import logger

def configure_logger():
    # i.e. make it info or debug level
    pass

def main():
    configure_logger()

    logger.info("BitBingo has started, beginning setup checks")
    setup_database()

if __name__ == "__main__":
    main()