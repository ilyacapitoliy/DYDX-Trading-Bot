from constants import CLOSE_AT_ZSCORE_CROSS, UNREALIZED_PNL_LEVEL
from func_utils import format_number
from func_public import get_candles_recent
from func_cointegration import calculate_zscore
from func_private import place_market_order
from func_messaging import send_message
import json
import time
import pandas as pd
import datetime
from pprint import pprint
date_now = datetime.datetime.now()


# Manage trade exits
def manage_trade_exits(client):

  """
    Manage exiting open positions
    Based upon criteria set in constants
  """

  # Initialize saving output
  save_output = []

  # Opening JSON file
  try:
    open_positions_file = open("dydxtradebot/program/bot_agents.json")
    open_positions_dict = json.load(open_positions_file)
    #pprint(open_positions_dict)
  except:
    return "complete"

  # Guard: Exit if no open positions in file
  if len(open_positions_dict) < 1:
    return "complete"

  # Get all open positions per trading platform
  exchange_pos = client.private.get_positions(status="OPEN")
  all_exc_pos = exchange_pos.data["positions"]

  markets_names_live = []
  for j in all_exc_pos:
    markets_names_live.append(j["market"])
  
  date_now = datetime.datetime.now().isoformat()
  markets_live_full = []
  for p in all_exc_pos:
    markets_live_full.append({"date now":date_now,
                              "date created":p["createdAt"],
                              "market": p["market"], 
                              "side":p["side"],
                              "size":p["size"],
                              "maxSize":p["maxSize"],
                              "entryPrice":p["entryPrice"],
                              "unrealizedPnl": float(p["unrealizedPnl"]),
                              "sumOpen":p["sumOpen"],                              
                              })

  # Protect API
  time.sleep(0.5)

  # Check all saved positions match order record
  # Exit trade according to any exit trade rules
  for position in open_positions_dict:

    # Initialize is_close trigger
    is_close = False

    # Extract position matching information from file - market 1
    position_market_m1 = position["market_1"]
    position_size_m1 = position["order_m1_size"]
    position_side_m1 = position["order_m1_side"]
    position_start_price_m1 = position["order_m1_price"]
    #position_createdAt_m1 = position["order_time_m1"]

    # Extract position matching information from file - market 2
    position_market_m2 = position["market_2"]
    position_size_m2 = position["order_m2_size"]
    position_side_m2 = position["order_m2_side"]
    position_start_price_m2 = position["order_m2_price"]
    #position_createdAt_m2 = position["order_time_m2"]

    # Protect API
    time.sleep(0.5)

    # Get order info m1 per exchange
    order_m1 = client.private.get_order_by_id(position["order_id_m1"])
    order_market_m1 = order_m1.data["order"]["market"]
    order_size_m1 = order_m1.data["order"]["size"]
    order_side_m1 = order_m1.data["order"]["side"]
    order_price_m1 = order_m1.data["order"]["price"]
    
    pprint(order_market_m1)
    

    # Protect API
    time.sleep(0.5)

    # Get order info m2 per exchange
    order_m2 = client.private.get_order_by_id(position["order_id_m2"])
    order_market_m2 = order_m2.data["order"]["market"]
    order_size_m2 = order_m2.data["order"]["size"]
    order_side_m2 = order_m2.data["order"]["side"]
    order_price_m2 = order_m2.data["order"]["price"]

    # Perform matching checks
    check_m1 = position_market_m1 == order_market_m1 and position_size_m1 == order_size_m1 and position_side_m1 == order_side_m1
    check_m2 = position_market_m2 == order_market_m2 and position_size_m2 == order_size_m2 and position_side_m2 == order_side_m2
    check_live = position_market_m1 in markets_names_live and position_market_m2 in markets_names_live
       
      
    # Guard: If not all match exit with error
    if not check_m1 or not check_m2 or not check_live:
    #  print(f"Warning: Not all open positions match exchange records for {position_market_m1} and {position_market_m2}")
      continue

    # Get prices
    series_1 = get_candles_recent(client, position_market_m1)
    time.sleep(0.2)
    series_2 = get_candles_recent(client, position_market_m2)
    time.sleep(0.2)

    # Get markets for reference of tick size
    markets = client.public.get_markets().data

    # Protect API
    time.sleep(0.2)

    # Detrmine PNL
    for m in markets_live_full:
      if m["market"] == position_market_m1:
        pnl_1 = m["unrealizedPnl"]
      if m["market"] == position_market_m2:
        pnl_2 = m["unrealizedPnl"]
      
    pprint(f"market_1: {position_market_m1} pnl_1: {pnl_1}")
    pprint(f"market_2: {position_market_m2} pnl_2: {pnl_2}")
    
    pnl = pnl_1 + pnl_2
    pnl_percent = pnl / (float(position_size_m1)*float(position_start_price_m1) + float(position_size_m2)*float(position_start_price_m2))*100
    
    pprint(f"pnl: {pnl}")
    pprint(f"pnl %: {round(pnl_percent,2)}")
    

    # Trigger close based on Z-score
    if CLOSE_AT_ZSCORE_CROSS:

      # Initialize z_scores
      hedge_ratio = position["hedge_ratio"]
      z_score_traded = position["z_score"]
      if len(series_1) > 0 and len(series_1) == len(series_2):
        spread = series_1 - (hedge_ratio * series_2)
        z_score_current = calculate_zscore(spread).values.tolist()[-1]
      
      # Determine trigger
      z_score_level_check = abs(z_score_current) >= abs(z_score_traded/7)
      z_score_cross_check = (z_score_current < 0 and z_score_traded > 0) or (z_score_current > 0 and z_score_traded < 0)
      pnl_check = pnl_percent > 3.33

      # Close trade
      if z_score_level_check and z_score_cross_check and pnl_check:
          
          # Initiate close trigger
          is_close = True
    ###
    # Add any other close logic you want here
    # Trigger is_close
    
    ###

    # Close positions if triggered
    if is_close:
      
        # Determine side - m1
        side_m1 = "SELL"
        if position_side_m1 == "SELL":
            side_m1 = "BUY"

        # Determine side - m2
        side_m2 = "SELL"
        if position_side_m2 == "SELL":
            side_m2 = "BUY"

        # Get and format Price
        price_m1 = float(series_1[-1])
        price_m2 = float(series_2[-1])
        accept_price_m1 = price_m1 * 1.03 if side_m1 =="BUY" else price_m1 * 0.97
        accept_price_m2 = price_m2 * 1.03 if side_m2 =="BUY" else price_m2 * 0.97
        tick_size_m1= markets["markets"][position_market_m1]["tickSize"]
        tick_size_m2= markets["markets"][position_market_m2]["tickSize"]
        accept_price_m1 = format_number(accept_price_m1, tick_size_m1)
        accept_price_m2 = format_number(accept_price_m2, tick_size_m2)

        # Close positions
        try:
           
           # Close positions for market 1
           print(">>> Closing market 1 <<<")
           print(f"Closing position for {position_market_m1}")
           
           close_order_m1 = place_market_order(
              client,
              market=position_market_m1,
              side=side_m1,
              size=position_size_m1,
              price=accept_price_m1,
              reduce_only=True,
            )
           base_id = close_order_m1["order"]["id"]
           print(close_order_m1["order"]["id"])
           print(">>> Closing <<<")
           
           # Protect API
           time.sleep(1)

           # Close positions for market 2
           print(">>> Closing market 2 <<<")
           print(f"Closing position for {position_market_m2}")
           
           close_order_m2 = place_market_order(
              client,
              market=position_market_m2,
              side=side_m2,
              size=position_size_m2,
              price=accept_price_m2,
              reduce_only=True,
            )
           quote_id = close_order_m2["order"]["id"]
           print(close_order_m2["order"]["id"])
           print(">>> Closing <<<")
           
           # Determine amount - m1
           amount_m1 = accept_price_m1*position_size_m1
           if position_side_m1 == "SELL":
                amount_m1 = -accept_price_m1*position_size_m1

           # Determine amount - m2
           amount_m2 = accept_price_m2*position_size_m2
           if position_side_m2 == "SELL":
                amount_m2 = -accept_price_m2*position_size_m2

           # Store closed positions
           date = datetime.datetime.now()

           closed_pairs = []

           closed_pairs.append({
                "closed_date":date.isoformat(),
                "closed_base_id":base_id,
                "closed_base_market": position_market_m1,
                "closed_base_side": side_m1,
                "closed_base_price": accept_price_m1,
                "closed_base_size": position_size_m1,
                "closed_base_amount": amount_m1,
                "pnl_base": round(pnl_1, 2),
                "closed_quote_id":quote_id,
                "closed_quote_market": position_market_m2,
                "closed_quote_side": side_m2,
                "closed_quote_price": accept_price_m2,
                "closed_quote_size": position_size_m2,
                "closed_quote_amount": amount_m2,
                "pnl_quote": round(pnl_2, 2),
                "closed_z_score":z_score_current,
                "pair_pnl": round(pnl, 2),
                "pair_pnl_percent": round(pnl_percent, 2),
            })

           # Create and save DataFrame
           df_auto_close = pd.DataFrame(closed_pairs)
           df_auto_close.to_csv("dydxtradebot/program/output/closed_positions.csv",mode='a', index= False, header= False)
           send_message(f"Bot closed the pair:\n\n{position_market_m1}:\nSide: {side_m1}, Size: {position_size_m1}, Price: {accept_price_m1}$  \n-- VS -- \n{position_market_m2}: \
                        \nSide: {side_m2}, Size: {position_size_m2}, Price: {accept_price_m2}$\n\nZ-Score: {z_score_current}\nPair PnL: {round(pnl,2)}$\nPair PnL %: {round(pnl_percent,2)}%")
           
           with open(f"dydxtradebot/program/closed_positions.txt", "w") as f:
              f.write(f"func_entry_pairs executed {position_market_m1} VS {position_market_m2} in {date.isoformat()} \n\nBase id:{base_id}\nQuote ID:{quote_id}  ")
              f.write("------")
           
        except Exception as e:
           print(f"Exit failed for {position_market_m1} with {position_market_m2}: {e}")
           save_output.append(position)

    # Keep record  if items and save
    else:
       save_output.append(position)

# Save remaining items
    print(f"{len(save_output)} Items remaining. Saving file...")
    with open("dydxtradebot/program/bot_agents.json", "w") as f:
       json.dump(save_output, f)


           


   


    







    
