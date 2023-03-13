from func_connections import connect_dydx
import datetime
from func_messaging import send_message
from func_utils import format_number
from func_public import get_candles_recent
import pandas as pd
import numpy as np
import json
import time

if __name__ == "__main__":


    # Connect to client
    try:
        print("Connecting to client...")
        client = connect_dydx()
        send_message("Start analyzing tool")
    except Exception as e:
        print("Error connecting to client: ", e)
        send_message(f"Failed to connect to client {e}")
        exit(1)

    # Store Balance
    try:
        account = client.private.get_account()
        free_collateral = float(account.data["account"]["freeCollateral"])
        account_number = account.data["account"]["accountNumber"]

        date = datetime.datetime.now()

        balance = []

        balance.append({
            "date":date.isoformat(),
            "balance": free_collateral,
            "pnl":daily_pnl,
        })

        # Create and save DataFrame
        df_1 = pd.DataFrame(balance)
        df_1.to_csv("balance.csv",mode='a', index= False, header= False)
    except Exception as e:
        print("Error connecting to client: ", e)
        send_message(f"Failed to connect to client {e}")
        exit(1)

