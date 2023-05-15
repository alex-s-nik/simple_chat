import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

NUMBER_OF_HISTORY_MESSAGES = 20
TIME_TO_BAN = 60
