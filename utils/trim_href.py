from urllib.parse import urlparse
from config import login_url

def get_domain_and_append_path(url):
    """
    Extracts the domain from the URL and appends the path to it.

    Args:
        url (str): The full URL.

    Returns:
        str: A new URL with the domain and the extracted path.
    """
    parsed_url = urlparse(url)
    parsed_login = urlparse(login_url)
    domain = f"{parsed_login.scheme}://{parsed_login.netloc}"  # Extract scheme and netloc
    path = parsed_url.path  # Extract the path
    return f"{domain}{path}"  # Combine the domain and path