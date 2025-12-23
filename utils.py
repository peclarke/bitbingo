import duckdb
import os

from typing import Tuple
from log import logger

DB_PATH = os.getenv("DUCKDB_PATH", "app.db")

async def get_db():
    con = duckdb.connect(DB_PATH)
    try:
        yield con
    except:
        logger.error("Something went wrong grabbing the DB connection")
        raise
    finally:
        con.close()

def _win_masks_for_n(n: int) -> Tuple[int, ...]:
    """
    Returns bitmasks for all winning lines (rows, cols, 2 diagonals) on an n x n board.
    Indices are row-major: 0..n*n-1.
    Bit i corresponds to index i (i.e., 1 << i).
    """
    if n < 1:
        raise ValueError("n must be >= 1")

    masks = []

    # Rows
    for r in range(n):
        m = 0
        for c in range(n):
            m |= 1 << (r * n + c)
        masks.append(m)

    # Cols
    for c in range(n):
        m = 0
        for r in range(n):
            m |= 1 << (r * n + c)
        masks.append(m)

    # Main diagonal (top-left -> bottom-right)
    m = 0
    for i in range(n):
        m |= 1 << (i * n + i)
    masks.append(m)

    # Anti-diagonal (top-right -> bottom-left)
    m = 0
    for i in range(n):
        m |= 1 << (i * n + (n - 1 - i))
    masks.append(m)

    return tuple(masks)