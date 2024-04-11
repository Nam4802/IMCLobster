from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import string

POSITION_LIMIT = {"STARFRUIT" : 20, "AMETHYSTS" : 20}
START_POSITION = {"STARFRUIT" : 0, "AMETHYSTS" : 0}

class Trader:

    data = {'STARFRUIT':[5040], 'AMETHYSTS':[10002]}

    # Function to just print a dict containing current mid price of all products
    def mid_price(self, order_depth):

        mid_price_all = {}

        for product in order_depth:
            mid_price = (list(order_depth[product].sell_orders.keys())[0] + list(order_depth[product].buy_orders.keys())[0]) / 2
            print(product + " current mid price : " + str(mid_price))

            mid_price_all[product] = mid_price

        return mid_price_all

    # Update data
    def update_data(self, order_depth):
        for product in order_depth:
            mid_price = (list(order_depth[product].sell_orders.keys())[0] + list(order_depth[product].buy_orders.keys())[0]) / 2
            Trader.data[product].append(mid_price)

    # Calculate moving average
    def calc_price_ma(self, data):

        MA_DUR = 5
        mavg = 0

        for i in range(min(len(data), MA_DUR)):
            mavg += data[-1 - i] / MA_DUR

        return mavg

    def run(self, state: TradingState):

        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("Position: " + str(state.position))
        #print("Observations: " + str(state.observations))
        data_s = Trader.data['STARFRUIT']
        data_a = Trader.data['AMETHYSTS']
        print("Last prices: STARFRUIT: " + str(data_s[-1]) + ", AMETHYSTS: " + str(data_a[-1]))

        result = {}

        self.mid_price(state.order_depths)
        self.update_data(state.order_depths)

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            if product == "STARFRUIT":
                acceptable_price = self.calc_price_ma(data_s)
            elif product == "AMETHYSTS":
                acceptable_price = 10000

            #print("Acceptable price : " + str(acceptable_price))
            #print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
    
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if int(best_ask) < (acceptable_price):
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))
    
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if int(best_bid) > (acceptable_price):
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))
            
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1
        return result, conversions, traderData
