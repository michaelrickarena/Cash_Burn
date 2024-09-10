from xero import get_spend_money, xero_request, get_payments
import pandas as pd

df_payments = get_payments()
df_spend_money = get_spend_money()

res = pd.concat([df_payments, df_spend_money])

res.to_csv("results_new.csv", index = False)