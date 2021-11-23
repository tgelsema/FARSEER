"""
Configuration of general logger. Kept separate from flask application logger.
See ask_and_answer.py for flask app logger configuration.

When we know what exactly should be logged and in what format, this will probably be changed.
"""

import logging

logger = logging.getLogger("INFO")
logger.setLevel(logging.INFO)
#Define a format
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

#Define a handler. In our case, we write to a file in this folder
filehandler = logging.FileHandler('infolog.log')
filehandler.setFormatter(formatter)

#Add handler to our logger
logger.addHandler(filehandler)