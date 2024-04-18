from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import string
import numpy as np

POSITION_LIMIT = {"STARFRUIT" : 20, "AMETHYSTS" : 20, "ORCHIDS": 100, "CHOCOLATE": 250, "STRAWBERRIES": 350, "ROSES": 60, "GIFT_BASKET": 60}
START_POSITION = {"STARFRUIT" : 0, "AMETHYSTS" : 0, "ORCHIDS": 0, "CHOCOLATE": 0, "STRAWBERRIES": 0, "ROSES": 0, "GIFT_BASKET": 0}
MAKE_MARGIN = {"STARFRUIT" : 2, "AMETHYSTS" : 4}
MAKE_VOL = {"STARFRUIT": 6, "AMETHYSTS": 6}

class Trader:

    data = {"STARFRUIT":[], "AMETHYSTS":[], "ORCHIDS": [], "CHOCOLATE": [], "STRAWBERRIES": [], "ROSES": [], "GIFT_BASKET": []}

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
            Trader.data[product].append(mid_price)

    # Calculate moving average
    def calc_price_ma(self, data, ma_dur):

        mavg = 0

        for i in range(min(len(data), ma_dur)):
            mavg += data[-1 - i] / ma_dur

        return mavg

    # Calculate standard deviation
    def calc_price_std(self, data, std_dur):

        std = np.std([data[i] for i in range(- min(len(data), std_dur), 0)])

        return std

    def market_make(self, order_depth, product, position, take_price, make_margin, make_vol):
        make_orders: list[Order] = []

        new_pos = position

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
                
                basic_orders.append(Order(product, best_bid, - min(new_pos + POSITION_LIMIT[product], best_bid_amount)))
                #new_pos -= best_bid_amount
                new_pos -= min(new_pos + POSITION_LIMIT[product], best_bid_amount)
                

        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            if int(best_ask) < take_price:
                
                basic_orders.append(Order(product, best_ask, min(POSITION_LIMIT[product] - new_pos, - best_ask_amount)))
                #new_pos += best_ask_amount
                new_pos += min(POSITION_LIMIT[product] - new_pos, - best_ask_amount)
                

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
    
        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if best_bid > (best_ask_duck + import_tar + tp_fee / best_bid_amount) and (new_pos + best_bid_amount) <= POSITION_LIMIT[product]:
                conv += best_bid_amount
                basic_orders.append(Order(product, best_bid, - best_bid_amount))

        return basic_orders, new_pos, conv

    def calc_gift(self, all_order_depths, position):
        gift_orders: list[Order] = []
        choco_ord = all_order_depths["CHOCOLATE"]
        strb_ord = all_order_depths["STRAWBERRIES"]
        rose_ord = all_order_depths["ROSES"]
        gift_ord = all_order_depths["GIFT_BASKET"]

        new_pos = position

        sell_gift_check = list(gift_ord.buy_orders.keys())[0] - 4 * list(choco_ord.sell_orders.keys())[0] - 6 * list(strb_ord.sell_orders.keys())[0] - list(rose_ord.sell_orders.keys())[0]

        buy_gift_check = - (list(gift_ord.sell_orders.keys())[0] - 4 * list(choco_ord.buy_orders.keys())[0] - 6 * list(strb_ord.buy_orders.keys())[0] - list(rose_ord.buy_orders.keys())[0])

        if sell_gift_check > 0 and len(gift_ord.buy_orders) != 0:
            best_bid, best_bid_amount = list(gift_ord.buy_orders.items())[0]

            sell_vol = min(new_pos + POSITION_LIMIT["GIFT_BASKET"], best_bid_amount)

            gift_orders.append(Order("GIFT_BASKET", best_bid, - sell_vol))
            gift_orders.append(Order("CHOCOLATE", list(choco_ord.sell_orders.keys())[0], 4 * sell_vol))
            gift_orders.append(Order("STRAWBERRIES", list(strb_ord.sell_orders.keys())[0], 6 * sell_vol))
            gift_orders.append(Order("ROSES", list(rose_ord.sell_orders.keys())[0], sell_vol))
            
            new_pos -= sell_vol

        if buy_gift_check > 0 and len(gift_ord.sell_orders) != 0:
            best_ask, best_ask_amount = list(gift_ord.sell_orders.items())[0]

            buy_vol = min(POSITION_LIMIT["GIFT_BASKET"] - new_pos, - best_ask_amount)

            gift_orders.append(Order("GIFT_BASKET", best_ask, buy_vol))
            gift_orders.append(Order("CHOCOLATE", list(choco_ord.buy_orders.keys())[0], - 4 * buy_vol))
            gift_orders.append(Order("STRAWBERRIES", list(strb_ord.buy_orders.keys())[0], - 6 * buy_vol))
            gift_orders.append(Order("ROSES", list(rose_ord.buy_orders.keys())[0], - buy_vol))

            new_pos += buy_vol

        return gift_orders, new_pos

    def run(self, state: TradingState):

        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("Position: " + str(state.position))
        print("Observations: " + str(state.observations))

        self.update_data(state.order_depths)

        result = {}

        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            if product not in state.position.keys():
                prod_position = START_POSITION[product]
            else:
                prod_position = state.position[product]

            if product == "AMETHYSTS":
                take_price = 10000
            elif product == "STARFRUIT":
                take_price = self.calc_price_ma(Trader.data[product], 5)
            elif product == "STRAWBERRIES":
                take_price = self.calc_price_ma(Trader.data[product], 100)
            elif product == "ORCHIDS": 
                take_price = self.calc_price_ma(Trader.data[product], 200)
            else:
                take_price = self.calc_price_ma(Trader.data[product], 250)

                conv = 0
        
            if product == "ORCHIDS" and len(state.observations.conversionObservations) != 0:
                [take_orders, make_position, conv] = self.orchid_conversion(order_depth, product, prod_position, take_price, state.observations)
                orders += take_orders
            #elif product == "GIFT_BASKET":
            #    [gift_orders, take_position] = self.calc_gift(state.order_depths, prod_position)
            #    [take_orders, make_position] = self.basic_bns(order_depth, product, take_position, take_price)
            #    orders += gift_orders
            #    orders += take_orders
                
            elif product in ["STARFRUIT", "AMETHYSTS"]:
                [take_orders, make_position] = self.basic_bns(order_depth, product, prod_position, take_price)
                make_orders = self.market_make(order_depth, product, prod_position, take_price, MAKE_MARGIN[product], MAKE_VOL[product])
                orders += take_orders
                orders += make_orders
            else:
                [take_orders, make_position] = self.basic_bns(order_depth, product, prod_position, take_price)
                orders += take_orders
    
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.

        conversions = conv
        return result, conversions, traderData
