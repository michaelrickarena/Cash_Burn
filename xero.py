import json
import requests
import webbrowser
import base64
import datetime
import pandas as pd
import time
import re
from dotenv import load_dotenv
import os


load_dotenv(".env")
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
redirect_url = 'https://www.xero.com/'
scope = 'openid profile email accounting.transactions.read accounting.reports.read offline_access'
b64_id_secret = base64.b64encode(bytes(client_id + ':' + client_secret, 'utf-8')).decode('utf-8')

def XeroFirstAuth():
    # 1. Send a user to authorize your app
    auth_url = ('''https://login.xero.com/identity/connect/authorize?''' +
                '''response_type=code''' +
                '''&client_id=''' + client_id +
                '''&redirect_uri=''' + redirect_url +
                '''&scope=''' + scope +
                '''&state=123''')

    # 2. Users are redirected back to you with a code
    auth_res_url = "https://www.xero.com/ca/?code=fR-VS5Zp1tSqcNQbq86AIHCqr2b9AE_i4Pb1IZ884-Q&scope=openid%20profile%20email%20accounting.transactions.read%20accounting.reports.read%20offline_access&state=123&session_state=Kzb6Uwl7w7wGVk7rA6TEz6Fh_1fdiGSbUujNr0CCwes.4Ve1F-0E0M4PZGS4TRhgew"
    start_number = auth_res_url.find('code=') + len('code=')
    end_number = auth_res_url.find('&scope')
    auth_code = auth_res_url[start_number:end_number]

    # 3. Exchange the code
    exchange_code_url = 'https://identity.xero.com/connect/token'
    response = requests.post(exchange_code_url, 
                            headers = {
                                'Authorization': 'Basic ' + b64_id_secret
                            },
                            data = {
                                'grant_type': 'authorization_code',
                                'code': auth_code,
                                'redirect_uri': redirect_url
                            })
    json_response = response.json()

    # 4. Receive your tokens
    return [json_response['access_token'], json_response['refresh_token']]

# 5. Check the full set of tenants you've been authorized to access
def XeroTenants(access_token):
    connections_url = 'https://api.xero.com/connections'
    response = requests.get(connections_url,
                           headers = {
                               'Authorization': 'Bearer ' + access_token,
                               'Content-Type': 'application/json'
                           })
    json_response = response.json()
    
    for tenants in json_response:
        json_dict = tenants
    return json_dict['tenantId']


# XeroTenants(tokens['access_token'])

# 6.1 Refreshing access tokens
def XeroRefreshToken(refresh_token):
    token_refresh_url = 'https://identity.xero.com/connect/token'
    response = requests.post(token_refresh_url,
                            headers = {
                                'Authorization' : 'Basic ' + b64_id_secret,
                                'Content-Type': 'application/x-www-form-urlencoded'
                            },
                            data = {
                                'grant_type' : 'refresh_token',
                                'refresh_token' : refresh_token
                            })
    json_response = response.json()
    
    new_refresh_token = json_response['refresh_token']
    rt_file = open('refresh_token.txt', 'w')
    rt_file.write(new_refresh_token)
    rt_file.close()
    
    return [json_response['access_token'], json_response['refresh_token']]

old_refresh_token = open('refresh_token.txt', 'r').read()
XeroRefreshToken(old_refresh_token)

#refresh token data before each API call
def RefreshTokenData():
    global old_refresh_token, new_tokens, xero_tenant_id
    old_refresh_token = open('refresh_token.txt', 'r').read()
    new_tokens = XeroRefreshToken(old_refresh_token)
    xero_tenant_id = XeroTenants(new_tokens[0])

# 6.2 Call the API, Invoices
def XeroInvoicesRequest():
    RefreshTokenData()
    
    get_url = 'https://api.xero.com/api.xro/2.0/Invoices'
    response = requests.get(get_url,
                           headers = {
                               'Authorization': 'Bearer ' + new_tokens[0],
                               'Xero-tenant-id': xero_tenant_id,
                               'Accept': 'application/json'
                           })
    json_response = response.json()
    
    xero_output = open('xero_output_invoices.txt', 'w')
    xero_output.write(response.text)
    xero_output.close()


def XeroPaymentRequest():
    RefreshTokenData()
    
    get_url = 'https://api.xero.com/api.xro/2.0/Payments/75781bab-5b45-4763-b2e4-741c0b4e78fd'
    response = requests.get(get_url,
                           headers = {
                               'Authorization': 'Bearer ' + new_tokens[0],
                               'Xero-tenant-id': xero_tenant_id,
                               'Accept': 'application/json'
                           })
    json_response = response.json()    
    xero_output = open('xero_output_payment.txt', 'w')
    xero_output.write(response.text)
    xero_output.close()

def export_csv_invoices():
    invoices = open(r'xero_output_invoices.txt', 'r').read()
    json_invoice = json.loads(invoices)
    analysis = open(r'invoices.csv', 'w')
    analysis.write('Contact Name' + ',' + 'Contact ID' + ',' + 'Invoice ID' + ',' + 'Invoice Number' + ',' + 'Invoice Date' + ',' + 'Sub Total' + ',' + 'Total Tax' + ',' + 'Total' + ',' + 'Type' + ',' + 'Currency' + ',' + 'Amount Due' + ',' + 'Amount Paid' + ',' + 'Amount Credited')
    analysis.write('\n')
    #Loop through invoices in JSON
    for invoices in json_invoice['Invoices']:                        

        contact_name = invoices['Contact']['Name']
        contact_name = contact_name.replace(',', '')
        contactID = invoices['Contact']['ContactID']
        InvoiceID = invoices['InvoiceID']
        Invoice_Number = invoices['InvoiceNumber']
        invoice_date = invoices['DateString'].split("T",1)[0]
        # invoice_due_date = invoices['DueDateString'].split("T",1)[0]
        sub_total = str(invoices['SubTotal'])
        TotalTax = str(invoices['TotalTax'])
        total = str(invoices['Total'])
        payment_type = invoices['Type']
        currency_code = invoices['CurrencyCode']
        # payments_date = invoices['Payments']['Date']
        # payments_amount = invoices['Payments']['Amount']
        amount_due = str(invoices['AmountDue'])
        amount_paid = str(invoices['AmountPaid'])
        amount_credited = str(invoices['AmountCredited'])

        analysis.write(contact_name + ',' + contactID + ',' + InvoiceID + ',' + Invoice_Number + ',' + invoice_date + ',' + sub_total + ',' + TotalTax + ',' + total + ',' + payment_type + ',' + currency_code + ',' + amount_due + ',' + amount_paid + ',' + amount_credited)
        analysis.write('\n')
    analysis.close()


def export_csv_payments():
    payments = open(r'xero_output_payment.txt', 'r').read()
    json_payment = json.loads(payments)
    payment_analysis = open(r'payments.csv', 'w')
    payment_analysis.write('Contact Name' + ',' + 'Date' + ',' +'Payment Type' + ',' + 'Invoice Link' + ',' + 'Status' + ',' + 'Reconciled' + ',' + 'Total' + ',' + 'Currency')
    payment_analysis.write('\n')
    #Loop through invoices in JSON
    for payments in json_payment['Payments']:
        if payments['IsReconciled'] == True and payments['Status'] == 'AUTHORISED':
            invoice = payments['Invoice']
            name = invoice['Contact']['Name']
            name = name.replace(',', '')

            payment_type = invoice['Type']
            invoiceID = invoice['InvoiceID']
            invoiceLink = f'https://go.xero.com/AccountsPayable/View.aspx?InvoiceID={invoiceID}'

            #Below is to convert Xero date to an actual datetime. "actual_date" Is the cleaned variable
            date = str(payments['Date'])
            date = date.removeprefix('/Date(')
            date = int(date.removesuffix('+0000)/'))
            date = str(datetime.timedelta(days=date / 86400000) + datetime.datetime(1970,1,1))
            actual_date = datetime.datetime.strptime(date,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')


            status = payments['Status']
            reconciled = str(payments['IsReconciled'])
            amount = str(payments['Amount'])
            currency = str(payments['CurrencyRate'])

            payment_analysis.write(name + ',' + actual_date + ',' + payment_type + ',' + invoiceLink + ',' + status + ',' + reconciled + ',' + amount + ',' + currency)

            payment_analysis.write('\n')
    payment_analysis.close()


def xero_request(url, headers):
    status_code = 0
    while status_code != 200:
        response = requests.get(url, headers=headers)

        status_code = response.status_code
        if status_code == 429:
            wait_time = int(response.headers["Retry-After"])
            print(f"Waiting {wait_time} seconds due to rate limiting...")
            time.sleep(wait_time)

    return response.json()


def get_spend_money_details(txn):
    txn_id = txn["BankTransactionID"]

    txn_type = txn["Type"]
    if txn_type not in ["SPEND", "RECEIVE"]:
        return []

    txn_contact = txn["Contact"]["Name"]
    txn_date = txn["DateString"][:10]

    txn_curr = txn["CurrencyCode"]
    txn_curr_rate = txn["CurrencyRate"] if "CurrencyRate" in txn else 1

    txn_line_items = txn["LineItems"]

    results = []
    for line in txn_line_items:
        if "LineAmount" in line and line["LineAmount"] != 0:
            txn_tax_type = txn["LineAmountTypes"]
            txn_tax = (
                float(line["TaxAmount"])
                if (txn_tax_type == "Exclusive") and ("TaxAmount" in line)
                else 0
            )
            txn_amount_source = round(float(line["LineAmount"]) + txn_tax, 2)
            txn_desc = line["Description"] if "Description" in line else 1
            txn_acct_code = line["AccountCode"]

            trackers = line["Tracking"] if "Tracking" in line else ""
            txn_tracking = trackers[0]["Option"] if len(trackers) > 0 else ""

            if txn_acct_code not in [
                "10110",  # Short-term Investments
                "70510", # Bank Charges
                "23000", # fx Clearing
                "21015", # Suspense
            ]:
                results.append(
                    {
                        "Contact Name": txn_contact,
                        "Date": txn_date,
                        "Link": f"https://go.xero.com/Bank/ViewTransaction.aspx?bankTransactionID={txn_id}",
                        "Currency": txn_curr,
                        "Rate": txn_curr_rate,
                        "Description": txn_desc,
                        "Amount (Source)": txn_amount_source,
                        "Account Code": txn_acct_code,
                        "Amount (Base)": round(float(txn_amount_source / txn_curr_rate), 2),
                        "Department": txn_tracking,
                        "Type": txn_type,
                    }
                )

    return results


def get_spend_money():
    RefreshTokenData()
    headers = {
        "Authorization": "Bearer " + new_tokens[0],
        "Xero-tenant-id": xero_tenant_id,
        "Accept": "application/json",
    }
    page_no, pages_available, results = 1, True, []

    while pages_available:
        res = xero_request(
            f"https://api.xero.com/api.xro/2.0/banktransactions?page={page_no}&where=Status%3D%3D%22AUTHORISED%22",
            headers,
        )

        txns = res["BankTransactions"]

        for idx, txn in enumerate(txns):
            is_rec, status = (
                txn["IsReconciled"],
                txn["Status"],
            )
            if is_rec and status == "AUTHORISED":
                results.extend(get_spend_money_details(txn))
                print(f"Processed {100 * (page_no - 1) + idx + 1} transaction(s)")

        pages_available = len(txns) > 0
        page_no += 1

    df = pd.DataFrame(results)
    return df


def get_payment_details(txn):
    txn_id = txn["InvoiceID"]

    txn_contact = txn["Contact"]["Name"]

    txn_curr_rate = txn["CurrencyRate"] if "CurrencyRate" in txn else 1
    txn_curr = txn["CurrencyCode"]

    txn_line_items = txn["LineItems"]

    txn_total = float(txn["Total"])

    txn_pmts = txn["Payments"]

    results = []
    if txn_total > 0:
        for pmt in txn_pmts:
            for line in txn_line_items:
                if "LineAmount" in line and line["LineAmount"] != 0:
                    txn_tax_type = txn["LineAmountTypes"]
                    txn_tax = (
                        float(line["TaxAmount"])
                        if (txn_tax_type == "Exclusive") and ("TaxAmount" in line)
                        else 0
                    )
                    txn_amount_source = round(
                        (float(line["LineAmount"]) + txn_tax)
                        * float(pmt["Amount"])
                        / txn_total,
                        2,
                    )
                    txn_desc = line["Description"] if "Description" in line else 1
                    txn_acct_code = line["AccountCode"]

                    trackers = line["Tracking"] if "Tracking" in line else ""
                    txn_tracking = trackers[0]["Option"] if len(trackers) > 0 else ""

                    if txn_acct_code not in [
                        "10110",
                        "70510",
                        "23000",
                        "21015",
                    ]:
                        pmt_date = re.search(r"\d+", pmt["Date"])[0]
                        results.append(
                            {
                                "Contact Name": txn_contact,
                                "Date": (
                                    datetime.timedelta(days=float(pmt_date) / 86400000)
                                    + datetime.datetime(1970, 1, 1)
                                ).strftime("%Y-%m-%d"),
                                "Link": f"https://go.xero.com/AccountsReceivable/View.aspx?InvoiceID={txn_id}" if txn["Type"] == "ACCREC" else f"https://go.xero.com/AccountsPayable/View.aspx?InvoiceID={txn_id}",
                                "Currency": txn_curr,
                                "Rate": txn_curr_rate,
                                "Description": txn_desc,
                                "Amount (Source)": txn_amount_source,
                                "Account Code": txn_acct_code,
                                "Amount (Base)": round(
                                    float(txn_amount_source / txn_curr_rate), 2
                                ),
                                "Department": txn_tracking,
                                "Type": txn["Type"],
                            }
                        )

    return results


def get_payments():
    RefreshTokenData()
    headers = {
        "Authorization": "Bearer " + new_tokens[0],
        "Xero-tenant-id": xero_tenant_id,
        "Accept": "application/json",
    }
    page_no, pages_available, results = 1, True, []

    while pages_available:
        res = xero_request(
            f"https://api.xero.com/api.xro/2.0/Invoices?page={page_no}&Statuses=AUTHORISED,PAID",
            headers,
        )

        txns = res["Invoices"]

        for idx, txn in enumerate(txns):
            results.extend(get_payment_details(txn))
            print(f"Processed {100 * (page_no - 1) + idx + 1} transaction(s)")

        pages_available = len(txns) > 0
        page_no += 1

    df = pd.DataFrame(results)
    return df