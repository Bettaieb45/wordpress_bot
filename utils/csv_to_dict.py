from collections import defaultdict
import csv
# Process CSV
def process_csv_to_dict(csv_path):
    posts_dict = defaultdict(list)
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            page_url = row["Host URL with broken links"]
            posts_dict[page_url].append({
                "Anchor Text": row["Anchor"],
                "Broken HREF": row["Broken internal link"],
                "New Href": row["Update internal link to"]
            })
    return posts_dict