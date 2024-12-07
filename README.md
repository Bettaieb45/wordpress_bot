WordPress Bot Project

Overview

This project automates the process of managing WordPress posts, specifically focusing on updating internal links based on CSV input data. It uses Selenium for web interaction, processes data from CSV files, and supports secure operations with VPN integration. The bot ensures efficient and automated updates for WordPress administrators.

Features

Login Automation: Logs into WordPress securely, with support for Google Authenticator OTP.

CSV Processing: Reads and processes CSV files to identify and update broken links in WordPress posts.

Link Update Automation: Automates the update of internal links based on input data.

VPN Integration: Ensures secure operations using NordVPN.

Logging: Provides real-time logs with timestamps for tracking and debugging.

Project Structure

Root Files

.gitignore: Specifies files and directories to ignore in version control.

README.md: Documentation for the project (this file).

config.py: Stores configuration settings, including credentials, file paths, and Selenium WebDriver setup.

main.py: Entry point of the application.

Utility Scripts

utils/append_csv.py

Handles appending data to existing CSV files, ensuring data consistency during updates.

utils/csv_to_dict.py

Processes CSV files and converts them into a dictionary format, organizing data for further operations.

utils/get_domain.py

Extracts domain names from URLs, useful for grouping and validating data by domain.

utils/logger.py

Provides a logging utility to output messages with timestamps, aiding in debugging and monitoring.

utils/login.py

Manages automated login to WordPress, including:

Navigating to the login page.

Handling credentials securely.

Supporting multi-factor authentication (MFA) with Google Authenticator.

utils/nordvpn.py

Automates reconnecting to NordVPN to ensure secure operations.

WordPress Scripts

wordpress/update_links.py: Core functionality for updating links in WordPress posts based on the processed CSV data.

Prerequisites

Python 3.8 or higher

Selenium WebDriver

NordVPN CLI installed

Google Chrome or a compatible browser

CSV file containing the following columns:

Host URL with broken links

Anchor

Broken internal link

Update internal link to

Setup

Install Dependencies:

pip install -r requirements.txt

Configure config.py:

Set WordPress credentials (username, password).

Specify paths for input and output CSV files.

Configure the Selenium WebDriver and login URL.

Ensure VPN Availability:

Install NordVPN CLI and ensure it is functional.

Add necessary VPN credentials.

Usage

Place the input CSV file in the specified path.

Run the main script:

python main.py

Follow prompts for Google Authenticator OTP if MFA is enabled.

The bot will:

Log into WordPress.

Process the CSV file.

Update links based on the CSV data.

Save results to the output CSV file.

Logging

Real-time logs are displayed in the console, providing:

Timestamps for actions.

Progress updates.

Error messages if any issues occur.

Security

Credentials are managed in config.py but should be stored securely using environment variables or secret management tools.

VPN integration ensures secure operations, especially for sensitive updates.

Contribution

Contributions are welcome! Please follow these steps:

Fork the repository.

Create a feature branch (feature/your-feature-name).

Commit your changes and submit a pull request.


