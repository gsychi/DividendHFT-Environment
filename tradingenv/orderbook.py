import numpy as np
import logging
import base64
import typing
import matplotlib.pyplot as plt
import copy
from tradingenv.order import * 

class OrderBook:
    def __init__(self):
        
        self.buy_orders: List[Order] = []
        self.sell_orders: List[Order] = []
        self.current_price = 0 # this is determined by the last trade price
        
    def submit_order(self, order: Order): # this adds a new order into the book
        if order.direction == 'B':
            self.buy_orders.append(order)
        if order.direction == 'S':
            self.sell_orders.append(order)
            
    # we need to sort the book to be in the right order. 
    # once an order is filled, the book is immediately updated.
    def sort_book(self, time): 
        
        # Filter out all the orders remaining
        self.buy_orders = [x for x in self.buy_orders if x.valid_until >= time]
        self.sell_orders = [x for x in self.sell_orders if x.valid_until >= time]
        
        # 1. market orders always go first
        # 2. the tightest limit orders are filled first, defined by distance from current price
        # 3. if things are the same, then the tiebreak is by time, then size
        self.buy_orders = sorted(self.buy_orders) 
        self.sell_orders = sorted(self.sell_orders) 
        
    def fill_order(self, time):
        
        # no orders can be filled if no buy or no sell orders
        if len(self.buy_orders) == 0 or len(self.sell_orders) == 0:
            return []
        
        orders_filled = []
        
        randomizer = np.random.random()
        # If there exists a buy AND sell market order, we want to fill the highest priority one at random
        if self.buy_orders[0].order_type == 'M' and self.sell_orders[0].order_type == 'M':
            if (self.buy_orders[0].order_time < self.sell_orders[0].order_time) or (self.buy_orders[0].order_time == self.sell_orders[0].order_time and randomizer < 0.5): # fill first buy
                qty_to_fill = self.buy_orders[0].qty
                
                idx = 0
                while qty_to_fill > 0:
                    if self.sell_orders[idx].order_type == 'L' and self.sell_orders[idx].marketmaker_name != self.buy_orders[0].marketmaker_name:
                        size = min(qty_to_fill, self.sell_orders[idx].qty)
                        qty_to_fill -= size
                        self.sell_orders[idx].qty -= size
                        self.buy_orders[0].qty -= size
                        self.current_price = self.sell_orders[idx].order_price
                        
                        filled_order = {'buyer': self.buy_orders[0].marketmaker_name,
                                        'seller': self.sell_orders[idx].marketmaker_name,
                                        'qty': size,
                                        'order_price': self.sell_orders[idx].order_price,
                                        'transaction_time': time
                        }
                        orders_filled.append(filled_order)
                    else: # order is market order, you cannot fill a market order with another market order
                        pass
                    
                    idx += 1
                    if idx >= len(self.sell_orders):
                        break
     
            else: # fill first sell
                qty_to_fill = self.sell_orders[0].qty
                    
                idx = 0
                while qty_to_fill > 0:
                    if self.buy_orders[idx].order_type == 'L' and self.buy_orders[idx].marketmaker_name != self.sell_orders[0].marketmaker_name:
                        size = min(qty_to_fill, self.buy_orders[idx].qty)
                        qty_to_fill -= size
                        self.buy_orders[idx].qty -= size
                        self.sell_orders[0].qty -= size
                        self.current_price = self.buy_orders[idx].order_price

                        filled_order = {'buyer': self.buy_orders[idx].marketmaker_name,
                                        'seller': self.sell_orders[0].marketmaker_name,
                                        'qty': size,
                                        'order_price': self.buy_orders[idx].order_price,
                                        'transaction_time': time
                        }
                        orders_filled.append(filled_order)
                    else: # order is market order, you cannot fill a market order with another market order
                        pass
                    
                    idx += 1
                    if idx >= len(self.buy_orders):
                        break
        # Otherwise, we fill the highest priority market order 
        elif self.buy_orders[0].order_type == 'M':
            qty_to_fill = self.buy_orders[0].qty
                
            idx = 0
            while qty_to_fill > 0:
                if self.sell_orders[idx].order_type == 'L' and self.sell_orders[idx].marketmaker_name != self.buy_orders[0].marketmaker_name:
                    size = min(qty_to_fill, self.sell_orders[idx].qty)
                    qty_to_fill -= size
                    self.sell_orders[idx].qty -= size
                    self.buy_orders[0].qty -= size
                    self.current_price = self.sell_orders[idx].order_price

                    filled_order = {'buyer': self.buy_orders[0].marketmaker_name,
                                    'seller': self.sell_orders[idx].marketmaker_name,
                                    'qty': size,
                                    'order_price': self.sell_orders[idx].order_price,
                                    'transaction_time': time
                    }
                    orders_filled.append(filled_order)
                else: # order is market order, you cannot fill a market order with another market order
                    pass

                idx += 1
                if idx >= len(self.sell_orders):
                    break
        elif self.sell_orders[0].order_type == 'M':
            qty_to_fill = self.sell_orders[0].qty
                    
            idx = 0
            while qty_to_fill > 0:
                if self.buy_orders[idx].order_type == 'L' and self.buy_orders[idx].marketmaker_name != self.sell_orders[0].marketmaker_name:
                    size = min(qty_to_fill, self.buy_orders[idx].qty)
                    qty_to_fill -= size
                    self.buy_orders[idx].qty -= size
                    self.sell_orders[0].qty -= size
                    self.current_price = self.buy_orders[idx].order_price

                    filled_order = {'buyer': self.buy_orders[idx].marketmaker_name,
                                    'seller': self.sell_orders[0].marketmaker_name,
                                    'qty': size,
                                    'order_price': self.buy_orders[idx].order_price,
                                    'transaction_time': time
                    }
                    orders_filled.append(filled_order)
                else: # order is market order, you cannot fill a market order with another market order
                    pass

                idx += 1
                if idx >= len(self.buy_orders):
                    break
        else: # Otherwise, we check if buy and sell cross
            
            if self.buy_orders[0].order_price > self.sell_orders[0].order_price: # if somebody is willing to buy at less than the sell order
                if self.buy_orders[0].order_time < self.sell_orders[0].order_time or \
                (self.buy_orders[0].order_time == self.sell_orders[0].order_time and randomizer < 0.5): # if buy order was put in first
                    qty_to_fill = self.buy_orders[0].qty
                    
                    idx = 0
                    while qty_to_fill > 0 and self.buy_orders[0].order_price > self.sell_orders[idx].order_price:
                        if self.sell_orders[idx].marketmaker_name != self.buy_orders[0].marketmaker_name:
                            size = min(qty_to_fill, self.sell_orders[idx].qty)
                            qty_to_fill -= size
                            self.sell_orders[idx].qty -= size
                            self.buy_orders[0].qty -= size
                            self.current_price = self.sell_orders[idx].order_price

                            filled_order = {'buyer': self.buy_orders[0].marketmaker_name,
                                            'seller': self.sell_orders[idx].marketmaker_name,
                                            'qty': size,
                                            'order_price': self.sell_orders[idx].order_price,
                                            'transaction_time': time
                            }
                            orders_filled.append(filled_order)
                        else:
                            pass
                        idx += 1
                        if idx >= len(self.sell_orders):
                            break
                        
                else:
                    qty_to_fill = self.sell_orders[0].qty
                    
                    idx = 0
                    while qty_to_fill > 0 and self.buy_orders[idx].order_price > self.sell_orders[0].order_price:
                        if self.buy_orders[idx].marketmaker_name != self.sell_orders[0].marketmaker_name:
                            size = min(qty_to_fill, self.buy_orders[idx].qty)
                            qty_to_fill -= size
                            self.buy_orders[idx].qty -= size
                            self.sell_orders[0].qty -= size
                            self.current_price = self.buy_orders[idx].order_price

                            filled_order = {'buyer': self.buy_orders[idx].marketmaker_name,
                                            'seller': self.sell_orders[0].marketmaker_name,
                                            'qty': size,
                                            'order_price': self.buy_orders[idx].order_price,
                                            'transaction_time': time
                            }
                            orders_filled.append(filled_order)
                        else:
                            pass
                        idx += 1
                        if idx >= len(self.buy_orders):
                            break
                        
        # remove all orders that are completely filled
        self.buy_orders = [x for x in self.buy_orders if x.qty > 0]
        self.sell_orders = [x for x in self.sell_orders if x.qty > 0]

        return orders_filled
        
    def __str__(self):
        return 'Buy Orders sorted by priority:\n\n' + '\n'.join([str(i+1) + ". " + order.__str__() for (i, order) in enumerate(self.buy_orders)]) + '\n\nSell Orders sorted by priority:\n\n' + '\n'.join([str(i+1) + ". " + order.__str__() for (i, order) in enumerate(self.sell_orders)])
    
    def __repr__(self):
        plt.hist([x.order_price for x in self.buy_orders if x.order_type == "L"], bins=len(self.buy_orders)//2, alpha=0.7)
        plt.hist([x.order_price for x in self.sell_orders if x.order_type == "L"], bins=len(self.buy_orders)//2, alpha=0.7)
        plt.show()
        return "Orderbook Histogram"
    
    def get_anonymized_book(self):
        anon_buys = copy.deepcopy(self.buy_orders)
        anon_sells = copy.deepcopy(self.sell_orders)
        for i in range(len(anon_buys)):
            anon_buys[i].marketmaker_name = "unknown"
        for i in range(len(anon_sells)):
            anon_sells[i].marketmaker_name = "unknown"
        return (anon_buys, anon_sells)
        
        