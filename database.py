from typing import List
import duckdb

from log import logger, log_exceptions

'''
Database calls for the `bingo` table
'''
@log_exceptions
def modify_mark_victor(user_id: int, conn = None):
    '''
    Marks the current incomplete game with the victor 

    Args:
        user_id: int - the winner of the current game
        conn: None or duckdb connection - a current connection to the db. Useful for chaining calls
    '''
    if (conn is None):
        conn = duckdb.connect("app.db")
    
    cnt, = conn.sql(f'SELECT COUNT(*) FROM users WHERE id = {user_id}').fetchone()
    if cnt > 0:
        conn.sql(f'UPDATE bingo SET victor = {user_id} WHERE completed = false')
        conn.sql(f'UPDATE users SET number_games_won = number_games_won + 1 WHERE id = {user_id}')
        logger.info(f"Marked {user_id} as victor for bingo game")
    else:
        logger.error(f"User with id [{user_id}] was not found and could not be marked the winner")

@log_exceptions
def generate_and_fill_prompts(bingo_game_id: int, con = None, number: int = 8):
    '''
    Generates prompts for the bingo game and inserts it into the database

    Args:
        - bingo_game_id: int - the integer id of the bingo game
        - con = None - database connection
        - number: int = 8 - the number of prompts to generate. 
            -> valid numbers are for all x>2, x^2-1
            -> this allows for a free square in the middle
    '''
    if (con is None):
        con = duckdb.connect('app.db')

    bingoCnt, = con.sql(f"SELECT COUNT(*) FROM bingo WHERE id = {bingo_game_id}").fetchone()
    if bingoCnt == 0:
        logger.error(f"Bingo game with id [{bingo_game_id}] does not exist")
        return
    
    # generate prompts
    results = con.sql(f"SELECT * FROM read_json('static/prompts.json') USING SAMPLE {number}").fetchall()
    prompts = list(map(lambda prompt: prompt[0], results))
    # insert free prompt
    prompts.insert(4, "FREE")

    # insert prompts into database
    for i, prompt in enumerate(prompts):
        con.sql(f"INSERT INTO prompts (bingo_game, idx, prompt) VALUES ({bingo_game_id}, {i},'{prompt}')")

@log_exceptions
def create_new_bingo_game(winner = None):
    '''
    This marks the current game as COMPLETE and creates a new one

    Args:
        - winner: int or None. If it's an int, it will mark that player as the victor
    '''
    with duckdb.connect("app.db") as con:
        # mark the current game with the winner
        if (winner is not None):
            modify_mark_victor(winner, con)

        con.sql('UPDATE bingo SET completed = true, finished_at = now() WHERE completed = false')
        con.sql('INSERT INTO bingo DEFAULT VALUES;')

        bingoId, = con.sql('SELECT id FROM bingo where completed = false').fetchone()
        generate_and_fill_prompts(bingoId, con)

        logger.info("Created a new bingo game")

# create_new_bingo_game(winner = 1)

@log_exceptions
def get_bingo_game(bingo_game_id: int = None):
    '''
    Fetch either the curent bingo game or one that is specified

    Args:
        bingo_game_id: int - the id of any bingo game or None for the current one
    '''
    with duckdb.connect("app.db") as con:
        game = None
        if bingo_game_id is None:
            game = con.sql("SELECT * FROM bingo WHERE completed = false").fetchone()
        else:
            game = con.sql(f"SELECT * FROM bingo WHERE id = {bingo_game_id}").fetchone()
        return game

@log_exceptions
def get_all_bingo_games():
    '''
    Gets all the bingo games that have ever been created

    Returns:
        - a list of tuples of bingo games
    '''
    with duckdb.connect("app.db") as con:
        try:
            res = con.sql("SELECT * FROM bingo").fetchall()
            return res
        except:
            logger.exception("get_all_bingo_games")

'''
Database calls for the `user_bingo` table
'''
@log_exceptions
def add_completed_prompt_to_user(bingo_game_id: int, user_id: int, prompt_indexes: List[int]):
    '''
    When a prompt is completed in the bingo table, mark it as complete

    Args:
        bingo_game_id - the ID of the bingo game
        user_id - the ID of the user that completed the prompt
        prompt_indexes - array of indexes where the completed prompt on the table is
    '''
    with duckdb.connect("app.db") as con:
        # Validate bingo and user in the db
        bingoCnt, = con.sql(f"SELECT COUNT(*) FROM bingo WHERE id = {bingo_game_id}").fetchone()
        userCnt,  = con.sql(f"SELECT COUNT(*) FROM users WHERE id = {user_id}").fetchone()

        if bingoCnt == 1 and userCnt == 1:
            # add the completed index
            for index in prompt_indexes:
                print(f'INSERT INTO user_bingo_progress (user_id, bingo_id, completed_index) VALUES ({user_id}, {bingo_game_id}, {index})')
                con.sql(f'INSERT INTO user_bingo_progress (user_id, bingo_id, completed_index) VALUES ({user_id}, {bingo_game_id}, {index})')

        elif bingoCnt != 1:
            logger.error(f"Bingo game with id [{bingo_game_id}] found a count of {bingoCnt} in the db")
        elif userCnt != 1:
            logger.error(f"User with id [{user_id}] found a count of {userCnt} in the db")

@log_exceptions
def get_completed_bingo_prompts_for_user(bingo_game_id: int, user_id: int):
    '''
    Gets a list of all completed bingo prompts for that user for that game

    Args:
        bingo_game_id - the ID of the bingo game
        user_id - the ID of the user that completed the prompt
    '''
    with duckdb.connect("app.db") as con:
        bingoCnt, = con.sql(f"SELECT COUNT(*) FROM bingo WHERE id = {bingo_game_id}").fetchone()
        userCnt,  = con.sql(f"SELECT COUNT(*) FROM users WHERE id = {user_id}").fetchone()

        if bingoCnt == 1 and userCnt == 1:
            results = con.sql(f"SELECT completed_index FROM user_bingo_progress WHERE user_id = {user_id} AND bingo_id = {bingo_game_id}").fetchall()
            indexes = list(map(lambda res: res[0], results))
            return indexes
        else:
            logger.error(f"Bingo game {bingo_game_id} was not found associated for user {user_id}")

@log_exceptions
def get_count_of_completed_prompts(bingo_game_id: int = None):
    '''
    Gets the number of prompts that have been completed for the specified game or current game

    Args:
        bingo_game_id: int = None - either the game id or nothing, which defaults to current
    '''
    with duckdb.connect('app.db') as con:
        if (bingo_game_id is None):
            promptCnt, = con.sql(f"SELECT COUNT(*) FROM user_bingo_progress WHERE bingo_id IN (SELECT id FROM bingo WHERE completed = false)").fetchone()
        else:
            promptCnt, = con.sql(f"SELECT COUNT(*) FROM user_bingo_progress WHERE bingo_id = {bingo_game_id}").fetchone()
        return promptCnt

get_count_of_completed_prompts()

def delete_bingo_prompt_for_user(bingo_game_id: int, user_id: int, prompt_index: int):
    pass

'''
Database calls for the `users` table
'''
def get_user_info(user_id: int):
    pass

def get_all_users():
    pass

def create_new_user():
    pass

'''
Database calls for the `prompts` table
'''
@log_exceptions
def get_all_current_prompts():
    '''
    Get all prompts for the current bingo game

    Returns:
        - [(idx, prompt)] - list of prompts and their indexes tupled together
    '''
    with duckdb.connect("app.db") as con:
        currentGameId, = con.sql("SELECT id FROM bingo WHERE completed = false").fetchone()
        if currentGameId is None:
            logger.info("No game is in session")
            return
        
        return con.sql(f"SELECT idx, prompt FROM prompts WHERE bingo_game = {currentGameId}").fetchall()

def get_all_prompts():
    '''
    Get all the prompts that the application can use
    '''
    pass

def create_prompt(prompt: str):
    pass

def remove_prompt(prompt_id: int):
    pass

'''
Meta database calls
'''
def setup_database(dbname = "app.db"):
    try:
        logger.info("Attempting connection and table check")
        con = duckdb.connect(database=dbname, read_only = False)
        con.sql('CREATE SEQUENCE IF NOT EXISTS user_increment START 1')
        con.sql('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY DEFAULT nextval('user_increment'),
                username VARCHAR UNIQUE NOT NULL,
                prof_img_url VARCHAR NULL,
                is_admin BOOLEAN DEFAULT false,
                points INTEGER DEFAULT 0,
                number_games_won INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT current_localtimestamp()
            )'''
        )
        con.sql('CREATE SEQUENCE IF NOT EXISTS bingo_increment START 1')
        con.sql('''CREATE TABLE IF NOT EXISTS bingo (
                id INTEGER PRIMARY KEY DEFAULT nextval('bingo_increment'),
                completed BOOLEAN DEFAULT false,
                victor INTEGER NULL REFERENCES users(id),
                created_at DATETIME DEFAULT current_localtimestamp(),
                finished_at DATETIME NULL DEFAULT NULL
            )'''
        )
        con.sql('''CREATE TABLE IF NOT EXISTS user_bingo_progress (
                user_id INTEGER,
                bingo_id INTEGER,
                completed_index INTEGER NOT NULL,
                PRIMARY KEY (user_id, bingo_id, completed_index)
            )'''
        )
        con.sql('''CREATE TABLE IF NOT EXISTS prompts (
                bingo_game INTEGER,
                idx INTEGER NOT NULL, -- where on the board the prompt is [0,16]
                prompt VARCHAR NOT NULL, -- the text that is in the square
                created_at DATETIME DEFAULT current_localtimestamp(),
                PRIMARY KEY (bingo_game, idx)
            )'''
        )
    except:
        logger.exception("An error occurred when setting up the database")
    finally:
        logger.info("Database is ready")
        con.close()