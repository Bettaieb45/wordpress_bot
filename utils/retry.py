import time 
#import logger.py file 
from utils.logger import log
from utils.append_csv import write_results_to_csv_row
# Retry logic
def retry(action,page_url=None,anchors=None,csv_file=None, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return action()
        except Exception as e:
            log(f"Attempt {attempt+1} failed: {e}")
            time.sleep(delay)
    log(f"All {retries} attempts failed.")
    log(f"No identifiable button found for {page_url}. Skipping page.")
    for anchor in anchors:
        write_results_to_csv_row({
            "Page URL": page_url,
            "Anchor Text": anchor["Anchor Text"],
            "Broken HREF": anchor["Broken HREF"],
            "New HREF": anchor["New Href"],
            "Status": "Button can't be clicked"
            }, csv_file)
    return False