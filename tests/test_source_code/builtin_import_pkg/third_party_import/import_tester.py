from datetime import datetime
import time
from os.path import isdir
import logging.config

now = datetime.now()
some_time = time.time()
isdir(".")
cfg = logging.config.dictConfig()
