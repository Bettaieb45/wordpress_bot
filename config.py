from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os
from dotenv import load_dotenv
load_dotenv()
username = os.getenv("WP_USERNAME")
password = os.getenv("WP_PASSWORD")
output_csv_path = os.getenv("OUTPUT_CSV_PATH")
input_csv_path = os.getenv("INPUT_CSV_PATH")
driver = webdriver.Chrome(service=Service('/usr/local/bin/chromedriver'))
COOKIE_FILE = os.getenv("COOKIE_FILE")
login_url = os.getenv("LOGIN_URL")
