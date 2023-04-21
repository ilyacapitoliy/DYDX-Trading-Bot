from constants import ZSCORE_THRESH, USD_PER_TRADE, USD_MIN_COLLATERAL, TOKEN_FACTOR_10
from func_utils import format_number
from func_public import get_candles_recent
from func_cointegration import calculate_zscore
from func_messaging import send_message_berta
from func_private import is_open_positions
from func_bot_agent import BotAgent
import pandas as pd
import json
import uuid
import datetime
import time

from pprint import pprint


# Open positions
def open_positions(client):

    """
    Manage finding triggers for trade entry
    Store trades for managing later on exit function
    """

    # Load cointegrated pairs
    df = pd.read_csv("dydxtradebot/program/cointegrated_pairs.csv")


    # Get markets from referencing of min order size, tick size etc
    markets = client.public.get_markets().data

    # Initialize container for BotAGent results
    bot_agents = []

    #Opening JSON file
    try:
        open_positions_file = open("dydxtradebot/program/bot_agents.json")
        open_positions_dict = json.load(open_positions_file)
        for p in open_positions_dict:
          bot_agents.append(p)
    except:
        bot_agents = []
    

    # Find ZScore triggers
    for index, row in df.iterrows():

        # Extract variables
        base_market = row["base_market"]
        quote_market = row["quote_market"]
        hedge_ratio = row["hedge_ratio"]
        half_life = row["half_life"]

        # Get prices
        series_1 = get_candles_recent(client, base_market)
        series_2 = get_candles_recent(client, quote_market)
        
        # Get ZScore
        if len(series_1) > 0 and len(series_1) == len(series_2):
            spread = series_1 - (hedge_ratio * series_2)
            z_score = calculate_zscore(spread).values.tolist()[-1]

            # Establish if potential trade
            if abs(z_score) >= ZSCORE_THRESH:

                potential_b_price = series_1[-1]
                potential_q_price = series_2[-1]

                # Determine side 
                potential_b_side = "BUY" if z_score < 0 else "SELL"
                potential_q_side = "BUY" if z_score > 0 else "SELL"

                pot_date = datetime.datetime.now()

                potential_pairs = []

                # Opening JSON file
                with open("dydxtradebot/program/output/potential_trades.json") as f:
                    pot_pairs_dict = json.load(f)

                for m in pot_pairs_dict:
                    m.update({"date": pot_date.isoformat(),
                            "base_market": base_market,
                            "base_side": potential_b_side,
                            "base_price": potential_b_price,
                            "quote_market": quote_market,
                            "quote_side": potential_q_side,
                            "quote_price": potential_q_price,
                            "z_score": z_score,
                            "half_life": half_life})
                    potential_pairs.append(m)

                with open("dydxtradebot/program/output/potential_trades.json", "a") as f:
                    json.dump(potential_pairs, f)
                

                # Protect API
                time.sleep(15)
                
                send_message_berta(f"New opportunity for arbitrage:\n\n{base_market}:\n  {potential_b_side} at price: {potential_b_price}$\n --VS-- \n{quote_market}:\n  {potential_q_side} at price: {potential_q_price}$\n\nZ-Score: {round(z_score,2)}\nHalf-Life: {int(half_life)} hours")
                
                time.sleep(15)
                
                # Ensure like-for-like not already open (diversify trading)
                is_base_open = is_open_positions(client, base_market)
                is_quote_open = is_open_positions(client, quote_market)

                # Place trade
                if not is_base_open and not is_quote_open:

                    # Determine side 
                    base_side = "BUY" if z_score < 0 else "SELL"
                    quote_side = "BUY" if z_score > 0 else "SELL"

                    # Get acceptable price in string format with correct number of decimals
                    base_price = series_1[-1]
                    quote_price = series_2[-1]
                    accept_base_price = float(base_price) * 1.01 if z_score < 0 else float(base_price) * 0.99
                    accept_quote_price = float(quote_price) * 1.01 if z_score > 0 else float(quote_price) * 0.99
                    failsafe_base_price = float(base_price) * 0.05 if z_score < 0 else float(base_price) * 1.7
                    base_tick_size = markets["markets"][base_market]["tickSize"]
                    quote_tick_size = markets["markets"][quote_market]["tickSize"]

                    # Format prices
                    accept_base_price = format_number(accept_base_price, base_tick_size)
                    accept_quote_price = format_number(accept_quote_price, quote_tick_size)
                    accept_failsafe_base_price = format_number(failsafe_base_price, base_tick_size)
                
                    # Get size
                    # base_quantity = 1 /base_price * USD_PER_TRADE
                    # quote_quantity = 1 /quote_price * USD_PER_TRADE
                    # Get size
                    base_quantity = 1 / base_price * USD_PER_TRADE
                    quote_quantity = 1 / quote_price * USD_PER_TRADE
                    ### -ADD HERE- ###
                    for particolari in TOKEN_FACTOR_10 :
                        if base_market== particolari :
                            base_quantity= float(int(base_quantity/100)*100) 
                        if quote_market== particolari :
                            quote_quantity= float(int(quote_quantity/100)*100) 
                    ####-THE REST REMAIN AS THE ORIGINAL VERSION -###
                    base_step_size = markets["markets"][base_market]["stepSize"]
                    quote_step_size = markets["markets"][quote_market]["stepSize"]

                    # Format sizes
                    base_size = format_number(base_quantity, base_step_size)
                    quote_size = format_number(quote_quantity, quote_step_size)

                    # Ensure size
                    base_min_order_size = markets["markets"][base_market]["minOrderSize"]
                    quote_min_order_size = markets["markets"][quote_market]["minOrderSize"]
                    check_base = float(base_quantity) > float(base_min_order_size)
                    check_quote = float(quote_quantity) > float(quote_min_order_size)

                    # Determine amount - m2
                    amount_m1 = float(accept_base_price)*float(base_size)
                    if base_side == "SELL":
                        amount_m1 = -float(accept_base_price)*float(base_size)

                    # Determine amount - m2
                    amount_m2 = float(accept_quote_price)*float(quote_size)
                    if quote_side == "SELL":
                        amount_m2 = -float(accept_quote_price)*float(quote_size)

                    # If checks pass, place trades
                    if check_base and check_quote:

                        # Check account balance
                        account = client.private.get_account()
                        free_collateral = float(account.data["account"]["freeCollateral"])
                        print(f"Balance: {free_collateral} and minimum at {USD_MIN_COLLATERAL}")

                        # Guard: Ensure collateral
                        if free_collateral*10 < USD_MIN_COLLATERAL:
                            break

                        # Create Bot Agent
                        bot_agent = BotAgent(
                            client,
                            market_1=base_market,
                            market_2=quote_market,
                            base_side=base_side,
                            base_size=base_size,
                            base_price=accept_base_price,
                            quote_side=quote_side,
                            quote_size=quote_size,
                            quote_price=accept_quote_price,
                            accept_failsafe_base_price=accept_failsafe_base_price,
                            z_score=z_score,
                            half_life=half_life,
                            hedge_ratio=hedge_ratio
                        )

                        # Open Trades
                        bot_open_dict = bot_agent.open_trades()

                        base_id = bot_open_dict["order_id_m1"]
                        quote_id = bot_open_dict["order_id_m2"]

                        unique_id = str(uuid.uuid4())
                        pair_id = unique_id[0:12]

                        # Handle success in opening trades
                        if bot_open_dict["pair_status"] == "LIVE":

                            # Append success in opening trades
                            bot_agents.append(bot_open_dict)
                            del(bot_open_dict)

                            # Store open positions
                            
                            date = datetime.datetime.now()

                            open_pairs = []
                                                    
                            open_pairs.append({
                            "pair_id":pair_id,
                            "open_date":date.isoformat(),
                            "open_base_id": base_id,
                            "open_base_market": base_market,
                            "open_base_side": base_side,
                            "open_base_price": accept_base_price,
                            "open_base_size": base_size,
                            "open_base_amount": amount_m1,
                            "open_quote_id": quote_id,
                            "open_quote_market": quote_market,
                            "open_quote_side": quote_side,
                            "open_quote_price": accept_quote_price,
                            "open_quote_size": quote_size,
                            "open_quote_amount": amount_m2,
                            "open_z_score":z_score,
                            })
                        
                            df_entry = pd.DataFrame(open_pairs)
                            df_entry.to_csv("dydxtradebot/program/output/open_positions.csv",mode='a', index= False, header=False)

                            # Confirm live status
                            print("Trade status: Live")
                            print("---")                    
     
    # Save agents
    print(f"Success: Manage open trade checked")
    if len(bot_agents) > 0:
        with open("dydxtradebot/program/bot_agents.json", "w") as f:
            json.dump(bot_agents, f)
        
