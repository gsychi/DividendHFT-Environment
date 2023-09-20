import numpy as np
import logging
import matplotlib.pyplot as plt

from tradingenv.order import * 
from tradingenv.orderbook import *
from tradingenv.traders import *

class World:
    
    def __init__(self, dividend_var=0.5, dividend_interval=10000, news_rarity=15000, traders=[RandomAITrader("Gordon"), RandomAITrader("James"), RandomAITrader("Mila"), RandomAITrader("Mina")]):
        
        # Log
        self.time = 0 
        self.log = logging.getLogger("World")
        logging.basicConfig(level = logging.INFO)
        
        # Dividend Variables
        self.dividend_var: float = dividend_var
        self.dividend_history: List[float] = []
        self.dividend: float = np.random.normal(0, dividend_var)
        self.dividend_interval: int = dividend_interval
        
        # News variables
        self.news_rarity: float = news_rarity
        self.daily_news_sentiment: float = np.random.normal(0, 1/self.news_rarity)
        
        # Orderbook
        self.orderbook: OrderBook = OrderBook() # todo: make orderbook class
        self.price_history: List[float] = [0]
        
        # Traders/Entities
        self.traders: List[Trader] = traders
        self.trader_hashtable: dict = {self.traders[i].name: i for i in range(len(self.traders))}
            
        self.total_asset_value = sum(x.total_asset_value for x in self.traders)
        self.trades_per_person = {i: [] for i in range(len(self.traders))}
        self.transactions = []
        self.capital_history = [[x.capital for x in self.traders]]
        self.asset_value_history = [[x.total_asset_value for x in self.traders]]
        
    def next_ply(self): # this sets us for the next turn
        self.time += 1
    
    def __str__(self):
        state = "Time: " + str(self.time)
        state += "\nNext Dividend payout: " + str(round(self.dividend, 2))
        state += "\nTime till payout: " + str(self.dividend_interval-self.time%self.dividend_interval)
        state += "\nDaily News Sentiment: " + str(round(self.daily_news_sentiment, 2))
        # state += "\n\n\nTrader Positions:\n" + '\n'.join(x.__str__() for x in self.traders)
        return state
    
    def run_ply(self, verbose=False): # this allows us to simulate the actions done in a given step
    
        # payout and reset dividends. We will say that you cannot trade on the time step that dividends are given out
        if self.time % self.dividend_interval == 0 and not self.time == 0:
            
            # payout dividend
            for i in range(len(self.traders)):
                final_dividends_gained = 0
                for trade in self.traders[i].trades:
                    final_dividends_gained += (self.dividend * trade['position'])
                if verbose:
                    self.log.info(f"{self.traders[i].name} received {str(final_dividends_gained)} from dividends.")
                self.traders[i].capital += final_dividends_gained
            
            # reset dividend
            self.dividend_history.append(self.dividend)
            self.dividend = np.random.normal(0, self.dividend_var)
            if verbose:
                self.log.info(f"Dividend paid out { str(round(self.dividend_history[-1], 3))}, new dividends set at {str(round(self.dividend, 3))}.")
                
        # Update the fair for every trader estimate
        if self.time % self.dividend_interval == 0:
            for i in range(len(self.traders)):
                if type(self.traders[i]) == ContestantTrader:
                    self.traders[i].dividend_estimate = np.random.normal(self.dividend, max(self.traders[i].prediction_offness/2, self.dividend*self.traders[i].prediction_offness))
                    
        # set daily news sentiment. Only really big news, i.e. Above 1 is a big news article
        self.daily_news_sentiment = np.random.rand()
        if abs(self.daily_news_sentiment) < 1/self.news_rarity:
            if verbose:
                self.log.info("News sentiment large at time step, will affect trading behaviour.")

        # TODO: ensure that they can only submit one market order!!
        # write a quote
        kwargs_list = []
        for trader in self.traders:
            # write a quote
            if type(trader) == ContestantTrader:
                new_kwargs = [dict(x, **{'marketmaker_name': trader.name}) for x in trader.create_quotes(self.time, current_price=self.orderbook.current_price, orderbook=self.orderbook.get_anonymized_book(), transactions=self.transactions)]
                kwargs_list += new_kwargs
            else:
                new_kwargs = [dict(x, **{'marketmaker_name': trader.name}) for x in trader.create_quotes(self.time, current_price=self.orderbook.current_price)]
                kwargs_list += new_kwargs
        for kwargs in kwargs_list:
            self.orderbook.submit_order(Order(**kwargs))

        # Sort order book by nicest bids
        self.orderbook.sort_book(time=self.time)
        new_orders = self.orderbook.fill_order(time=self.time)
        self.transactions += new_orders
        self.price_history.append(self.orderbook.current_price)

        # Update positions for based on news_order
        for transaction in new_orders:

            buyer_idx = self.trader_hashtable[transaction['buyer']]
            seller_idx = self.trader_hashtable[transaction['seller']]

            # Let's do it from the buyer's persperctive
            buy_trade = {'position': transaction['qty'],
                        'order_price': transaction['order_price'],
                        'transaction_time': transaction['transaction_time']}
            sell_trade = {'position': -transaction['qty'],
                        'order_price': transaction['order_price'],
                        'transaction_time': transaction['transaction_time']}


            self.trades_per_person[buyer_idx].append(buy_trade)
            self.trades_per_person[seller_idx].append(sell_trade)

            self.traders[buyer_idx].capital -= (transaction['qty'] * transaction['order_price'])
            self.traders[seller_idx].capital += (transaction['qty'] * transaction['order_price'])

        total_trades = 0
        total_asset_value = 0
        for key in self.trades_per_person:
            self.traders[key].trades = self.trades_per_person[key]
            total_trades += len(self.trades_per_person[key])
            total_asset_value += self.traders[key].total_asset_value
            self.traders[key].update_asset_value(current_price=self.orderbook.current_price)

        assert (total_trades/2) == len(self.transactions)
        assert round(total_asset_value, 2) == round(self.total_asset_value, 2)

        self.capital_history.append([x.capital for x in self.traders])
        self.asset_value_history.append([x.total_asset_value for x in self.traders])
        
    def plot_stock_history(self):
        plt.figure(figsize=(12,8))
        plt.plot(self.price_history)
        plt.show()
        
    def plot_stock_history_with_dividend(self):
        tmp = []
        for dividend in self.dividend_history:
            tmp += [dividend] * self.dividend_interval
        plt.figure(figsize=(12,8))
        plt.plot(self.price_history)
        plt.plot(tmp)
        plt.show()
        
    def plot_capital_history(self):
        plt.figure(figsize=(12,8))
        tmp = np.array(self.capital_history)
        for i in range(len(tmp[0])):
            plt.plot(tmp[:, i], label=self.traders[i].name)
        plt.legend()
        plt.show()
        
    def plot_asset_value_history(self):
        plt.figure(figsize=(12,8))
        tmp = np.array(self.asset_value_history)
        for i in range(len(tmp[0])):
            plt.plot(tmp[:, i], label=self.traders[i].name)
        plt.legend()
        plt.show()