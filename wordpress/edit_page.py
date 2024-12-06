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
from utils.normalize import normalize_text

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
        button_links_updated =update_button(driver, csv_file, anchors, page_url,)
        
        
        if (button_links_updated ):
            log(f"Updating page: {page_url}")
            
            retry(lambda: WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save')]"))
            ).click())
            WebDriverWait(driver, 20).until(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".components-snackbar__content"), "Page updated.")
            )
            log(f"Page updated for {page_url}")
        else:
            log(f"No changes made to the page: {page_url}")
    except Exception as e:
        log(f"Error processing Gutenberg page {page_url}: {e}")

def update_button(driver, csv_file, anchors, page_url):
    link_updates = []  # To collect results for CSV writing
    links_updated = False
    js_script = """
    let updates = {};
    document.querySelectorAll('.acf-field input[type="text"]').forEach(field => {
        updates[field.getAttribute('name')] = {
            text: field.value,
            element: field
        };
    });
    return updates;
    """
    acf_fields = driver.execute_script(js_script)

    for anchor in anchors:
        anchor_text = anchor["Anchor Text"]
        broken_href = anchor["Broken HREF"]
        new_href = anchor["New Href"]
        trimmed_new_href = get_domain_and_append_path(new_href)
        trimmed_broken_href = get_domain_and_append_path(broken_href)
        matched = False
        same_anchor = False

        for field in acf_fields:
            if normalize_text(acf_fields[field]['text']) == normalize_text(anchor_text):
                # Get index of the anchor text
                current_index = list(acf_fields.keys()).index(field)
                next_index = current_index + 1
                # Get the text of the next field
                next_field = list(acf_fields.keys())[next_index]
                current_href = acf_fields[next_field]['text']
                trimmed_current_href = get_domain_and_append_path(current_href)
                log(f"Found matching anchor text '{anchor_text}'.")
                log(f"Current href: '{current_href}', Trimmed href: '{trimmed_current_href}'")
                same_anchor = True

                if current_href in {broken_href, trimmed_broken_href} or trimmed_current_href in {broken_href, trimmed_broken_href}:
                    matched = True
                    # Update the link using Selenium instead of JS
                    log(f"Updating href from '{current_href}' to '{new_href}'.")
                    try:
                        input_field = acf_fields[next_field]['element']
                        driver.execute_script("arguments[0].focus();", input_field)  # Focus the field
                        input_field.clear()  # Clear existing value
                        input_field.send_keys(new_href)  # Type the new value
                        input_field.send_keys("\t")  # Simulate tabbing out to trigger change
                        links_updated = True
                        log(f"Replaced href '{current_href}' with '{new_href}' for '{anchor_text}'.")
                        link_updates.append({
                            "Page URL": page_url,
                            "Anchor Text": anchor_text,
                            "Broken HREF": broken_href,
                            "New HREF": new_href,
                            "Status": "Updated"
                        })
                    except Exception as e:
                        log(f"Failed to update href for '{anchor_text}': {e}")
                    break
                elif current_href in {new_href, trimmed_new_href} or trimmed_current_href in {new_href, trimmed_new_href}:
                    matched = True
                    log(f"'{anchor_text}' with href '{new_href}' is already updated.")
                    link_updates.append({
                        "Page URL": page_url,
                        "Anchor Text": anchor_text,
                        "Broken HREF": broken_href,
                        "New HREF": new_href,
                        "Status": "Already Updated"
                    })
                    break
        if not matched:
            if not same_anchor:
                log(f"Checking iframe for '{anchor_text}' on {page_url}.")
                iframe_updated = update_iframe(driver, csv_file, [anchor], page_url)
                if iframe_updated:
                    links_updated = True
                else:
                    log(f"no matching anchor text found for '{anchor_text}' on {page_url}.")
                    link_updates.append({
                        "Page URL": page_url,
                        "Anchor Text": anchor_text,
                        "Broken HREF": broken_href,
                        "New HREF": new_href,
                        "Status": "Anchor text not found"
                    })
            else:
                log(f"No matching broken href found for '{anchor_text}' on {page_url}.")
                link_updates.append({
                "Page URL": page_url,
                "Anchor Text": anchor_text,
                "Broken HREF": broken_href,
                "New HREF": new_href,
                "Status": "HREF not found"
                })
    # Write all results to the CSV in one go
    for result in link_updates:
        write_results_to_csv_row(result, csv_file)

    return links_updated



def update_iframe(driver, csv_file, anchors, page_url):
    try:
        # Locate the iframe and switch to it
        iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)
        log("Switched to the iframe.")

        # JavaScript to update links directly and collect results
        js_script = """
        let updates = [];
        document.querySelectorAll('a').forEach((anchor, index) => {
            let uniqueId = `anchor-${index}`;
            anchor.setAttribute('data-id', uniqueId); // Assign unique ID
            updates.push({
                id: uniqueId,
                text: anchor.innerText.trim(),
                href: anchor.href.trim()
            });
        });
        return updates;
        """
        anchors_on_page = driver.execute_script(js_script)

        # Process and update links
        updated_links = []
        links_updated = False
        for anchor in anchors:
            anchor_text = anchor["Anchor Text"]
            broken_href = anchor["Broken HREF"]
            trimmed_current_href = get_domain_and_append_path(broken_href)
            new_href = anchor["New Href"]
            trimmed_new_href = get_domain_and_append_path(new_href)
            matched = False
            same_anchor = False
            for page_anchor in anchors_on_page:
                if normalize_text(page_anchor['text']) == normalize_text(anchor_text):
                    same_anchor = True
                    current_href = page_anchor['href']
                    trimmed_current_href = get_domain_and_append_path(current_href)
                    if current_href in {broken_href,trimmed_current_href} or trimmed_current_href in {broken_href,trimmed_current_href}:
                        matched = True
                        # Update the link
                        driver.execute_script("""
                            let anchor = document.querySelector(`a[data-id='${arguments[0]}']`);
                            let newHref = arguments[1];
                            anchor.href = newHref;
                            anchor.setAttribute("data-mce-href", newHref);
                            ['input', 'change', 'blur', 'keyup', 'mousedown', 'mouseup', 'focus'].forEach(event =>
                                anchor.dispatchEvent(new Event(event, { bubbles: true }))
                            );
                        """, page_anchor['id'], new_href)
                        links_updated = True
                        log(f"Replaced href '{current_href}' with '{new_href}' for '{anchor_text}'.")
                        updated_links.append({
                            "Page URL": page_url,
                            "Anchor Text": anchor_text,
                            "Broken HREF": anchor["Broken HREF"],
                            "New HREF": anchor["New Href"],
                            "Status": "Updated"
                        })
                        break
                    elif current_href in {new_href,trimmed_new_href} or trimmed_new_href in {new_href,trimmed_new_href}:
                        matched = True
                        log(f"'{anchor_text}' with href '{new_href}' is already updated.")
                        updated_links.append({
                            "Page URL": page_url,
                            "Anchor Text": anchor_text,
                            "Broken HREF": anchor["Broken HREF"],
                            "New HREF": anchor["New Href"],
                            "Status": "Already Updated"
                        })
                        break
            if not matched:
                if not same_anchor:
                    log(f"not matching anchor text found in iframe for '{anchor_text}' on {page_url}.")
                else :
                    log(f"No matching broken href found in iframe for '{anchor_text}' on {page_url}.")
                    updated_links.append({
                        "Page URL": page_url,
                        "Anchor Text": anchor_text,
                        "Broken HREF": anchor["Broken HREF"],
                        "New HREF": anchor["New Href"],
                        "Status": "HREF not found"
                    })

        # Write results to the CSV
        for result in updated_links:
            write_results_to_csv_row(result, csv_file)

    except Exception as e:
        log(f"Error processing iframe for {page_url}: {e}")

    finally:
        driver.switch_to.default_content()  # Always return to the main content
        log("Switched back to the main content.")
        return links_updated
