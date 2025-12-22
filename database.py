import random
from typing import List
import duckdb

from log import logger, log_exceptions
from models import Bingo, User
from utils import _win_masks_for_n

'''
Database calls for the `bingo` table
'''
def handle_victor(con: duckdb.DuckDBPyConnection, user_id: int):
    '''
    Handles marking the victory of a game
    '''
    # a game can be incomplete and a winner found
    bingoGameId, = con.sql("SELECT id FROM bingo WHERE completed = false").fetchone()
    # check if there is already a winner.
    count, = con.sql(f"SELECT COUNT(victor) FROM bingo WHERE completed = false AND victor IS NOT NULL").fetchone()
    if (count == 0):
        # first time a winner has been found
        modify_mark_victor(user_id, bingoGameId, con)
        set_finish_time_for_game(con)
    else:
        # gain 50 points for completing bingo, but not first
        assign_victory_points(con=con, user_id=user_id, bingo_game=bingoGameId, points=50)

def set_finish_time_for_game(con: duckdb.DuckDBPyConnection):
    '''
    Sets the time the bingo game finished, or was won
    '''
    con.sql("UPDATE bingo SET finished_at = current_localtimestamp() WHERE completed = false")

@log_exceptions
def modify_mark_victor(user_id: int, bingoGameId: int = None, conn = None):
    '''
    Marks the current incomplete game with the victor 

    Args:
        user_id: int - the winner of the current game
        bingoGameId: int - the id of the bingo game to mark points to 
        conn: None or duckdb connection - a current connection to the db. Useful for chaining calls
    '''
    if (conn is None):
        conn = duckdb.connect("app.db")

    if bingoGameId is None:
        bingoGameId, = conn.sql(f'SELECT id FROM bingo WHERE completed = false').fetchone()
    
    cnt, = conn.sql(f'SELECT COUNT(*) FROM users WHERE id = {user_id}').fetchone()
    if cnt > 0:
        conn.sql(f'UPDATE bingo SET victor = {user_id} WHERE completed = false')
        conn.sql(f'UPDATE users SET number_games_won = number_games_won + 1 WHERE id = {user_id}')
        # 100 victory points for being the first to win the bingo game
        assign_victory_points(con=conn, user_id=user_id, bingo_game=bingoGameId, points=100)
        logger.info(f"Marked {user_id} as victor for bingo game")
    else:
        logger.error(f"User with id [{user_id}] was not found and could not be marked the winner")

@log_exceptions
def assign_victory_points(con: duckdb.DuckDBPyConnection, user_id: int, bingo_game: int, points: int):
    '''
    When a game is won, assign victory points for that user
    '''
    cnt, = con.sql(f"SELECT COUNT(*) FROM user_wins WHERE user_id = {user_id} AND bingo_id = {bingo_game}").fetchone()
    if cnt > 0:
        # The user has already won once before, no more points for you
        return
    
    # Give them the points and mark them as won for this game
    con.sql(f'UPDATE users SET points = points + {points} WHERE id = {user_id}')
    con.sql(f"INSERT INTO user_wins (user_id, bingo_id) VALUES ({user_id}, {bingo_game})")

@log_exceptions
def get_game_winner():
    '''
    Gets the winner or None of the current game

    Returns:
        userId or None
    '''
    with duckdb.connect("app.db") as con:
        victor, = con.sql("SELECT victor FROM bingo WHERE completed = false").fetchone()
        return victor

@log_exceptions
def generate_and_fill_prompts(bingo_game_id: int, con = None, number: int = 8, use_json = False):
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
    
    # get size of grid
    n = get_n_for_game(con)
    numberOfPrompts = (n*n)-1
    
    # generate prompts
    query = f"SELECT * FROM prompts_static USING SAMPLE {numberOfPrompts}"
    if (use_json):
        query = f"SELECT * FROM read_json('static/prompts.json') USING SAMPLE {numberOfPrompts}"

    results = con.sql(query).fetchall()
    prompts = list(map(lambda prompt: prompt[0], results))
    # insert free prompt
    freeIndex = 4 if n == 3 else random.randint(0,15)
    prompts.insert(freeIndex, "FREE")

    # insert prompts into database
    for i, prompt in enumerate(prompts):
        con.sql(f"INSERT INTO prompts (bingo_game, idx, prompt) VALUES ({bingo_game_id}, {i},'{prompt}')")

@log_exceptions
def create_new_bingo_game(con: duckdb.DuckDBPyConnection, winner = None):
    '''
    This marks the current game as COMPLETE and creates a new one

    Args:
        - winner: int or None. If it's an int, it will mark that player as the victor
    '''
    # mark the current game with the winner
    if (winner is not None):
        modify_mark_victor(user_id=winner, conn=con)

    con.sql('UPDATE bingo SET completed = true, finished_at = now() WHERE completed = false')
    con.sql('INSERT INTO bingo DEFAULT VALUES;')

    bingoId, = con.sql('SELECT id FROM bingo where completed = false').fetchone()
    generate_and_fill_prompts(bingoId, con)

    logger.info("Created a new bingo game")

@log_exceptions
def get_bingo_game(con: duckdb.DuckDBPyConnection, bingo_game_id: int = None):
    '''
    Fetch either the curent bingo game or one that is specified

    Args:
        bingo_game_id: int - the id of any bingo game or None for the current one

    Returns:
        pydantic model of a Bingo game (current or specified)
    '''
    game = None
    if bingo_game_id is None:
        game = con.sql("SELECT * FROM bingo WHERE completed = false").fetchone()
    else:
        game = con.sql(f"SELECT * FROM bingo WHERE id = {bingo_game_id}").fetchone()
    return Bingo(id=game[0], completed=game[1], victor=game[2], created_at=game[3], finished_at=game[4])

@log_exceptions
def get_all_bingo_games(con: duckdb.DuckDBPyConnection):
    '''
    Gets all the bingo games that have ever been created

    Returns:
        - a list of tuples of bingo games
    '''
    try:
        res = con.sql("SELECT * FROM bingo").fetchall()
        bingoResults: List[Bingo] = []
        for bingo in res:
            b = Bingo.from_list(bingo)
            bingoResults.append(b)
        return bingoResults
    except:
        logger.exception("get_all_bingo_games")

'''
Database calls for the `user_bingo` table
'''
@log_exceptions
def set_completed_prompts_for_user(con: duckdb.DuckDBPyConnection, bingo_game_id: int, user_id: int, prompt_indexes: List[int]):
    '''
    When a prompt is completed in the bingo table, mark it as complete

    Args:
        bingo_game_id - the ID of the bingo game
        user_id - the ID of the user that completed the prompt
        prompt_indexes - array of indexes where the completed prompt on the table is
    '''
    # Validate bingo and user in the db
    bingoCnt, = con.sql(f"SELECT COUNT(*) FROM bingo WHERE id = {bingo_game_id}").fetchone()
    userCnt,  = con.sql(f"SELECT COUNT(*) FROM users WHERE id = {user_id}").fetchone()

    if bingoCnt == 1 and userCnt == 1:
        # remove all other prompts to start
        con.sql(f'DELETE FROM user_bingo_progress WHERE user_id = {user_id} AND bingo_id = {bingo_game_id}')
        # add the completed indexes
        for index in prompt_indexes:
            con.sql(f'INSERT INTO user_bingo_progress (user_id, bingo_id, completed_index) VALUES ({user_id}, {bingo_game_id}, {index})')

    elif bingoCnt != 1:
        logger.error(f"Bingo game with id [{bingo_game_id}] found a count of {bingoCnt} in the db")
    elif userCnt != 1:
        logger.error(f"User with id [{user_id}] found a count of {userCnt} in the db")

    # check for winners (isWon, user)
    isWon, userId = check_win(con, user_id)
    if isWon:
        handle_victor(con, userId)   

    return isWon

@log_exceptions
def get_completed_bingo_prompts_for_user(con: duckdb.DuckDBPyConnection, bingo_game_id: int, user_id: int):
    '''
    Gets a list of all completed bingo prompts for that user for that game

    Args:
        bingo_game_id - the ID of the bingo game
        user_id - the ID of the user that completed the prompt
    '''
    bingoCnt, = con.sql(f"SELECT COUNT(*) FROM bingo WHERE id = {bingo_game_id}").fetchone()
    userCnt,  = con.sql(f"SELECT COUNT(*) FROM users WHERE id = {user_id}").fetchone()

    if bingoCnt == 1 and userCnt == 1:
        results = con.sql(f"SELECT completed_index FROM user_bingo_progress WHERE user_id = {user_id} AND bingo_id = {bingo_game_id}").fetchall()
        indexes = list(map(lambda res: res[0], results))
        return indexes
    else:
        logger.error(f"Bingo game {bingo_game_id} was not found associated for user {user_id}")

@log_exceptions
def get_count_of_completed_prompts(con: duckdb.DuckDBPyConnection, bingo_game_id: int = None):
    '''
    Gets the number of prompts that have been completed for the specified game or current game

    Args:
        bingo_game_id: int = None - either the game id or nothing, which defaults to current

    Returns:
        integer of number of completed prompts for that game
    '''
    if (bingo_game_id is None):
        promptCnt, = con.sql(f"SELECT COUNT(*) FROM user_bingo_progress WHERE bingo_id IN (SELECT id FROM bingo WHERE completed = false)").fetchone()
    else:
        promptCnt, = con.sql(f"SELECT COUNT(*) FROM user_bingo_progress WHERE bingo_id = {bingo_game_id}").fetchone()
    return promptCnt

@log_exceptions
def get_n_for_game(con: duckdb.DuckDBPyConnection):
    n, = con.sql("SELECT n FROM config").fetchone()
    return n

@log_exceptions
def check_win(con: duckdb.DuckDBPyConnection, user_to_check: int):
    '''
    Check if there is a winner for the current bingo game. This function is desgined to
    be executed directly after a prompt update to user_bingo_progress

    Arg:
        user_to_check: int - user id of the user to check

    Returns:
        (result boolean, id): tuple - (True, userId) if there is a winner (False, None) if nothing
    '''
    # Precompute for speed (toggle n=3 or n=4)
    WIN_MASKS_3 = _win_masks_for_n(3)
    WIN_MASKS_4 = _win_masks_for_n(4)

    n = get_n_for_game(con)

    currentGameId, = con.sql("SELECT id FROM bingo WHERE completed = false").fetchone()
    completed = get_completed_bingo_prompts_for_user(con, currentGameId, user_to_check)

    limit = n * n # (n x n) grid
    mask = 0
    for i in completed:
        if 0 <= i < limit:
            mask |= 1 << i
        else:
            raise ValueError(f"Index out of range: {i} (expected 0..{limit-1})")

    win_masks = WIN_MASKS_3 if n == 3 else WIN_MASKS_4
    result = any((mask & win) == win for win in win_masks)
    if result:
        return (result, user_to_check)
    else:
        return (False, None)

@log_exceptions
def old_check_win(con: duckdb.DuckDBPyConnection, user_to_check: int):
    '''
    Check if there is a winner for the current bingo game. This function is desgined to
    be executed directly after a prompt update to user_bingo_progress

    Arg:
        user_to_check: int - user id of the user to check

    Returns:
        (result boolean, id): tuple - (True, userId) if there is a winner (False, None) if nothing
    '''
    currentGameId, = con.sql("SELECT id FROM bingo WHERE completed = false").fetchone()
    completedPrompts = get_completed_bingo_prompts_for_user(con, currentGameId, user_to_check)

    """
    check for winnings (THIS IS FOR A 3x3 GROUPING)
    winning combos:
        [0, 1, 2], [3, 4, 5], [6, 7, 8]
        [0, 3, 6], [1, 4, 7], [2, 5, 8]
        [0, 4, 8], [2, 4, 6]

    Since subset is an expensive operation, I've opted to do a bit of preprocessing. 
    We're going to bucket sort the winning combinations down so just by using the first
    number of selected indexes, we can shrink maximum combinations from 8 to 3.
    """
    firstDigitWinners = {
        0: [[0, 1, 2], [0, 3, 6], [0, 4, 8]],
        1: [[0, 1, 2], [1, 4, 7]],
        2: [[0, 1, 2], [2, 5, 8], [2, 4, 6]],
        3: [[3, 4, 5], [0, 3, 6]],
        4: [[3, 4, 5], [1, 4, 7], [0, 4, 8], [2, 4, 6]],
        5: [[3, 4, 5], [2, 5, 8]],
        6: [[6, 7, 8], [2, 4, 6]],
        7: [[6, 7, 8], [1, 4, 7], [0, 4, 8]],
        8: [[6, 7, 8], [2, 5, 8]]
    }
    # find potential winning combinations
    completed = set(completedPrompts)

    def checkNumber(possibleWinners):
        # is the current set of indexes a subset of any winners?
        isWinner = False
        i = 0
        while i < len(possibleWinners) and isWinner == False:
            winner = possibleWinners[i]
            # must have at least 3 digits selected and must be a subset of a victory state
            if len(completed) >= 3 and set(winner).issubset(completed):
                isWinner = True
                return isWinner
            i += 1
        return isWinner

    for number in completedPrompts:
        possibleWinners = firstDigitWinners[number]
        isWinner = checkNumber(possibleWinners)

    if isWinner:
        return (True, user_to_check)
    else:
        return (False, None)


'''
Database calls for the `users` table
'''
@log_exceptions
def get_user_info_by_username(con: duckdb.DuckDBPyConnection, username: str):
    '''
    Gets all the information associated with the user given the user's username

    Args:
        username: str - the unique username of that user

    Returns:
        user object or None if not found
    '''
    user = con.sql(f"SELECT * FROM users WHERE username = '{username}'").fetchone()
    if user is not None:
        return User.from_list(user)
    return None

@log_exceptions
def get_username_by_id(con: duckdb.DuckDBPyConnection, user_id: int):
    '''
    Gets all the information associated with the user given the user's ID

    Args:
        user_id: int - the user id to query
    '''
    username, = con.sql(f"SELECT username FROM users WHERE id = {user_id}").fetchone()
    return username

@log_exceptions
def get_all_usernames(con: duckdb.DuckDBPyConnection):
    '''
    Gets a list of all usernames in the database

    Returns:
        a list of usernames (str)
    '''
    res = con.sql(f"SELECT username FROM users").fetchall()
    usernames = [name[0] for name in res]
    return usernames

@log_exceptions
def get_all_users(con: duckdb.DuckDBPyConnection):
    '''
    Returns all users
    '''
    res = con.sql(f"SELECT * FROM users").fetchall()
    users: List[User] = []
    for u in res:
        user = User.from_list(u)
        users.append(user)
    return users

def get_leaderboard_users(con: duckdb.DuckDBPyConnection, method = 'points'):
    '''
    Gets abridged users in order of points

    Args:
        method: either 'points' or 'number_games_won'. 
            number_games_won sorts in terms of most games won.
            Points sorts in terms of most points. Defaults to this.

    Returns:
        A list of users with id, username, and that method in descending order
    '''
    results = con.sql(f"SELECT * FROM users ORDER BY {method} DESC").fetchall()
    users: List[User] = multiple_users_to_multiple_models(results)
    return users
    
def multiple_users_to_multiple_models(results):
    users: List[User] = []
    for u in results:
        user = User.from_list(u)
        users.append(user)
    return users
    
@log_exceptions
def is_user_admin(con: duckdb.DuckDBPyConnection, user_id: int):
    '''
    Check if the given user id is an admin user

    Args:
        user_id: int - the user ID to query
    
    Returns:
        isAdmin: bool - true if the user is admin, false if not
    '''
    res = con.sql(f"SELECT is_admin FROM users WHERE id = {user_id}").fetchone()
    if res is not None:
        return res[0]
    else:
        return False

def create_new_user():
    pass

'''
Database calls for the `prompts` table
'''
@log_exceptions
def get_all_current_prompts(con: duckdb.DuckDBPyConnection):
    '''
    Get all prompts for the current bingo game

    Returns:
        - [(idx, prompt)] - list of prompts and their indexes tupled together
    '''
    currentGameId, = con.sql("SELECT id FROM bingo WHERE completed = false").fetchone()
    if currentGameId is None:
        logger.info("No game is in session")
        return
    
    return con.sql(f"SELECT idx, prompt FROM prompts WHERE bingo_game = {currentGameId}").fetchall()

def get_all_prompts(con: duckdb.DuckDBPyConnection):
    '''
    Get all the prompts that the application can use
    '''
    return con.sql("SELECT * FROM prompts_static").fetchall()

def create_prompt(con: duckdb.DuckDBPyConnection, prompt: str):
    if len(prompt) == 0:
        return False
    
    con.sql(f"INSERT INTO prompts_static VALUES ('{prompt}')")
    return True

def remove_prompt(prompt_id: int):
    pass

'''
Minigames
'''
def increase_click(user_id: int, bingo_game: int, clicks: int):
    '''
    Increases the click by 1 per user/bingo game in the database
    '''
    with duckdb.connect("app.db") as con:
        usrCnt, = con.sql(f"SELECT COUNT(*) FROM users WHERE id = {user_id}").fetchone()
        bingoCnt, = con.sql(f"SELECT COUNT(*) FROM bingo WHERE id = {bingo_game}").fetchone()
        if usrCnt == 0:
            logger.error(f"User does not exist to increase click with. User ID: {user_id}")
            return False
        
        if bingoCnt == 0:
            logger.error(f"Bingo game doesn't exist. ID: {bingo_game}")
            return False
        
        if not isinstance(clicks, int):
            logger.error("Number of clicks is not an integer")
            return False
        
        if clicks < 0:
            logger.error(f"Number of clicks cannot be a negative number: {clicks}")
            return False
        
        # check if the user has already got one
        records, = con.sql(f"SELECT COUNT(*) FROM user_game_clicks WHERE user_id = {user_id} AND bingo_id = {bingo_game}").fetchone()
        if records > 0:
            con.sql(f"UPDATE user_game_clicks SET clicks = clicks + {clicks} WHERE user_id = {user_id} AND bingo_id = {bingo_game}")
        else:
            # create one from scratch
            con.sql(f"INSERT INTO user_game_clicks (user_id, bingo_id, clicks) VALUES ({user_id}, {bingo_game}, {clicks})")

'''
Meta database calls
'''
def setup_database(dbname = 'app.db'):
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
                is_activated BOOLEAN DEFAULT false,
                created_at DATETIME DEFAULT current_localtimestamp()
            )'''
        )
        con.sql('''CREATE TABLE IF NOT EXISTS auth (username VARCHAR UNIQUE NOT NULL, hashpsw VARCHAR NOT NULL)''')
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
        con.sql('''CREATE TABLE IF NOT EXISTS user_wins (
                user_id INTEGER,
                bingo_id INTEGER,
                PRIMARY KEY (user_id, bingo_id)
                )'''
        )
        con.sql('''CREATE TABLE IF NOT EXISTS user_game_clicks (
                user_id INTEGER,
                bingo_id INTEGER,
                clicks INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, bingo_id))
            ''')
        con.sql('''CREATE TABLE IF NOT EXISTS prompts (
                bingo_game INTEGER,
                idx INTEGER NOT NULL, -- where on the board the prompt is [0,16]
                prompt VARCHAR NOT NULL, -- the text that is in the square
                created_at DATETIME DEFAULT current_localtimestamp(),
                PRIMARY KEY (bingo_game, idx)
            )'''
        )
        con.sql('''CREATE TABLE IF NOT EXISTS prompts_static AS
                SELECT * AS "prompts" FROM read_json_auto('static/prompts.json')''')
        
        con.sql('''CREATE TABLE IF NOT EXISTS config (n INTEGER NOT NULL DEFAULT 3)''')
        # create a config if one didn't exist before hand
        configs, = con.sql('SELECT COUNT(*) FROM config').fetchone()
        if configs == 0:
            con.sql('INSERT INTO config DEFAULT VALUES')

        # ensure a bingo game now exists
        bingoGames, = con.sql('SELECT COUNT(*) FROM bingo').fetchone()
        if bingoGames == 0:
            create_new_bingo_game(con)

    except:
        logger.exception("An error occurred when setting up the database")
    finally:
        logger.info("Database is ready")
        con.close()