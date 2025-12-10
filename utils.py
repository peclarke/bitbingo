
import duckdb

from log import logger


async def get_db():
    con = duckdb.connect("app.db")
    try:
        yield con
    except:
        logger.error("Something went wrong grabbing the DB connection")
        raise
    finally:
        con.close()
