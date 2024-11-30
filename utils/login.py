from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from utils.logger import log
import os
import pickle
from config import COOKIE_FILE, driver,login_url
import utils.wait as wait_for_element
# Google Authenticator OTP input
def get_google_authenticator_code_from_user():
    return input("Enter the Google Authenticator code: ")

def login_to_wordpress(username, password):
    # Navigate to WordPress dashboard
    driver.get(login_url)
    time.sleep(2)

    # Load cookies if they exist
    if os.path.exists(COOKIE_FILE):
        log("Loading cookies...")
        with open(COOKIE_FILE, "rb") as cookie_file:
            cookies = pickle.load(cookie_file)
            for cookie in cookies:
                cookie['domain'] = ".gardenersworld.production.wcp.imdserve.com"  # Ensure domain is set
                driver.add_cookie(cookie)

        # Refresh and check if session is valid
        driver.get(login_url)
        time.sleep(2)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "wp-admin-bar-my-account"))
            )
            log("Session restored with cookies. Already logged in.")
            return
        except Exception as e:
            log(f"Cookies expired or invalid: {e}. Proceeding to login.")

    # Perform login
    driver.get(login_url)
    time.sleep(2)

    # Enter username and password
    driver.find_element(By.ID, "user_login").send_keys(username)
    driver.find_element(By.ID, "user_pass").send_keys(password)
    driver.find_element(By.ID, "wp-submit").click()
    time.sleep(2)

    # Handle OTP if required
    try:
        log("Waiting for OTP input field...")
        otp_field_present = wait_for_element("#googleotp", By.CSS_SELECTOR, timeout=15)
        if otp_field_present:
            log("OTP input field detected. Please enter the code in the terminal.")
            otp_code = get_google_authenticator_code_from_user()
            otp_input = driver.find_element(By.CSS_SELECTOR, "#googleotp")
            otp_input.send_keys(otp_code)
            input("Press Enter to submit the OTP...")
            driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
            log("OTP submitted. Waiting for the dashboard...")
            time.sleep(3)
    except Exception as e:
        log(f"Error handling OTP: {e}")

    # Save cookies after successful login
    log("Saving cookies...")
    with open(COOKIE_FILE, "wb") as cookie_file:
        pickle.dump(driver.get_cookies(), cookie_file)
    log("Cookies saved.")

    log("Login process completed.")