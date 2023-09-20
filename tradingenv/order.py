import numpy as np
import logging
import base64
import typing

class Order:
    
    def __init__(self, marketmaker_name, order_time, qty, order_type, direction, valid_until, order_price=0, **kwargs): 
        
        # default values on the order
        self.marketmaker_name = marketmaker_name
        self.order_time = order_time
        
        self.qty = qty
        self.order_type = order_type  # this can be a market order, or a limit order, which we specify as 'M' or 'L'
        self.direction = direction # this is either 'B' for buy, or 'S' for sell
        self.valid_until = valid_until # this is the time step it is valid until
        
        # for a market order, this is invalid. For a limit order, we will require a price.
        # market orders are used just in case on a given day you think that you will take any
        # bid or ask just to get out or get into a position asap
        self.order_price = order_price 
        
        # Generate a unique ID for the transaction
        self.id = self.marketmaker_name + str(self.order_time) + str(self.qty) + str(self.order_type) + str(self.direction) + str(self.valid_until) + str(self.order_price)
        self.id = self.id.encode("utf-8")
        self.id = str(base64.b64encode(self.id))[2:-1]
        
    def __str__(self):
        if self.direction == "B":
            if self.order_type == "M":
                return self.id + ": " + self.marketmaker_name + " bid for " + str(self.qty) + ", good till " + str(self.valid_until) + ", order submitted at time " + str(self.order_time)
            else:
                return self.id + ": " +  self.marketmaker_name + " " + str(self.order_price) + " bid for " + str(self.qty) + ", good till " + str(self.valid_until) + ", order submitted at time " + str(self.order_time)        
        
        if self.direction == "S":
            if self.order_type == "M":
                return self.id + ": " + self.marketmaker_name + " " + str(self.qty) + " up, good till " + str(self.valid_until) + ", order submitted at time " + str(self.order_time)
            else:
                return self.id + ": " + self.marketmaker_name + " " + str(self.qty) + " at " + str(self.order_price) + ", good till " + str(self.valid_until) + ", order submitted at time " + str(self.order_time)
                
    
    def __lt__(self, obj):
        
        # 1. market orders always go first
        if self.order_type != obj.order_type:
            return self.order_type == "M"
        
        # if both are market orders, tiebreak is by order time, then by sizing
        if self.order_type == "M":
            if self.order_time != obj.order_time:
                return self.order_time < obj.order_time
            else:
                return self.qty > obj.qty
        
        # 2. the tightest limit orders are filled first, defined by distance from current price
        if self.order_type == "L":
            if self.order_price != obj.order_price:
                if self.direction == 'B': # realistically, we will only compare buys with other buys
                    return self.order_price > obj.order_price
                else:
                    return self.order_price < obj.order_price
            else:
                if self.order_time != obj.order_time:
                    return self.order_time < obj.order_time
                else:
                    return self.qty > obj.qty  
                
    def __le__(self, obj):
        
        # 1. market orders always go first
        if self.order_type != obj.order_type:
            return self.order_type == "M"
        
        # if both are market orders, tiebreak is by order time, then by sizing
        if self.order_type == "M":
            if self.order_time != obj.order_time:
                return self.order_time < obj.order_time
            else:
                return self.qty >= obj.qty
        
        # 2. the tightest limit orders are filled first, defined by distance from current price
        if self.order_type == "L":
            if self.order_price != obj.order_price:
                if self.direction == 'B': # realistically, we will only compare buys with other buys
                    return self.order_price > obj.order_price
                else:
                    return self.order_price <= obj.order_price
            else:
                if self.order_time != obj.order_time:
                    return self.order_time < obj.order_time
                else:
                    return self.qty >= obj.qty  
  
    def __eq__(self, obj):
        return (self.order_type == obj.order_type) and \
               (self.order_time == obj.order_time) and \
               (self.qty == obj.qty) and \
               (self.order_price == obj.order_price) # for market order, price should be 0 by default

