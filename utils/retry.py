import time 
#import logger.py file 
from utils.logger import log
# Retry logic
def retry(action, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return action()
        except Exception as e:
            log(f"Attempt {attempt+1} failed: {e}")
            time.sleep(delay)
    log(f"All {retries} attempts failed.")
    return False