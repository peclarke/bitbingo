import logging
import datetime
import os

# create logger
logger = logging.getLogger("BitBingo")
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# check if log directory exists
if (not os.path.isdir('logs')):
    os.makedirs('logs')

current = datetime.datetime.now().strftime("%Y-%m-%d")
file_handler = logging.FileHandler(f"./logs/{current}-app.log", mode="a", encoding="utf-8")
file_handler.formatter = formatter
logger.addHandler(file_handler)

# add ch to logger
logger.addHandler(ch)