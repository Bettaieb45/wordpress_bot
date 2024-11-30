from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
from utils.retry import retry
from utils.logger import log
from config import driver 
from wordpress.edit_page import handle_edit_page
from wordpress.edit_article import handle_edit_article
from utils.append_csv import write_results_to_csv_row
def update_links(posts_dict, output_csv_path):

    with open(output_csv_path, 'a', newline='') as csv_file:
        fieldnames = ["Page URL", "Anchor Text", "Broken HREF", "New HREF", "Status"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for page_url, anchors in posts_dict.items():
            log(f"Processing page: {page_url}")
            driver.get(page_url)
            time.sleep(3)  # Small delay to allow the page to load

        # Check for "Edit Article" button
            edit_article_buttons = driver.find_elements(By.LINK_TEXT, "Edit Article")
            if edit_article_buttons:
                log(f"'Edit Article' button found for {page_url}.")
                retry(lambda: edit_article_buttons[0].click())
                handle_edit_article(page_url, anchors, csv_file)
                continue  # Move to the next page after processing

        # Check for "Edit Page" button
            edit_page_buttons = driver.find_elements(By.LINK_TEXT, "Edit Page")
            if edit_page_buttons:
                log(f"'Edit Page' button found for {page_url}.")
                retry(lambda: edit_page_buttons[0].click())
                handle_edit_page(page_url, anchors, csv_file)
                continue  # Move to the next page after processing
        # Check for "Edit Plant Records" button
            edit_plant_record_buttons = driver.find_elements(By.LINK_TEXT, "Edit Plant Records")
            if edit_plant_record_buttons:
                log(f"'Edit Plant Records' button found for {page_url}.")
                retry(lambda: edit_plant_record_buttons[0].click())
                handle_edit_article(page_url, anchors, csv_file)
                continue
        # Check for "Edit List" button
            edit_list_buttons = driver.find_elements(By.LINK_TEXT, "Edit List")
            if edit_list_buttons:
                log(f"'Edit List' button found for {page_url}.")
                retry(lambda: edit_list_buttons[0].click())
                handle_edit_article(page_url, anchors, csv_file)
                continue
        
        # If neither button is found
            log(f"No 'Edit Article' , 'Edit Page','Edit Plant Records' or 'Edit List' button found for {page_url}. Skipping page.")
            for anchor in anchors:
                    write_results_to_csv_row({
                        "Page URL": page_url,
                        "Anchor Text": anchor["Anchor Text"],
                        "Broken HREF": anchor["Broken HREF"],
                        "New HREF": anchor["New Href"],
                        "Status": "Not identifiable"
                    }, csv_file)

