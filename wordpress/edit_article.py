from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.retry import retry
from utils.logger import log
from config import driver
from utils.append_csv import write_results_to_csv_row
from utils.trim_href import get_domain_and_append_path


def handle_edit_article(page_url, anchors, csv_file):
    log(f"Processing 'Edit Article' page: {page_url}")
    try:
        # Locate and interact with the editor iframe
        log("Locating and interacting with the editor iframe.")
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "content_ifr"))
        )
        driver.switch_to.frame(iframe)
        log("Switched to the editor iframe.")

        links_updated = False
        link_updates = []  # To collect results for CSV writing

        # Batch JavaScript processing
        js_script = """
        let updates = [];
        document.querySelectorAll('a').forEach(anchor => {
            let status = "Not found";
            updates.push({
                text: anchor.innerText.trim(),
                href: anchor.href.trim(),
                element: anchor
            });
        });
        return updates;
        """
        anchors_on_page = driver.execute_script(js_script)
        print(anchors_on_page)
        for anchor in anchors:
            anchor_text = anchor["Anchor Text"]
            broken_href = anchor["Broken HREF"]
            new_href = anchor["New Href"]
            trimmed_broken_href = get_domain_and_append_path(broken_href)
            trimed_new_href=get_domain_and_append_path(new_href)
            print(f"trimmed broken href",trimmed_broken_href)
            # Process all matching links in the page
            matched = False
            for page_anchor in anchors_on_page:
                if page_anchor['text'] == anchor_text:
                    current_href = page_anchor['href']
                    if current_href in {broken_href, trimmed_broken_href}:
                        matched = True
                        # Update the link
                        driver.execute_script("""
                            let anchor = arguments[0];
                            let newHref = arguments[1];
                            anchor.href = newHref;
                            anchor.setAttribute("data-mce-href", newHref);
                            ['input', 'change', 'blur', 'keyup', 'mousedown', 'mouseup', 'focus'].forEach(event =>
                                anchor.dispatchEvent(new Event(event, { bubbles: true }))
                            );
                        """, page_anchor['element'], new_href)
                        links_updated = True
                        log(f"Replaced href '{current_href}' with '{new_href}' for '{anchor_text}'.")
                        link_updates.append({
                            "Page URL": page_url,
                            "Anchor Text": anchor_text,
                            "Broken HREF": broken_href,
                            "New HREF": new_href,
                            "Status": "Updated"
                        })
                        break
                    elif current_href == new_href:
                        matched = True
                        log(f"'{anchor_text}' with href '{new_href,trimed_new_href}' is already updated.")
                        link_updates.append({
                            "Page URL": page_url,
                            "Anchor Text": anchor_text,
                            "Broken HREF": broken_href,
                            "New HREF": new_href,
                            "Status": "Already updated"
                        })
                        break

            if not matched:
                log(f"No matching anchor text or broken href found for '{anchor_text}' on {page_url}.")
                link_updates.append({
                    "Page URL": page_url,
                    "Anchor Text": anchor_text,
                    "Broken HREF": broken_href,
                    "New HREF": new_href,
                    "Status": "Not found"
                })

        # Write all results to the CSV in one go
        for result in link_updates:
            write_results_to_csv_row(result, csv_file)

        driver.switch_to.default_content()
        log("Switched back to the main content.")

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

    except Exception as e:
        log(f"Error processing 'Edit Article' page {page_url}: {e}")
    log(f"Completed processing 'Edit Article' page: {page_url}")
