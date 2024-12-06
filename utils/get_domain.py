from urllib.parse import urlparse
def get_domain(url):
    """
    Extracts the domain from the given URL.

    Args:
        url (str): The full URL to process.

    Returns:
        str: The domain extracted from the URL.
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc