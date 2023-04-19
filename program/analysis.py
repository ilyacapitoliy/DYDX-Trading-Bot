import pandas as pd
from functools import reduce
from func_connections import connect_dydx
from func_messaging import send_message
from dateutil import parser
import uuid
import time 
from datetime import datetime, timedelta

from pprint import pprint

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

    try:
        # Get account balance
        account = client.private.get_account()
        free_collateral = float(account.data["account"]["freeCollateral"])

        time.sleep(0.5)

        date_now = datetime.now()
        date_yesterday = date_now - timedelta(days=1)
        yesterday = date_yesterday.isoformat()

        # Get all filled orders
        all_fills = client.private.get_fills(limit=100)
        all_exc_pos = all_fills.data["fills"]

        fills = []

        for p in all_exc_pos:
            fills.append({"now_timestamp":date_now.isoformat(),
                        "created_timestamp":p["createdAt"].replace("Z",""),
                        "order_id": p["orderId"],
                        "market": p["market"], 
                        "side":p["side"],
                        "price":float(p["price"]),
                        "size":float(p["size"]),              
                        "fee":round(float(p["fee"]), 3),
                        "type":p["type"], 
                        "balance":round(free_collateral, 2),   
                        "pair_status": "",
                        "pair_id":"",                   
                        })


        df_fills = pd.DataFrame(fills)

        # Change strings timestamps to pandas datetime object
        df_fills['now_timestamp'] =  pd.to_datetime(df_fills['now_timestamp']) #.dt.strftime('%d/%m/%Y %H:%M:%S')
        df_fills['created_timestamp'] =  pd.to_datetime(df_fills['created_timestamp'])

        # Make separate created date and time column 
        df_fills['created_date'] = pd.to_datetime(df_fills['created_timestamp']).dt.strftime('%d/%m/%Y')
        df_fills['created_time'] = pd.to_datetime(df_fills['created_timestamp']).dt.strftime('%H:%M:%S')


        grouped = df_fills.groupby('order_id', as_index=False) \
                            .aggregate({'size': 'sum','fee':'sum'})  
        cols_to_keep = ['now_timestamp','created_timestamp','balance','created_date','created_time', 'order_id','pair_id','pair_status','market', 'side', 'type','price']
        trade_list = pd.merge(df_fills[cols_to_keep],grouped, how="right", on='order_id') 
        trade_list = trade_list.drop_duplicates(subset=['order_id'])
        trade_list.sort_values(by='created_date', ascending=True, inplace=True)  # sort by date


        open_pairs = pd.read_csv('dydxtradebot/program/output/open_positions.csv') #'dydxtradebot/program/output/open_positions.csv'
        closed_pairs = pd.read_csv('dydxtradebot/program/output/closed_positions.csv') #'dydxtradebot/program/output/closed_positions.csv'

        # DEFINE POSITIONS ASIGNING OPEN/CLOSE PAIR STATUS
        # iterate over the trade list dataframe

        # OPEN
        for index, row in trade_list.iterrows():
            order_id = row['order_id']
            # find the corresponding row in the open positions dataframe
            base_row = open_pairs.loc[open_pairs['open_base_id'] == order_id]
            # if there is a match, update the trade_list dataframe
            if not base_row.empty:
                trade_list.at[index, 'pair_status'] = 'OPEN'

        for index, row in trade_list.iterrows():
            order_id = row['order_id']
            # find the corresponding row in the open positions dataframe
            quote_row = open_pairs.loc[open_pairs['open_quote_id'] == order_id]
            # if there is a match, update the trade_list dataframe
            if not quote_row.empty:
                trade_list.at[index, 'pair_status'] = 'OPEN'

        # CLOSE
        for index, row in trade_list.iterrows():
            order_id = row['order_id']
            # find the corresponding row in the open positions dataframe
            base_row = closed_pairs.loc[closed_pairs['closed_base_id'] == order_id]
            # if there is a match, update the trade_list dataframe
            if not base_row.empty:
                trade_list.at[index, 'pair_status'] = 'CLOSE'

        for index, row in trade_list.iterrows():
            order_id = row['order_id']
            # find the corresponding row in the open positions dataframe
            quote_row = closed_pairs.loc[closed_pairs['closed_quote_id'] == order_id]
            # if there is a match, update the trade_list dataframe
            if not quote_row.empty:
                trade_list.at[index, 'pair_status'] = 'CLOSE'


        

        # Loop through the rows of the trade_list dataframe
        for i, trade_row in trade_list.iterrows():
            order_id = trade_row['order_id']
            open_base_id = open_pairs.loc[open_pairs['open_base_id'] == order_id, 'pair_id']
            open_quote_id = open_pairs.loc[open_pairs['open_quote_id'] == order_id, 'pair_id']
            
            if len(open_base_id) > 0:
                trade_list.at[i, 'pair_id'] = open_base_id.iloc[0]
            elif len(open_quote_id) > 0:
                trade_list.at[i, 'pair_id'] = open_quote_id.iloc[0]

        #Initialize an empty dictionary to keep track of unique IDs

        # Make Amount column 

        for index, row in trade_list.iterrows():
            side = row['side']
            if side == 'BUY':
                trade_list.loc[index, 'amount'] = row['price']*row['size'] + row['fee']
            else:
                trade_list.loc[index, 'amount'] = -(row['price']*row['size'] + row['fee'])


        # Load the existing CSV file (if it exists)
        try:
            existing_data = pd.read_csv('dydxtradebot/program/output/trade_list.csv')
        except FileNotFoundError:
            existing_data = pd.DataFrame()

        merged_data = pd.concat([existing_data, trade_list])  # Combine the existing data with the new data
        latest_data = merged_data.drop_duplicates(subset=['order_id'])
        latest_data.to_csv('dydxtradebot/program/output/trade_list.csv', index=False)  # Save the new data to the CSV file

        send_message("trade_list data was loaded successfully!")


    except Exception as e:
        print("Error to create trade_list: ", e)
        send_message(f"Failed to create trade_list {e}")

    trade_list.tail(10)

    # try:
    #     # Concatanate two tables "open_positions.csv" & "closed_positions.csv"
    #     pair_trades = pd.concat([open_pairs,closed_pairs], axis=1)

    #     # Create empty column for Pair Id
    #     pair_trades['pair_id'] = pd.Series(dtype=object)

    #     # Asign Pair Id from Trade List to Pair Trades dataset
    #     for index, row in pair_trades.iterrows():
    #         open_base_id_row = row['open_base_id']
    #         matching_trade = trade_list.loc[trade_list['order_id'] == open_base_id_row]
    #         if not matching_trade.empty:
    #             pair_id = matching_trade.iloc[0]['pair_id']
    #             pair_trades.at[index, 'pair_id'] = pair_id

    #     # Convert date to datetime format
    #     pair_trades['open_date'] =  pd.to_datetime(pair_trades['open_date']) #.dt.strftime('%d/%m/%Y %H:%M:%S')
    #     pair_trades['closed_date'] =  pd.to_datetime(pair_trades['closed_date'])

    #     # Find pair's duration
    #     for i in range(0,len(pair_trades)):
    #         pair_trades.loc[i, 'duration'] = pair_trades.loc[i,'closed_date'] - pair_trades.loc[i,'open_date']

    #     pair_trades['duration_days'] = pair_trades['duration'].dt.round('D').dt.days.astype(str)

    #     # Iterate through Pair Trades dataset and extract data for MaxDrawdown data
    #     markets = []
    #     for i in range(len(pair_trades)):
    #         markets.append({
    #         "duration_days":pair_trades.loc[i,'duration_days'],
    #         "open_date":pair_trades.loc[i, 'open_date'].isoformat(),
    #         "closed_date":pair_trades.loc[i, 'closed_date'].isoformat(),
    #         "open_base_id":pair_trades.loc[i,'open_base_id'],
    #         "open_base_market":pair_trades.loc[i, 'open_base_market'],
    #         "open_base_side":pair_trades.loc[i, 'open_base_side'],
    #         "open_base_price":pair_trades.loc[i, 'open_base_price'],
    #         "open_base_size":pair_trades.loc[i, 'open_base_size'],
    #         "open_base_amount":pair_trades.loc[i,'open_base_amount'],
    #         "open_quote_id":pair_trades.loc[i,'open_quote_id'],
    #         "open_quote_market":pair_trades.loc[i, 'open_quote_market'],
    #         "open_quote_side":pair_trades.loc[i, 'open_quote_side'],
    #         "open_quote_price":pair_trades.loc[i, 'open_quote_price'],
    #         "open_quote_size":pair_trades.loc[i, 'open_quote_size'],
    #         "open_quote_amount":pair_trades.loc[i,'open_quote_amount'],
    #         })    

    #     markets
            
    #     # MAX DRAWDOWN FOR BASE MARKET
    #     close_prices_base = []

    #     for m in markets:
    #         # Get candles for period when position was open
    #         candles = client.public.get_candles(
    #                 market=m['open_base_market'],
    #                 resolution="1HOUR",
    #                 from_iso=m['open_date'],
    #                 to_iso=m['closed_date'],
    #             )

    #     # Structure data
    #     for candle in candles.data["candles"]:
    #         close_prices_base.append({"market":m['open_base_market'], 
    #                             "datetime": candle["startedAt"], 
    #                             "base_price": float(candle["close"]),
    #                             "base_side": m['open_base_side'],
    #                             })

    #     candles_for_dd = pd.DataFrame(close_prices_base)

    #     if candles_for_dd.loc[candles_for_dd['base_side'] == 'BUY'].empty:
    #         maxdrawdown_base = (m['open_base_price'] - candles_for_dd['base_price'].max())*m['open_base_size']
    #     elif candles_for_dd.loc[candles_for_dd['base_side'] == 'SELL'].empty:
    #         maxdrawdown_base = (candles_for_dd['base_price'].min() - m['open_base_price'])*m['open_base_size']

    #     for index, row in pair_trades.iterrows():
    #         if row['open_base_id'] == m['open_base_id']:
    #             pair_trades.loc[index, 'maxdrawdown_base'] = maxdrawdown_base
    #             pair_trades.loc[index, 'maxdrawdown_base_percent'] = maxdrawdown_base/abs(m['open_base_amount']) * 100
                

    #     # MAX DRAWDOWN FOR QUOTE MARKET
    #     close_prices_quote = []

    #     for m in markets:

    #         # Get candles for period when position was open
    #         candles = client.public.get_candles(
    #                 market=m['open_quote_market'],
    #                 resolution="1HOUR",
    #                 from_iso=m['open_date'],
    #                 to_iso=m['closed_date'],
    #             )

    #         # Structure data
    #         for candle in candles.data["candles"]:
    #             close_prices_quote.append({"market":m['open_quote_market'], 
    #                                 "datetime": candle["startedAt"], 
    #                                 "quote_price": float(candle["close"]),
    #                                 "quote_side": m['open_quote_side'],
    #                                 })

    #         candles_for_dd_quote = pd.DataFrame(close_prices_quote)
    #         pprint(candles_for_dd_quote['quote_price'].max())

    #         if candles_for_dd_quote.loc[candles_for_dd_quote['quote_side'] == 'BUY'].empty:
    #             maxdrawdown_quote = (m['open_quote_price'] -  candles_for_dd_quote['quote_price'].max())*m['open_quote_size']
    #         elif candles_for_dd_quote.loc[candles_for_dd_quote['quote_side'] == 'SELL'].empty:
    #             maxdrawdown_quote = (candles_for_dd_quote['quote_price'].min()  - m['open_quote_price'])*m['open_quote_size']

    #         for index, row in pair_trades.iterrows():
    #             if row['open_quote_id'] == m['open_quote_id']:
    #                 pair_trades.loc[index, 'maxdrawdown_quote'] = maxdrawdown_quote 
    #                 pair_trades.loc[index, 'maxdrawdown_quote_percent'] = maxdrawdown_quote/abs(m['open_quote_amount']) * 100
    #                 pair_trades.loc[index, 'pair_maxdrawdown'] = maxdrawdown_quote + maxdrawdown_base
    #                 pair_trades.loc[index, 'pair_maxdrawdown_percent'] = maxdrawdown_base/abs(m['open_base_amount']) * 100 + maxdrawdown_quote/abs(m['open_quote_amount']) * 100

    #     # Load the existing CSV file (if it exists)
    #     try:
    #         existing_data = pd.read_csv('dydxtradebot/program/output/pair_trades.csv')
    #     except FileNotFoundError:
    #         existing_data = pd.DataFrame()

    #     merged_data = pd.concat([existing_data, pair_trades])  # Combine the existing data with the new data
    #     latest_data = merged_data.drop_duplicates(subset=['open_base_id'])
    #     latest_data.to_csv('dydxtradebot/program/output/pair_trades.csv', index=False)  # Save the new data to the CSV file

    #     send_message("pair_trades data was loaded successfully!")


    # except Exception as e:
    #     print("Error to create pair_trades: ", e)
    #     send_message(f"Failed to create pair_trades {e}")

    
    try:

        # Let's get all  CLOSED positions
        all_positions = client.private.get_positions(status="CLOSED")
        all_positions = all_positions.data['positions']
        all_closed_positions = []

        for x in all_positions:
            all_closed_positions.append({
                "market": x['market'],
                "side":x['side'],
                "size":x['size'],
                "maxSize":round(float(x['maxSize']), 3),
                "entryPrice":float(x['entryPrice']),
                "exitPrice":float(x['exitPrice']),
                "realizedPnl":round(float(x['realizedPnl']),2),
                "createdAt":x['createdAt'],
                "closedAt":x['closedAt'],
                "sumOpen":x['sumOpen'],
                "sumClose":x['sumClose'],
                "realizedPnl percent":  round((round(float(x['realizedPnl']), 2) / round(round(float(x['sumOpen']), 3)*float(x['entryPrice']), 2)) *100 , 4),
                "start amount":round(round(float(x['sumOpen']), 3)*float(x['entryPrice']), 2),
                "close amount":round(round(float(x['sumClose']), 3)*float(x['exitPrice']), 2),
            })

        get_closed_df = pd.DataFrame(all_closed_positions)
        get_closed_df

        #get_closed_df['current timestamp'] = pd.to_datetime(get_closed_df['createdAt']) #.dt.strftime('%d/%m/%Y %H:%M:%S')
        #get_closed_df['created timestamp'] = pd.to_datetime(get_closed_df['closedAt'])

        # Make separate created date and time column 
        get_closed_df['created_date'] = pd.to_datetime(get_closed_df['createdAt']).dt.strftime('%d/%m/%Y')
        get_closed_df['closed_date'] = pd.to_datetime(get_closed_df['closedAt']).dt.strftime('%d/%m/%Y')

        get_closed_df.sort_values(by=['closedAt']).head()

        
        # OPEN POSITIONS PER DAY
        open_positions = get_closed_df.groupby('created_date')['entryPrice'].count().reset_index(name='num_open_positions')

        # CLOSED POSITIONS PER DAY
        closed_positions = get_closed_df.groupby('closed_date')['realizedPnl'].count().reset_index(name='num_closed_positions')

        # PNL PER DAY & PNL % PER DAY
        df_for_pnl = get_closed_df.groupby('closed_date')['realizedPnl'].sum().reset_index(name='pnl_daily')

        df_for_std_return = get_closed_df.groupby('closed_date')['realizedPnl percent'].std().round(2).reset_index(name='std_return')

        # MEAN & MEDIAN PNL PER DAY
        df_for_mean_pnl = get_closed_df.groupby('closed_date')['realizedPnl'].mean().round(2).reset_index(name='pnl_mean_daily')
        df_for_median_pnl = get_closed_df.groupby('closed_date')['realizedPnl'].median().round(2).reset_index(name='pnl_median_daily')

        # NUMBER OF ORDERS PER DAY
        trades_per_day = trade_list.groupby('created_date')['order_id'].count().reset_index(name='num_orders')
        trades_per_day

        # VOLUME ALL (BUY & SELL) ORDERS
        volume_per_day = trade_list.groupby('created_date')['amount'].sum().reset_index(name='volume_orders')

        # BUY & SELL VOLUME
        buy_volume_per_day = trade_list[trade_list['side'] == 'BUY'].groupby('created_date')['amount'].sum().reset_index(name='volume_BUY_orders')
        sell_volume_per_day = trade_list[trade_list['side'] == 'SELL'].groupby('created_date')['amount'].sum().reset_index(name='volume_SELL_orders')

        # VOLUME OPEN POSITIONS PER DAY
        volume_open_positions_per_day = get_closed_df.groupby('created_date')['start amount'].sum().reset_index(name='volume_open_positions')

        # VOLUME CLOSED POSITIONS PER DAY
        volume_closed_positions_per_day = get_closed_df.groupby('closed_date')['close amount'].sum().reset_index(name='volume_closed_positions')


        # TOTAL PER DAY

        data_frames_created_date = [trades_per_day, volume_per_day, buy_volume_per_day, sell_volume_per_day, open_positions, volume_open_positions_per_day]
        df_merged = reduce(lambda  left,right: pd.merge(left,right,on=['created_date'],how='outer'), data_frames_created_date)

        data_frames_closed_date = [df_for_pnl, df_for_mean_pnl, df_for_median_pnl, closed_positions, volume_closed_positions_per_day, df_for_std_return]
        df_merged_2 = reduce(lambda  left,right: pd.merge(left,right,on=['closed_date'],how='outer'), data_frames_closed_date)


        merged_total = pd.merge(df_merged, df_merged_2, left_on=['created_date'], right_on=['closed_date'], how="left")

        merged_total['BUY_SELL_ratio'] = round(merged_total['volume_BUY_orders'] / abs(merged_total['volume_SELL_orders']), 2)

        #merged_total['num_live_positions'] = pd.Series(dtype=int)
        #merged_total['volume_live_positions'] = pd.Series(dtype=float)
        #merged_total['return_daily'] = pd.Series(dtype=float)
        merged_total['avg_trade_net_profit'] = pd.Series(dtype=float)

        total_per_day = merged_total[['created_date',
                                    'num_orders',
                                    'volume_BUY_orders',
                                    'volume_SELL_orders',
                                    'BUY_SELL_ratio',
                                    'volume_open_positions',
                                    'volume_closed_positions',
                                    'num_open_positions',
                                    'num_closed_positions',
                                    'pnl_daily',
                                    'pnl_mean_daily',
                                    'pnl_median_daily',
                                    'std_return',
                                    'avg_trade_net_profit']].fillna(0).sort_values(by=['created_date']).astype({'num_open_positions':'int','num_orders':'int' })

        # NUMBER OF LIVE POSITIONS
        #for i in range(1, len(total_per_day)):
        #   total_per_day.loc[i, 'num_live_positions'] = get_open_df['unrealizedPnl'].count()
        #for i in range(1, len(total_per_day)):
        #    total_per_day.loc[i, 'num_live_positions'] = total_per_day.loc[i-1, 'num_live_positions'] + (total_per_day.loc[i, 'num_open_positions'] - total_per_day.loc[i, 'num_closed_positions'])

        # VOLUME OF LIVE POSITIONS
        #for i in range(1, len(total_per_day)):
        #    total_per_day.loc[i, 'volume_live_positions'] = get_open_df['amount'].abs().round().sum()
        #for i in range(1, len(total_per_day)):
        #    total_per_day.loc[i, 'volume_live_positions'] = total_per_day.loc[i-1, 'volume_live_positions'] + (total_per_day.loc[i, 'volume_open_positions'] - total_per_day.loc[i, 'volume_closed_positions'])

        # DAILY RETURN
        #for i in range(1, len(total_per_day)):
        #    total_per_day.loc[i, 'return_daily'] = round((total_per_day.loc[i, 'pnl_daily'] / total_per_day.loc[i, 'volume_open_positions'])*100, 4) 

        # Average Trade Net Profit
        for i in range(1, len(total_per_day)):
            total_per_day.loc[i, 'avg_trade_net_profit'] = round((total_per_day.loc[i, 'pnl_daily'] / total_per_day.loc[i, 'num_open_positions']),2)

        # Load the existing CSV file (if it exists)
        try:
            existing_data = pd.read_csv('dydxtradebot/program/output/total_per_day.csv')
        except FileNotFoundError:
            existing_data = pd.DataFrame()

        merged_data = pd.concat([existing_data, total_per_day])  # Combine the existing data with the new data
        latest_data = merged_data.drop_duplicates(subset=['created_date'])
        latest_data.to_csv('dydxtradebot/program/output/total_per_day.csv', index=False)  # Save the new data to the CSV file

        send_message("total_per_day data was loaded successfully!")


    except Exception as e:
        print("Error to create total_per_day: ", e)
        send_message(f"Failed to create total_per_day {e}")


    try:
        # Lets get balance of account
        account = client.private.get_account()
        free_collateral = float(account.data["account"]["freeCollateral"])
        equity = float(account.data["account"]["equity"])
        time.sleep(0.5)

        balance_list = []

        balance_list.append({
            "created_date":date_now.isoformat(),
            "initial_deposit":5700,
            "withdrawable_balance":round(free_collateral, 2),
            "equity":round(equity, 2),
            "margin":round(equity, 2)-round(free_collateral, 2),
            "margin_percent":(round(equity, 2)-round(free_collateral, 2))*100 / round(equity, 2),
        })

        balance = pd.DataFrame(balance_list)

        balance['created_date'] = pd.to_datetime(balance['created_date']).dt.strftime('%d/%m/%Y')

        # Load the existing CSV file (if it exists)
        try:
            existing_data = pd.read_csv('dydxtradebot/program/output/balance.csv')
        except FileNotFoundError:
            existing_data = pd.DataFrame()

        merged_data = pd.concat([existing_data, balance])  # Combine the existing data with the new data
        latest_data = merged_data.drop_duplicates(subset=['created_date'])
        latest_data.to_csv('dydxtradebot/program/output/balance.csv', index=False)  # Save the new data to the CSV file

        send_message("balance data was loaded successfully!")

    except Exception as e:
        print("Error to create balance: ", e)
        send_message(f"Failed to create balance {e}")





    
    
    
    











