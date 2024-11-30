from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from utils.retry import retry
from utils.logger import log
from config import driver 
from utils.append_csv import write_results_to_csv_row
from utils.trim_href import get_domain_and_append_path
def handle_edit_page(page_url, anchors, csv_file):
    log(f"Processing 'Edit Page' for Gutenberg: {page_url}")
    try:
        # Wait for Gutenberg editor to load
        log("Waiting for Gutenberg editor to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".edit-post-header"))
        )
        log("Gutenberg editor loaded.")
        # Process ACF fields on the page
        process_gutenberg_page(page_url, anchors, csv_file)
    except Exception as e:
        log(f"Error loading Gutenberg editor for {page_url}: {e}")
    log(f"Completed processing 'Edit Page' for Gutenberg: {page_url}")

# Process ACF fields on Gutenberg pages
def process_gutenberg_page(page_url, anchors, csv_file):
    log(f"Processing Gutenberg page: {page_url}")
    try:
        # Wait for Gutenberg editor and ACF fields to become visible
        log("Waiting for ACF fields and full page render...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='text']"))
        )
        time.sleep(3)  # Fallback wait to ensure all dynamic elements are rendered
        log("ACF fields are visible and the page is fully loaded.")

        # Use JavaScript to dynamically search and update ACF fields
        there_is_an_update = False
        for anchor in anchors:
            anchor_text = anchor["Anchor Text"]
            broken_href = anchor["Broken HREF"]
            new_href = anchor["New Href"]
            trimmed_broken_href = get_domain_and_append_path(broken_href)
            print(f"trimmed_broken_href: {trimmed_broken_href}")
            # Normalize URLs and update them using JavaScript
            js_script = f"""
            let status = "Not found";
            document.querySelectorAll('input[type="text"]').forEach(field => {{
                let normalize = (url) => url.replace(/\\/$/, '');  // Remove trailing slash
                if (normalize(field.value) === normalize("{broken_href}")) {{
                    field.value = "{new_href}";
                    status = "Updated";
                    // Trigger WordPress change detection
                    const events = ['input', 'change'];
                    events.forEach(event => field.dispatchEvent(new Event(event, {{ bubbles: true }})));
                }} else if (normalize(field.value) === normalize("{trimmed_broken_href}")) {{
                    field.value = "{new_href}";
                    status = "Updated";
                    // Trigger WordPress change detection
                    const events = ['input', 'change'];
                    events.forEach(event => field.dispatchEvent(new Event(event, {{ bubbles: true }})));
                }}else if (normalize(field.value) === normalize("{new_href}")) {{
                    status = "Already updated";
                }}
            }});
            if (status === "Updated") {{
                return status;
            }}else{{
                document.querySelectorAll('iframe').forEach(iframe => {{
                const doc = iframe.contentDocument || iframe.contentWindow.document;
                doc.querySelectorAll('a').forEach(anchor=>{{
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
                        }} else if (anchor.href.trim() === "{trimmed_broken_href}") {{
                            // Update the link
                            const newHref = "{new_href}";
                            anchor.href = newHref;
                            anchor.setAttribute("data-mce-href", newHref);
                            // Trigger WordPress change detection
                            const events = ['input', 'change', 'blur', 'keyup', 'mousedown', 'mouseup', 'focus'];
                            events.forEach(event => anchor.dispatchEvent(new Event(event, {{ bubbles: true }})));
                            status = "Updated";
                        }}else if (anchor.href.trim() === "{new_href}") {{
                            // Already updated
                            status = "Already updated";
                        }}
                    }}
                }});
                }});

            }}
            return status;
            """
            status = driver.execute_script(js_script)
            if status == "Updated":
                log(f"Updated link from '{broken_href}' to '{new_href}' for '{anchor_text}'.")
                result_row = {
                    "Page URL": page_url,
                    "Anchor Text": anchor_text,
                    "Broken HREF": broken_href,
                    "New HREF": new_href,
                    "Status": status
                }
                there_is_an_update = True
            elif status == "Already updated":
                log(f"Link '{new_href}' is already updated for '{anchor_text}'.")
                result_row = {
                    "Page URL": page_url,
                    "Anchor Text": anchor_text,
                    "Broken HREF": broken_href,
                    "New HREF": new_href,
                    "Status": status
            }
            else:
                log(f"Link not found for '{anchor_text}' on {page_url}.")
                result_row = {
                    "Page URL": page_url,
                    "Anchor Text": anchor_text,
                    "Broken HREF": broken_href,
                    "New HREF": new_href,
                    "Status": "Not found"
            }
            write_results_to_csv_row(result_row, csv_file)


        # Save changes if any link was updated
        if (there_is_an_update):
            log(f"Updating page: {page_url}")
            
            retry(lambda: WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save')]"))
            ).click())
            log(f"Page updated for {page_url}")
            time.sleep(5)
        else:
            log(f"No changes made to the page: {page_url}")

    except Exception as e:
        log(f"Error processing Gutenberg page {page_url}: {e}")