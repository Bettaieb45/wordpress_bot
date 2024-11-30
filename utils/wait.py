from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import log
from config import driver
# Wait for an element
def wait_for_element(selector, by=By.CSS_SELECTOR, timeout=30):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
        log(f"Element {selector} loaded.")
        return True
    except Exception as e:
        log(f"Timeout waiting for element {selector}: {e}")
        return False