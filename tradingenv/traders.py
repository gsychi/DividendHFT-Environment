import numpy as np
import logging
import base64
import typing

from tradingenv.order import *
from tradingenv.orderbook import *

class Trader:
    def __init__(self, name, capital=10000):
        
        # Basic information for a trader
        self.name = name # their name
        self.capital = capital # liquid money they possess (i.e. purchasing power)
        self.trades = []
        self.total_asset_value = capital
        
    def __str__(self):
        position = 0
        for trade in self.trades:
            position += trade['position']
            
        state = "Trader/Market Maker Name: " + self.name 
        state += "\nLiquid Capital: " + str(round(self.capital, 2))
        state += "\nPosition: " + str(round(position, 2))
        state += "\nTotal Asset Value: " + str(round(self.total_asset_value, 2))
        state += "\nLast 10 Trades (out of " + str(len(self.trades)) + "): \n" 
        state += '\n'.join([str(i+1)+'. '+str(self.trades[-i-1]) for i in range(min(len(self.trades), 10))])
        return state
    
    def update_asset_value(self, current_price=0):
        cur_val = self.capital
        for trade in self.trades:
            cur_val += trade['position'] * (current_price - trade['order_price'])
        self.total_asset_value = cur_val
        return self.total_asset_value 
    
    def create_quotes(self, time, current_price=0):  # Here, a trader just sends in their quotes
        return []
        
class RandomAITrader(Trader):
    
    def __init__(self, name, capital=10000, eagerness=0.01, marketorder_eagerness=0.01, size_aggression=5, bullish=0.5, aggression=5, unpredictability=2):
        
        # Basic information for a trader
        super().__init__(name, capital)
        self.trades = []
        self.total_asset_value = capital
        
        # Trader Personality
        self.eagerness = eagerness # scaled from 0 to 1, higher = more eager to make a market
        self.marketorder_eagerness = marketorder_eagerness # given that they are trying to take on a position, what is the likelihood they are willing to take it at any price
        self.size_aggression = size_aggression # this is the average size of their bids
        self.bullish = bullish # this determines how likely they will take a positive directional belief in the stock
        self.aggression = aggression # this determines how tight they are willing to make the market
        self.unpredictability = unpredictability # this determines how possible they are to being unpredictable
        self.implied_price = 0
    
    def __str__(self):
        position = 0
        for trade in self.trades:
            position += trade['position']
            
        state = "Trader/Market Maker Name: " + self.name 
        state += "\nLiquid Capital: " + str(round(self.capital, 2))
        state += "\nPosition: " + str(round(position, 2))
        state += "\nTotal Asset Value: " + str(round(self.total_asset_value, 2))
        state += "\nLast 10 Trades (out of " + str(len(self.trades)) + "): \n" 
        state += '\n'.join([str(i+1)+'. '+str(self.trades[-i-1]) for i in range(min(len(self.trades), 10))])
        return state
    
    def update_asset_value(self, current_price=0):
        cur_val = self.capital
        for trade in self.trades:
            cur_val += trade['position'] * (current_price - trade['order_price'])
        self.total_asset_value = cur_val
        return self.total_asset_value 
    
    def create_quotes(self, time, current_price=0):  # Here, a trader just sends in their quotes
        
        # First of all, we want to determine the eagerness to make a bid.
        if np.random.rand() > self.eagerness or self.capital <= 0 or self.total_asset_value <= 0: # do not make any action
            return []
        else:
            bet_size = max(1, int(np.random.normal(self.size_aggression, self.size_aggression/2)))
            buy_price = round(np.random.normal(current_price - (1.5/self.aggression), self.unpredictability * 0.5/self.aggression), 3)
            sell_price = round(np.random.normal(current_price + (1.5/self.aggression), self.unpredictability * 0.5/self.aggression), 3)
            
            if np.random.rand() < self.bullish:
                if np.random.rand() < self.marketorder_eagerness: # they make a market order
                    quotes = {
                             'order_time': time,
                             'qty': bet_size,
                             'order_type':'M',
                             'direction':'B', 
                             'valid_until':time+1000}
                    return [quotes]
                elif self.capital - bet_size * buy_price >= 0:
                    quotes = {
                             'order_time': time,
                             'qty': bet_size,
                             'order_type':'L',
                             'direction':'B', 
                             'valid_until':time+1000,
                             'order_price': buy_price}
                    return [quotes]
                else:
                    return None

            else:
                if np.random.rand() < self.marketorder_eagerness: # they make a market order
                    quotes = {
                             'order_time': time,
                             'qty': bet_size,
                             'order_type':'M',
                             'direction':'S', 
                             'valid_until':time+1000}
                    return [quotes]
                elif self.capital + bet_size * sell_price > 0:
                    quotes = {
                             'order_time': time,
                             'qty': bet_size,
                             'order_type':'L',
                             'direction':'S', 
                             'valid_until':time+1000,
                             'order_price': sell_price}
                    return [quotes]
                else:
                    return []
                
class ContestantTrader(Trader):
    def __init__(self, name, prediction_offness, capital=10000):
        super().__init__(name, capital)
        self.trades = []
        self.total_asset_value = capital
        
        # guess on dividends
        self.prediction_offness = prediction_offness
        self.dividend_estimate = None
   
    def create_quotes(self, time, current_price=0, orderbook=None, transactions=None):
        # The `create_quotes` function is used to generate quotes for a trader. 

        # The parameters that you know as a trader are:
        # - time: the current time in the trading environment
        # - current_price: the current price of the stock
        # - orderbook: the current state of the order book, including all outstanding orders and their details
        # - self.dividend_estimate: your initial predicted dividend prediction on the day that the last dividend was paid out at. 
        # You will also know any variable defined in the __init__ function.
        
        # The function should return a list of quotes in the following format:
        # [{'order_time': int, 'qty': int, 'order_type': 'L' or 'M', 
        # 'direction': 'B' or 'S', 'valid_until': int, 'order_price': float}]
        # The market maker name will be added via the world environment 
        # If you decide not to make any bids, please return an empty list, i.e. []
        return []