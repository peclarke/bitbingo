import duckdb

from log import logger

'''
Database calls for the `bingo` table
'''
def modify_mark_victor(bingo_game_id: int):
    pass

def create_new_bingo_game():
    pass

def get_bingo_game(bingo_game_id: int):
    pass

def get_all_bingo_games():
    pass

'''
Database calls for the `user_bingo` table
'''
def add_completed_prompt_to_user(bingo_game_id: int, user_id: int, prompt_index: int):
    pass

def get_completed_bingo_prompts_for_user(bingo_game_id: int, user_id: int):
    pass

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
def get_all_prompts():
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
        con.sql('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username VARCHAR,
                prof_img_url VARCHAR,
                is_admin BOOLEAN,
                points INTEGER,
                number_games_won INTEGER,
                created_at DATETIME 
            )'''
        )
        con.sql('''CREATE TABLE IF NOT EXISTS bingo (
                id INTEGER PRIMARY KEY,
                completed BOOLEAN,
                victor INTEGER REFERENCES users(id),
                created_at DATETIME
            )'''
        )
        con.sql('''CREATE TABLE IF NOT EXISTS user_bingo_progress (
                user_id INTEGER REFERENCES users(id),
                bingo_id INTEGER REFERENCES bingo(id),
                completed_index INTEGER,
                PRIMARY KEY (user_id, bingo_id, completed_index)
            )'''
        )
        con.sql('''CREATE TABLE IF NOT EXISTS prompts (
                bingo_game INTEGER REFERENCES bingo(id),
                idx INTEGER, -- where on the board the prompt is [0,16]
                prompt VARCHAR, -- the text that is in the square
                PRIMARY KEY (bingo_game, idx)
            )'''
        )
    except:
        logger.exception("An error occurred when setting up the database")
    finally:
        logger.info("Database is ready")
        con.close()