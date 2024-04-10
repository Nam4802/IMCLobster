from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import string

POSITION_LIMIT = {"STARFRUIT" : 20, "AMETHYSTS" : 20}
START_POSITION = {"STARFRUIT" : 0, "AMETHYSTS" : 0}

class Trader:

    data = {'STARFRUIT':[5000], 'AMETHYSTS':[10000]}

    def current_price(self, order_depth):

        current_price_all = {}

        for product in order_depth:
            current_price = list(order_depth[product].sell_orders.keys())[0]
            print(product + " current price : " + str(current_price))

            current_price_all[product] = current_price

        return current_price_all


    def update_data(self, order_depth):
        for product in order_depth:
            Trader.data[product].append(list(order_depth[product].sell_orders.keys())[0])


    def run(self, state: TradingState):

        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("Position: " + str(state.position))
        #print("Observations: " + str(state.observations))
        data_s = Trader.data['STARFRUIT']
        data_a = Trader.data['AMETHYSTS']
        print("Last prices: STARFRUIT: " + str(data_s[-1]) + ", AMETHYSTS: " + str(data_a[-1]))

        result = {}

        self.current_price(state.order_depths)
        self.update_data(state.order_depths)

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            if product == "STARFRUIT":
                acceptable_price = 5055
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
