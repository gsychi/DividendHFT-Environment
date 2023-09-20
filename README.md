# DividendHFT-Environment

### **Introduction**

  
Over the past few decades (and perhaps longer), there have been many attempts by trading firms and academia alike to build mathematical or computational simulations to understand how the market works.  
  
Let's begin with the simplest concept: suppose there exists a virtual environment with _n_ agents, each randomly crossing the bid ask spread over a specified time period. With no intelligence, the value of this single stock acts purely like Brownian Motion: it is equivalent to a random walk model where, at every time point _t_, the probability that two agents will agree to a transaction at some cost 5% above current fair is the same as the probability that two agents will agree to a transaction at some cost 5% below current fair. (these numbers are purely for explanation purposes)  
  
The real world, however, is not so simple. From as early as the Tulip Mania in 1637, there have been many instances when a large bid/ask made by a market participant has a large effect on the price of a commodity. In the presence of intelligent agents, we cannot blindly assume Brownian motion, or that everyone acts in a random manner after a large bid; we must understand the market impact of our own actions, especially when we want to switch from a current portfolio to a different one in the future.  
  
This is where our simulation comes in. Rather than following a set price, this simulation relies on an orderbook, and orders from market participants (you!), to dictate exactly how the price moves. There will be a few random agents that trade infrequently and in a less intelligent manner, but make no mistake: **your** behaviour will change the market. **Moreover**, it is a chance to try strategies in the real world, for you to act as a trading firm and test out a strategy that would otherwise be impossible due to higher latency or insufficient data. Will you run a more arbitrage based strategy? Or do you think you have long term strategies to read the market? Find out in this game -- completely free to play, and with prizes to boot.  
  

### **World Environment**

  

*   The simulation is split into groups of 25000 time steps, which we refer to as a month, i.e. it is a turn-based game. The simulation starts at _t_\=0. You have an opportunity to submit as many bids as you want at every time step; however, only one bid/ask will be filled at each turn.
*   There only exists one commodity in the market (which we will call ABC) that starts at price $0 and is only affected by bid and ask spreads made by agents.
*   At the beginning of each month (i.e. every time step such that x mod 25000 is 1), a dividend drawn from the normal distribution N(0, 1) is defined, and each market participant is assigned a noisy prediction on the dividend that will be paid at the end of the month (i.e. every time step divisible to 25000). This prediction does not change over time, and can only be updated through algorithmic methods, based on your own due diligence of the market.  
    
*   Yes, prices can be negative! This was designed to maintain market neutrality, i.e. in expectation, if you buy a single share of ABC and hold it infinitely, your expected payoff is 0. In the real world, this would be equivalent to buying/selling shares for a stock you expect to have a similar drift term to SPY under Geometric Brownian Motion (otherwise if it performs worse, you would simply not buy or short the share, and the reverse if ABC performs better)

Hopefully this gives a bit of insight into how the world works! Now, let's look into the more technical details: what an order looks like in the simulation, and how the orderbook works.  
  

### **Order and the Orderbook**

  

            `class Order:          def __init__(self, marketmaker_name, order_time, qty, order_type, direction, valid_until,                      order_price=0, **kwargs):                           # default values on the order             self.marketmaker_name = marketmaker_name             self.order_time = order_time                          self.qty = qty             self.order_type = order_type # this can be a market or limit order, specified by 'M' or 'L'             self.direction = direction # this is either 'B' for buy, or 'S' for sell             self.valid_until = valid_until # this is the time step it is valid until                          # for a market order, a price is not required. For a limit order, we will require a price.             # market orders are used just in case on a given day you think that you will take any             # bid or ask just to get out or get into a position asap             self.order_price = order_price` 
            
            

This is how the simulation represents (and processes) a financial order that can be placed in a market. An **order** has several attributes including the market maker's name, the order time, the quantity, the order type (which can be either a market order or a limit order), the direction (either buy or sell), the time until which the order is valid, and the order price (which is only applicable for limit orders).  
  
There are only two types of order types: a market order (which means you are happy to take any price in the market right now; you will be filled immediately if you are the only one to place a market order in the orderbook), and a limit order (which means you are happy to buy/sell up to a specified price point in the market). Orders such as GTC (good till cancelled) can be simulated by submitting a new quote every day and setting the expiry date to be the next date, for which your algorithm will continuously put out the same quote until it is 'cancelled'.  
  
Now, we look at the orderbook. There are a few functions that the orderbook has, but by far the most important function is `def fill_order(self, time)`. The pipeline that the function has is as follows:  
  

*   The orderbook will sort the buy orders by price, with tiebreaker being time; the same goes for sell orders. However, it will always try to fill a market order if possible, with ties broken by time submitted; if a buy and sell market order is submitted at the same time, then only one of these orders is filled at random.
*   If there exists no market orders, then limit orders are filled if the tightest bid-ask market crosses. The bid is filled at the price of the market participant that submitted first; if they are submitted at the same time, then again the order price is chosen from the buyer/seller at random.
*   The price of commodity is set at the last agreed price of a successful transaction.
*   Once an order is submitted, it cannot be removed. Please be very careful about what you are submitting, and make sure that you are wary of market conditions!

  
Of course, this explanation would not be complete without understanding the agents that will be in the simulation. We will begin first by discussing a bit on how the bots will behave, and then talk about the intricacies of the data YOU will be allowed to use!  
  

### **Agents**

In the simulation, there will be two types of traders: generated random bots, and then other human contestants (that are given the same premise and data as you)! The number of bot personalities and types may be increased over time \[and we will send patch notes if required\], but for now there will only be one relevant agent type that you can learn their behavior from here.  
  
The random bots are analogous to a casual market player in the real world, where they may be looking for alpha, but in a simulation setting they are unaware about strategies and are just looking for a chance to hold a position for shares depending on their (uninformed) gut instinct. At every given time step, they have the opportunity to submit a single limit order in a direction they prefer and with a specified indifference price point. These traders are more trigger heavy on average to simulate multiple players in the market at once. We'll try not to reveal more about the agents in detail (otherwise they will be too easy to predict), but here are a few things to take into consideration:

*   These agents will only submit a bid in a single direction. However, there will be certain traders that are more 'bullish', and others that are more 'bearish'.
*   Similarly, aggression is a feature that exists for these traders to determine how aggressive they are going to set their prices, or how aggressively they will size their bids.
*   There are features such as eagerness and unpredictability that determine how unpredictable or eager a trader is to make a market.

  
That should be enough about the general agents! Now, let's learn a bit more about what you and your contestants will look like...  
  

### **Contestant Traders**

As a contestant trader, this is how you are initialized in the trading environment:

        `class ContestantTrader(Trader):         def __init__(self, name, prediction_offness, capital=10000):             super().__init__(name, capital)             self.trades = []             self.total_asset_value = capital                          # guess on dividends             self.prediction_offness = prediction_offness             self.dividend_estimate = None`
        
        

These are the features that define you as a market maker:  
  

*   #### **Name**
    
    This is something you can choose as the name that you'd like to be addressed as on the leaderboards. It has no other purpose other than as an identification tool. This will be equivalent to your username.
  
*   #### **Capital**
    
This defines how much starting capital you are given to trade with. Since the market is populated with only one asset worth $0 to begin with, this capital should be plenty for good returns. Everyone is given the same value to begin.  
  
*   #### **Prediction offness**
    
    This is by far the most important feature: it determines how noisy your estimate for the dividend is on average. Each month, every trader will have a unique predicted dividend, generated via a random number drawn from normal distribution. The mean of this normal distribution is the actual dividend, whereas the standard deviation is defined as  
      
    `max(prediction_offness/2, dividend*prediction_offness)`  
      
    This ensures that predictions are not too off when dividend outcomes are small. Everyone is given the same `prediction_offness` value, so it's time to make markets.
  

Now that this is defined, let's talk about your task in the challenge. Indeed, your goal is to edit the following function:  

        ``def create_quotes(self, time, current_price=0, orderbook=None):         # The `create_quotes` function is used to generate quotes for a trader.           # The parameters that you know as a trader are:         # - time: the current time in the trading environment         # - current_price: the current price of the stock         # - orderbook: the current state of the order book, including all outstanding orders and their details         # - self.dividend_estimate: your initial predicted dividend prediction on the day that the last dividend was paid out at.          # You will also know any variable defined in the __init__ function.                  # The function should return a list of quotes in the following format:         # [{'order_time': int, 'qty': int, 'order_type': 'L' or 'M',          # 'direction': 'B' or 'S', 'valid_until': int, 'order_price': float}]         # The market maker name will be added via the world environment          # If you decide not to make any bids, please return an empty list, i.e. []          return []``
        
    

As can be seen in the function above, you are allowed to use (and edit) any of the variables defined in the `__init__` statement above, alongside the inputs to the `create_quotes` function (time, current\_price, and orderbook). A few clarifications about the potential data you can access:  
  

*   **time:** this is an natural number greater than 0.
*   **current\_price:** this is a real number (float) that represents the current price of the stock
*   **orderbook:** a tuple consisting of two lists. The first list is a list of buy orders, and the second list is a list of sell orders.
*   **transactions:** a list of dictionaries, for which all dictionaries contain the entries 'buyer', 'seller', 'qty' (quantity), and 'order\_price' (i.e. the price of the transaction).
*   **self.dividend\_estimate:** a float that represents an estimate of what the dividend paid at the end of the month will be
*   **self.trades:** a list of dictionaries (similar to the variable transactions), but filtered to only contain the transactions you have made.

As you start writing your strategy, please be wary of the following pointers:  
  

*   The orderbook you are given is anonymous -- you will not know who is trading, and/or who is making bids. The orderbook will only give you access for all the unfilled bids in the market.
*   You are allowed to have a short position! However, keep in mind that if you do have a short position, then you will be the one paying out the dividend to those who have a long position.
*   If your capital is less than 0, you are not allowed to trade! Be careful...
*   Your code will run through a sanity check first to ensure that it can be submitted. If it does not pass, then your submission will not be processed...

Whew, that was a lot! Hope this makes all sense. Best of luck, and have fun!
