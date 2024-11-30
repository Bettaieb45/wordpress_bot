    
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import utils.retry as retry
from utils.logger import log
from config import driver
import utils.append_csv as write_results_to_csv_row

## I need the driver from conifg.py file

def handle_edit_article(page_url, anchors, csv_file):
    log(f"Processing 'Edit Article' page: {page_url}")
    try:
        # Interact with the editor iframe
        log("Locating and interacting with the editor iframe.")
        iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "content_ifr"))
        )
        driver.switch_to.frame(iframe)
        log("Switched to the editor iframe.")

        # Track if any links were updated
        links_updated = False

        # Use JavaScript to find and update anchor tags
        for anchor in anchors:
            anchor_text = anchor["Anchor Text"]
            broken_href = anchor["Broken HREF"]
            new_href = anchor["New Href"]

            js_script = f"""
            let status = "Not found";
            document.querySelectorAll('a').forEach(anchor => {{
                if (anchor.innerText.trim() === "{anchor_text}") {{
                    if (anchor.href.trim() === "{broken_href}") {{
                        // Update the link
                        const newHref = "{new_href}";
                        anchor.href = newHref;
                        anchor.setAttribute("data-mce-href", newHref);

                        // Trigger WordPress change detection
                        const events = ['input', 'change', 'blur', 'keyup', 'mousedown', 'mouseup', 'focus'];
                        events.forEach(event => anchor.dispatchEvent(new Event(event, {{ bubbles: true }})));
                        status = "Updated";
                    }} else if (anchor.href.trim() === "{new_href}") {{
                        // Already updated
                        status = "Already updated";
                    }}
                }}
            }});
            return status;
            """
            status = driver.execute_script(js_script)
            if status == "Updated":
                links_updated = True
                log(f"Replaced href '{broken_href}' with '{new_href}' for '{anchor_text}'.")
            elif status == "Already updated":
                log(f"'{anchor_text}' with href '{new_href}' is already updated.")
            else:
                log(f"No matching anchor text or broken href found for '{anchor_text}' on {page_url}.")
            result_row = {
                "Page URL": page_url,
                "Anchor Text": anchor_text,
                "Broken HREF": broken_href,
                "New HREF": new_href,
                "Status": status
            }
            write_results_to_csv_row(result_row, csv_file)
          

        driver.switch_to.default_content()
        log("Switched back to the main content.")

        if links_updated:
            # Update the post only if links were updated
            retry(lambda: WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "publish"))
            ).click())
            log(f"Post updated for {page_url}. Waiting for changes to propagate...")
            time.sleep(15)
        else:
            log(f"No links were updated for {page_url}. Skipping update action.")

    except Exception as e:
        log(f"Error processing 'Edit Article' page {page_url}: {e}")
    log(f"Completed processing 'Edit Article' page: {page_url}")