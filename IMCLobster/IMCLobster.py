from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import string

POSITION_LIMIT = {"STARFRUIT" : 20, "AMETHYSTS" : 20}
START_POSITION = {"STARFRUIT" : 0, "AMETHYSTS" : 0}
MAKE_MARGIN = {"STARFRUIT" : 1, "AMETHYSTS" : 1}
MAKE_VOL = {"STARFRUIT": 5, "AMETHYSTS": 5}

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

    def market_take(self, order_depth, product, position, take_price):
        take_orders: list[Order] = []
        new_pos = position

        for ask, vol in order_depth.sell_orders.items():
            if ask < take_price and (new_pos - vol) < POSITION_LIMIT[product]:
                #new_pos += min(POSITION_LIMIT[product] - new_pos, - vol)
                new_pos += - vol
                take_orders.append(Order(product, ask, - vol))

        for bid, vol in order_depth.buy_orders.items():
            if bid > take_price and (new_pos - vol) > - POSITION_LIMIT[product]:
                #new_pos -= min(new_pos + POSITION_LIMIT[product], vol)
                new_pos -= vol
                take_orders.append(Order(product, bid, - vol))

        return take_orders, new_pos


    def market_make(self, order_depth, product, position, take_price, make_margin, make_vol):
        make_orders: list[Order] = []
        best_ask = list(order_depth.sell_orders.keys())[0]
        best_bid = list(order_depth.buy_orders.keys())[0]

        new_pos = position

        if best_ask > (take_price + make_margin) and new_pos < POSITION_LIMIT[product]:
            new_pos += min(make_vol, POSITION_LIMIT[product] - new_pos)
            make_orders.append(Order(product, int(take_price + make_margin), min(make_vol, POSITION_LIMIT[product] - new_pos)))

        if best_bid < (take_price - make_margin) and new_pos > -POSITION_LIMIT[product]:
            new_pos -= min(make_vol, new_pos + POSITION_LIMIT[product])
            make_orders.append(Order(product, int(take_price + make_margin), -min(make_vol, new_pos + POSITION_LIMIT[product])))

        return make_orders

    #def market_sell(self, order_depth, product, position, take_price, make_price, makevl_price):
    #    sell_orders: List[Order] = []
    #    new_pos = position

    #    for bid, vol in order_depth.buy_orders.items():
    #        if bid >= take_price and (new_pos - vol) > -POSITION_LIMIT[product]:
    #            new_pos -= min(new_pos + POSITION_LIMIT[product], vol)
    #            sell_orders.append(Order(product, bid, - vol))

    #    if new_pos < position_limit[product] / 2:
    #        buy_orders.append(order(product, make_price, position_limit[product] / 2 - new_pos))
    #        buy_orders.append(order(product, makevl_price, position_limit[product] / 2))

    #    if new_pos < position_limit[product]:
    #        buy_orders.append(order(product, make_price, position_limit[product] - new_pos))

        #if new_pos > - (POSITION_LIMIT[product] / 2):
        #    sell_orders.append(Order(product, make_price, - (POSITION_LIMIT[product] / 2) - new_pos))
        #    sell_orders.append(Order(product, makevl_price, - (POSITION_LIMIT[product] / 2)))

        #if new_pos > - POSITION_LIMIT[product]:
        #    sell_orders.append(Order(product, make_price, - POSITION_LIMIT[product] - new_pos))

        #return sell_orders


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
                take_price = self.calc_price_ma(data_s)
            elif product == "AMETHYSTS":
                take_price = 10000

            if len(state.position) == 0:
                prod_position = START_POSITION[product]
            else:
                prod_position = state.position[product]
        
            [take_orders, make_position] = self.market_take(order_depth, product, prod_position, take_price)

            orders += take_orders

            #make_orders = self.market_make(order_depth, product, make_position, take_price, MAKE_MARGIN[product], MAKE_VOL[product])

            #orders += make_orders

            #print("Acceptable price : " + str(acceptable_price))
            #print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
            
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1
        return result, conversions, traderData
