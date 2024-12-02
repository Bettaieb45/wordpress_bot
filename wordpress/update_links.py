from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from utils.retry import retry
from utils.logger import log
from config import driver
from wordpress.edit_page import handle_edit_page
from wordpress.edit_article import handle_edit_article
from utils.append_csv import write_results_to_csv_row


def update_links(posts_dict, output_csv_path):
    button_actions = [
        {"text": "Edit Article", "handler": handle_edit_article},
        {"text": "Edit Page", "handler": handle_edit_page},
        {"text": "Edit Plant Records", "handler": handle_edit_article},
        {"text": "Edit List", "handler": handle_edit_article},
        {"text": "Edit Reviews", "handler": handle_edit_article},
    ]

    with open(output_csv_path, 'a', newline='') as csv_file:
        fieldnames = ["Page URL", "Anchor Text", "Broken HREF", "New HREF", "Status"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for page_url, anchors in posts_dict.items():
            log(f"Processing page: {page_url}")
            driver.get(page_url)

            try:
                # Wait for the page to load (configurable timeout)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except Exception as e:
                log(f"Page failed to load for {page_url}: {e}")
                for anchor in anchors:
                    write_results_to_csv_row({
                        "Page URL": page_url,
                        "Anchor Text": anchor["Anchor Text"],
                        "Broken HREF": anchor["Broken HREF"],
                        "New HREF": anchor["New Href"],
                        "Status": "Page load failed"
                    }, csv_file)
                continue

            # Try all button actions in order
            processed = False
            for action in button_actions:
                buttons = driver.find_elements(By.LINK_TEXT, action["text"])
                if buttons:
                    log(f"'{action['text']}' button found for {page_url}.")
                    retry(lambda: buttons[0].click())
                    action["handler"](page_url, anchors, csv_file)
                    processed = True
                    break

            if not processed:
                log(f"No identifiable button found for {page_url}. Skipping page.")
                for anchor in anchors:
                    write_results_to_csv_row({
                        "Page URL": page_url,
                        "Anchor Text": anchor["Anchor Text"],
                        "Broken HREF": anchor["Broken HREF"],
                        "New HREF": anchor["New Href"],
                        "Status": "Not identifiable"
                    }, csv_file)
