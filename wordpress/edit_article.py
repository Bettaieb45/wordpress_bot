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
def extract_links_from_page(driver):
    # Locate all iframes on the page
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        log(f"Found {len(iframes)} iframe(s) on the page.")
        
        page_anchors = []  # To store all links from all iframes
        
        for index, iframe in enumerate(iframes):
            try:
                
                
                driver.switch_to.frame(iframe)

                # Wait for iframe content to load
                time.sleep(1)
                
                # Check if iframe has content
                iframe_content = driver.execute_script("return document.body.innerHTML;")
                if not iframe_content.strip():
                    driver.switch_to.default_content()
                    continue

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
                # Append iframe index to each anchor
                for link in links_in_iframe:
                    link["iframe_index"] = index  # Store iframe index
                    page_anchors.append(link)
                
                # Switch back to the main content after processing
                driver.switch_to.default_content()
            except Exception as iframe_error:
                log(f"Error processing iframe {index + 1}: {iframe_error}")
                driver.switch_to.default_content()
        return page_anchors, iframes
def handle_edit_article(page_url, anchors, csv_file):
    log(f"Handling edit article for {page_url}")
    try:
        page_anchors,iframes = extract_links_from_page(driver)
        # Update links logic
        link_updates = []
        links_updated = False
        for anchor in anchors:
            anchor_text = anchor["Anchor Text"]
            broken_href = anchor["Broken HREF"]
            trimmed_broken_href = get_domain_and_append_path(broken_href)
            new_href = anchor["New Href"]
            trimmed_new_href = get_domain_and_append_path(new_href)
            same_anchor = False
            matched = False
            for page_anchor in page_anchors:
                if normalize(page_anchor["text"]) == normalize(anchor_text):
                    log(f"Found matching anchor text '{anchor_text}' on {page_url}.")
                    same_anchor = True
                    current_href = page_anchor["href"]
                    trimmed_current_href = get_domain_and_append_path(current_href)
                    if current_href in {broken_href, trimmed_broken_href} or trimmed_current_href in {broken_href, trimmed_broken_href}:
                        log(f"Found matching broken href '{broken_href}' on {page_url}.")
                        
                        # Switch to the correct iframe
                        iframe_index = page_anchor["iframe_index"]
                        log(f"Switching to iframe {iframe_index + 1} for updating anchor.")
                        driver.switch_to.frame(iframes[iframe_index])
                        
                        # Update the anchor
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
                            """, page_anchor['id'], new_href)
                        
                        # Switch back to main content
                        
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
                    elif current_href in {new_href, trimmed_new_href} or trimmed_current_href in {new_href, trimmed_new_href}:
                        matched = True
                        log(f"Link for '{anchor_text}' already updated.")
                        link_updates.append({
                            "Page URL": page_url,
                            "Anchor Text": anchor_text,
                            "Broken HREF": broken_href,
                            "New HREF": new_href,
                            "Status": "Already Updated"
                        })
            if not matched:
                if not same_anchor:
                    log(f"Link for '{anchor_text}' not found.")
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
            # Update the post only if links were updated
                driver.execute_script("window.scrollTo(0, 0)")
                retry(lambda: WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "publish"))
                ).click())
                log(f"Post updated for {page_url}. Waiting for changes to propagate...")
                WebDriverWait(driver, 5).until(
                    EC.text_to_be_present_in_element((By.ID, "message"), "Post updated")
                )
        else:
            log(f"No links were updated for {page_url}. Skipping update action.")
        
        #verify if the links were updated
        new_page_anchors,new_iframes = extract_links_from_page(driver)
        for links in link_updates:
            if links["Status"] == "Updated":
                for new_page_anchor in new_page_anchors:
                    if normalize(new_page_anchor["text"]) == normalize(links["Anchor Text"]):
                        if new_page_anchor["href"] == links["New HREF"]:
                            log(f"Link for '{links['Anchor Text']}' was successfully updated.")
                            break
                else:
                    log(f"Link for '{links['Anchor Text']}' was not updated.")
                    #change the status to not Updated if the link was not updated
                    links["Status"] = "Not Updated"
        for results in link_updates:
            write_results_to_csv_row(results, csv_file)
    except Exception as e:
        log(f"Error in handling edit article for {page_url}: {e}")
