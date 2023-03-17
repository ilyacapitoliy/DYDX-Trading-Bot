from func_connections import connect_dydx
from func_messaging import send_message
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime, timedelta

if __name__ == "__main__":


    # Connect to client
    try:
        print("Connecting to client...")
        client = connect_dydx()
    except Exception as e:
        print("Error connecting to client: ", e)
        send_message(f"Failed to connect to client {e}")
        exit(1)
    
    # Protect API
    time.sleep(0.5)

    # Store Balance
    try:
        account = client.private.get_account()
        free_collateral = float(account.data["account"]["freeCollateral"])
        #account_number = account.data["account"]["accountNumber"]

        # Protect API
        time.sleep(0.5)

        date = datetime.now()
        yesterday = date + timedelta(days=-1)
        
        #historical_pnl = client.private.get_historical_pnl(created_on_or_after=yesterday.isoformat())        
        #HistoricalAggregatedPnl = historical_pnl.data['historicalPnl'][0]


        balance = []

        balance.append({
            "date":date.isoformat(),
            "balance": free_collateral,
            #"daily pnl": daily_pnl,
            #"createdAt": when_tick,
        })

        # Create and save DataFrame
        df_1 = pd.DataFrame(balance)
        df_1.to_csv("balance.csv",mode='a', index= False, header= False)
        send_message(f"Balance: {round(free_collateral, 2)} $ \n\nSaved to storage. ")
    except Exception as e:
        print("Error connecting to client: ", e)
        send_message(f"Failed to connect to client {e}")
        exit(1)


