import csv
from utils.logger import log
def write_results_to_csv_row(row, csv_file):
    """Append a single row to the CSV."""
    fieldnames = ["Page URL", "Anchor Text", "Broken HREF", "New HREF", "Status"]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writerow(row)
    log(f"Appended row to CSV: {row}")
# Handle "Edit Article"