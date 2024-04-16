from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import string

POSITION_LIMIT = {"STARFRUIT" : 20, "AMETHYSTS" : 20, "ORCHIDS": 100}
START_POSITION = {"STARFRUIT" : 0, "AMETHYSTS" : 0, "ORCHIDS": 0}
MAKE_MARGIN = {"STARFRUIT" : 2, "AMETHYSTS" : 4, "ORCHIDS": 2}
MAKE_VOL = {"STARFRUIT": 6, "AMETHYSTS": 6, "ORCHIDS": 6}

class Trader:

    data = {'STARFRUIT':[5040], 'AMETHYSTS':[10002], 'ORCHIDS': [1200]}

    # Function to just print a dict containing current mid price of all products
    def mid_price(self, order_depth):

        mid_price_all = {}

        for product in order_depth:
            mid_price = (list(order_depth[product].sell_orders.keys())[0] + list(order_depth[product].buy_orders.keys())[0]) / 2
            #print(product + " current mid price : " + str(mid_price))

            mid_price_all[product] = mid_price

        return mid_price_all

    # Update data
    def update_data(self, order_depth):
        for product in order_depth:
            mid_price = (list(order_depth[product].sell_orders.keys())[0] + list(order_depth[product].buy_orders.keys())[0]) / 2
            print('Mid-price ' + product + ': ' + str(mid_price))
            Trader.data[product].append(mid_price)

    # Calculate moving average
    def calc_price_ma(self, data, ma_dur):

        mavg = 0

        for i in range(min(len(data), ma_dur)):
            mavg += data[-1 - i] / ma_dur

        return mavg

    def market_take(self, order_depth, product, position, take_price):
        take_orders: list[Order] = []
        new_pos = position

        for ask, vol in order_depth.sell_orders.items():
            if ask < take_price:
                new_pos += min(POSITION_LIMIT[product] - new_pos, - vol)
                take_orders.append(Order(product, ask, min(POSITION_LIMIT[product] - new_pos, - vol)))

        for bid, vol in order_depth.buy_orders.items():
            if bid > take_price:
                new_pos -= min(new_pos + POSITION_LIMIT[product], vol)
                take_orders.append(Order(product, bid, - min(new_pos + POSITION_LIMIT[product], vol)))

        return take_orders, new_pos


    def market_make(self, order_depth, product, position, take_price, make_margin, make_vol):
        make_orders: list[Order] = []
        #best_ask = list(order_depth.sell_orders.keys())[0]
        #best_bid = list(order_depth.buy_orders.keys())[0]

        new_pos = position

        #if best_ask > (take_price + make_margin) and new_pos < POSITION_LIMIT[product]:
        #    new_pos += min(make_vol, POSITION_LIMIT[product] - new_pos)
        #    make_orders.append(Order(product, take_price - make_margin, min(make_vol, POSITION_LIMIT[product] - new_pos)))

        #if best_bid < (take_price - make_margin) and new_pos > -POSITION_LIMIT[product]:
        #    new_pos -= min(make_vol, new_pos + POSITION_LIMIT[product])
        #    make_orders.append(Order(product, take_price + make_margin, -min(make_vol, new_pos + POSITION_LIMIT[product])))

        if new_pos < POSITION_LIMIT[product]:
            new_pos += min(make_vol, POSITION_LIMIT[product] - new_pos)
            make_orders.append(Order(product, int(take_price - make_margin), min(make_vol, POSITION_LIMIT[product] - new_pos)))

        if new_pos > -POSITION_LIMIT[product]:
            new_pos -= min(make_vol, new_pos + POSITION_LIMIT[product])
            make_orders.append(Order(product, int(take_price + make_margin), -min(make_vol, new_pos + POSITION_LIMIT[product])))

        return make_orders

    def basic_bns(self, order_depth, product, position, take_price):
        basic_orders: list[Order] = []

        new_pos = position

        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if int(best_bid) > take_price:
                new_pos -= best_bid_amount
                basic_orders.append(Order(product, best_bid, -best_bid_amount))

        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            if int(best_ask) < take_price:
                new_pos += best_ask_amount
                basic_orders.append(Order(product, best_ask, -best_ask_amount))

        return basic_orders, new_pos

    def orchid_conversion(self, order_depth, product, position, take_price, observation):
        basic_orders: list[Order] = []
        best_ask = list(order_depth.sell_orders.keys())[0]
        best_bid = list(order_depth.buy_orders.keys())[0]
        best_ask_duck = observation.conversionObservations[product].askPrice
        best_bid_duck = observation.conversionObservations[product].bidPrice

        new_pos = position
        import_tar = observation.conversionObservations[product].importTariff
        export_tar = observation.conversionObservations[product].exportTariff
        tp_fee = observation.conversionObservations[product].transportFees

        conv = 0

        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            if best_ask < (best_bid_duck - export_tar - tp_fee / ( - best_ask_amount)) and (new_pos + best_ask_amount) >= - POSITION_LIMIT[product]:
                conv += best_ask_amount
                basic_orders.append(Order(product, best_ask, - best_ask_amount))

            #elif best_ask < take_price:
            #    new_pos -= best_ask_amount
            #    basic_orders.append(Order(product, best_ask, -best_ask_amount))
    
        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if best_bid > (best_ask_duck + import_tar + tp_fee / best_bid_amount) and (new_pos + best_bid_amount) <= POSITION_LIMIT[product]:
                conv += best_bid_amount
                basic_orders.append(Order(product, best_bid, - best_bid_amount))

        return basic_orders, new_pos, conv
            


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
        print("Observations: " + str(state.observations))
        data_s = Trader.data['STARFRUIT']
        data_a = Trader.data['AMETHYSTS']
        data_o = Trader.data['ORCHIDS']
        #print("Last prices: STARFRUIT: " + str(data_s[-1]) + ", AMETHYSTS: " + str(data_a[-1]))

        result = {}

        self.mid_price(state.order_depths)
        self.update_data(state.order_depths)

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            if product not in state.position.keys():
                prod_position = START_POSITION[product]
            else:
                prod_position = state.position[product]

            if product == "STARFRUIT":
                take_price = self.calc_price_ma(data_s, 5)
            elif product == "AMETHYSTS":
                take_price = 10000
            elif product == "ORCHIDS":
                take_price == self.calc_price_ma(data_o, 200)
        
            if product == "ORCHIDS" and len(state.observations.conversionObservations) != 0:
                [take_orders, make_position, conv] = self.orchid_conversion(order_depth, product, prod_position, take_price, state.observations)
            else:
                [take_orders, make_position] = self.basic_bns(order_depth, product, prod_position, take_price)
                conv = 0
            
            orders += take_orders

            if product != "ORCHIDS":
                make_orders = self.market_make(order_depth, product, make_position, take_price, MAKE_MARGIN[product], MAKE_VOL[product])

                orders += make_orders

            #print("Acceptable price : " + str(acceptable_price))
            #print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
            
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = conv
        return result, conversions, traderData
