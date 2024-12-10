from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import log
from config import driver
from utils.trim_href import get_domain_and_append_path
from utils.normalize import normalize_text as normalize
from utils.append_csv import write_results_to_csv_row
import time
from utils.retry import retry


def extract_links_from_page(driver,page_url,anchors):
    """Extracts all links from the main page and iframes."""
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    log(f"Found {len(iframes)} iframe(s) on the page.")
    
    page_anchors = []  # To store all links from all iframes

    for index, iframe in enumerate(iframes):
        try:
            driver.switch_to.frame(iframe)
            log(f"Switched to iframe {index + 1}")

            # Wait for iframe content to load
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # Collect anchor data
            js_script = """
                let updates = [];
                document.querySelectorAll('a').forEach((anchor, index) => {
                    let uniqueId = `iframe-${arguments[0]}-anchor-${index}`;
                    anchor.setAttribute('data-id', uniqueId); // Assign unique ID
                    updates.push({
                        id: uniqueId,
                        text: anchor.innerText.trim(),
                        href: anchor.href.trim()
                    });
                });
                return updates;
            """
            links_in_iframe = driver.execute_script(js_script, index)
            for link in links_in_iframe:
                link["iframe_index"] = index  # Store iframe index
                page_anchors.append(link)

            driver.switch_to.default_content()
        except Exception as iframe_error:
            log(f"Error processing iframe {index + 1}: {iframe_error}")
            driver.switch_to.default_content()
            for anchor in anchors :
                write_results_to_csv_row({
                    "Page URL": page_url,
                    "Anchor Text": anchor["Anchor Text"],
                    "Broken HREF": anchor["Broken HREF"],
                    "New HREF": anchor["New Href"],
                    "Status": "Error processing iframe"
                })
            
    
    return page_anchors, iframes


def handle_edit_article(page_url, anchors, csv_file):
    """Handles editing an article by updating broken links."""
    log(f"Handling edit article for {page_url}")
    try:
        # Extract all links from the page
        page_anchors, iframes = extract_links_from_page(driver,page_url,anchors)
        page_anchor_map = {normalize(anchor["text"]): anchor for anchor in page_anchors}

        link_updates = []
        links_updated = False

        for anchor in anchors:
            anchor_text = anchor["Anchor Text"]
            broken_href = get_domain_and_append_path(anchor["Broken HREF"])
            new_href = anchor["New Href"]
            trimmed_new_href = get_domain_and_append_path(new_href)

            same_anchor = normalize(anchor_text) in page_anchor_map
            matched = False

            if same_anchor:
                page_anchor = page_anchor_map[normalize(anchor_text)]
                current_href = get_domain_and_append_path(page_anchor["href"])

                if current_href == trimmed_new_href:
                    log(f"Link for '{anchor_text}' already updated on {page_url}.")
                    link_updates.append({
                        "Page URL": page_url,
                        "Anchor Text": anchor_text,
                        "Broken HREF": broken_href,
                        "New HREF": new_href,
                        "Status": "Already Updated"
                    })
                    matched = True
                    continue
                elif current_href == broken_href:
                    iframe_index = page_anchor["iframe_index"]
                    try:
                        driver.switch_to.frame(iframes[iframe_index])
                        log(f"Switched to iframe {iframe_index + 1} for updating anchor.")

                        # Update the anchor link
                        driver.execute_script("""
                        let anchor = document.querySelector(`a[data-id='${arguments[0]}']`);
                        if (anchor) {
                            let newHref = arguments[1];
                            anchor.href = newHref;
                            anchor.setAttribute("data-mce-href", newHref);
                            ['input', 'change', 'blur', 'keyup', 'mousedown', 'mouseup', 'focus'].forEach(event =>
                                anchor.dispatchEvent(new Event(event, { bubbles: true }))
                            );
                        } else {
                            throw new Error(`Anchor with data-id '${arguments[0]}' not found.`);
                        }
                    """, page_anchor["id"], new_href)

                        driver.switch_to.default_content()
                        links_updated = True
                        matched = True
                        log(f"Replaced href '{current_href}' with '{new_href}' for '{anchor_text}'.")
                        link_updates.append({
                            "Page URL": page_url,
                            "Anchor Text": anchor_text,
                            "Broken HREF": broken_href,
                            "New HREF": new_href,
                            "Status": "Updated"
                        })
                    except Exception as update_error:
                        log(f"Error updating link for '{anchor_text}' on {page_url}: {update_error}")
                        driver.switch_to.default_content()
                        write_results_to_csv_row({
                        "Page URL": page_url,
                        "Anchor Text": anchor_text,
                        "Broken HREF": broken_href,
                        "New HREF": new_href,
                        "Status": "Error updating link"
                        }, csv_file)

                
            if not matched:
                if not same_anchor:
                    log(f"Anchor text '{anchor_text}' not found on {page_url}.")
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

        if links_updated:
            retry(lambda: WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "publish"))
            ).click())
            log(f"Post updated for {page_url}. Waiting for changes to propagate...")
            WebDriverWait(driver, 5).until(
                EC.text_to_be_present_in_element((By.ID, "message"), "Post updated")
            )
        else:
            log(f"No links were updated for {page_url}. Skipping update action.")

        # Verify link updates
        new_page_anchors, _ = extract_links_from_page(driver)
        for update in link_updates:
            if update["Status"] == "Updated":
                for new_anchor in new_page_anchors:
                    if normalize(new_anchor["text"]) == normalize(update["Anchor Text"]) and \
                            new_anchor["href"] == update["New HREF"]:
                        log(f"Link for '{update['Anchor Text']}' was successfully updated.")
                        break
                else:
                    log(f"Link for '{update['Anchor Text']}' was not updated.")
                    update["Status"] = "Not Updated"

        # Write results to CSV
        for result in link_updates:
            write_results_to_csv_row(result, csv_file)

    except Exception as e:
        log(f"Error in handling edit article for {page_url}: {e}")
        for result in link_updates:
            write_results_to_csv_row(result, csv_file)
