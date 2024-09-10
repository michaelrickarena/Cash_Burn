# Xero Data Extraction Script

## Overview

This script interacts with the Xero API to extract invoice and payment data, as well as bank transaction details. It retrieves data, processes it, and exports it to CSV files for further analysis.

## Features

- Authenticates with the Xero API using OAuth 2.0.
- Refreshes access tokens as needed.
- Retrieves invoice details, payment details, and bank transactions.
- Exports the data to CSV files:
  - `invoices.csv`: Contains details about invoices.
  - `payments.csv`: Contains details about payments.

## Files

- `refresh_token.txt`: Stores the refresh token for Xero API authentication.
- `results_new.csv`: Contains sensitive data extracted from Xero (ensure this file is handled securely).

## Setup

1. Create a `.env` file with the following variables:
   ```plaintext
   CLIENT_ID=your_client_id
   CLIENT_SECRET=your_client_secret
   ```
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the script to authenticate and retrieve data:
   ```bash
   python script_name.py
   ```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
