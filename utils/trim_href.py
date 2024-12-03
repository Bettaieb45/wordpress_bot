from urllib.parse import urlparse, urlunparse
from config import login_url
def get_domain_and_append_path(url):
    """
    Extracts the domain from the login_url and appends the full path (including query) from the given URL.

    Args:
        url (str): The full URL to process.

    Returns:
        str: A new URL with the domain from login_url and the original path and query from the provided URL.
    """
    parsed_url = urlparse(url)
    parsed_login = urlparse(login_url)
    
    # Combine scheme and netloc from login_url with the path and query from the original URL
    trimmed_url = urlunparse((
        parsed_login.scheme,  # Use the scheme from login_url
        parsed_login.netloc,  # Use the domain from login_url
        parsed_url.path,      # Use the path from the given URL
        '',                   # Keep params empty
        parsed_url.query,     # Use the query from the given URL
        ''                    # Keep fragment empty
    ))
    
    return trimmed_url
