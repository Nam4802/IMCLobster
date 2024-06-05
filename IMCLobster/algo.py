import json
from ssl import SSL_ERROR_WANT_X509_LOOKUP
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any
import numpy as np

POSITION_LIMIT = {"STARFRUIT" : 20, "AMETHYSTS" : 20, "ORCHIDS": 100, "CHOCOLATE": 250, "STRAWBERRIES": 350, "ROSES": 60, "GIFT_BASKET": 60, "COCONUT": 300, "COCONUT_COUPON": 600}
START_POSITION = {"STARFRUIT" : 0, "AMETHYSTS" : 0, "ORCHIDS": 0, "CHOCOLATE": 0, "STRAWBERRIES": 0, "ROSES": 0, "GIFT_BASKET": 0, "COCONUT": 0, "COCONUT_COUPON": 0}
MAKE_MARGIN = {"STARFRUIT" : 2, "AMETHYSTS" : 4}
MAKE_VOL = {"STARFRUIT": 6, "AMETHYSTS": 6}

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(self.to_json([
            self.compress_state(state, ""),
            self.compress_orders(orders),
            conversions,
            "",
            "",
        ]))

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders),
            conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing["symbol"], listing["product"], listing["denomination"]])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append([
                    trade.symbol,
                    trade.price,
                    trade.quantity,
                    trade.buyer,
                    trade.seller,
                    trade.timestamp,
                ])

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sunlight,
                observation.humidity,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value

        return value[:max_length - 3] + "..."

logger = Logger()

class Trader:

    data = {"STARFRUIT":[], "AMETHYSTS":[], "ORCHIDS": [], "CHOCOLATE": [], "STRAWBERRIES": [], "ROSES": [], "GIFT_BASKET": [], "GIFT_ITEMS": [], "COCONUT": [], "COCONUT_COUPON": []}

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

        mid_price_gift_item = 4 * Trader.data["CHOCOLATE"][-1] + 6 * Trader.data["STRAWBERRIES"][-1] + Trader.data["ROSES"][-1]
        Trader.data["GIFT_ITEMS"].append(mid_price_gift_item)

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

    def boll_score(self, data, ma_dur, std_dur):

        ma = self.calc_price_std(data, ma_dur)
        std = self.calc_price_std(data, std_dur)

        score = (data[-1] - ma) / std

        return score

    def calc_plf_pred(self, data, plf_dur, pred_dur):
        time = np.arange(min(len(data), plf_dur))
        new_data = [data[i] for i in range(- min(len(data), plf_dur), 0)]

        #coeffs = np.polyfit(time, new_data, 5)

        #x_target = min(len(data), plf_dur) + pred_dur

        #y_target = coeffs[0] * x_target**5 + coeffs[1] * x_target**4 + coeffs[2] * x_target**3 + coeffs[3] * x_target**2 + coeffs[4] * x_target + coeffs[5]
        
        coeffs = np.polyfit(time, new_data, 3)

        x_target = min(len(data), plf_dur) + pred_dur

        y_target = coeffs[0] * x_target**3 + coeffs[1] * x_target**2 + coeffs[2] * x_target + coeffs[3]

        return y_target

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


    def basic_bns(self, order_depth, product, position, take_price, action = "BOTH"):
        basic_orders: list[Order] = []

        new_pos = position

        if action == "BUY":
            take_price = 99999999
        if action == "SELL":
            take_price = 0

        if len(order_depth.buy_orders) != 0 and action != "BUY":
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if int(best_bid) > take_price:
                
                basic_orders.append(Order(product, best_bid, - min(new_pos + POSITION_LIMIT[product], best_bid_amount)))
                #new_pos -= best_bid_amount
                new_pos -= min(new_pos + POSITION_LIMIT[product], best_bid_amount)
                

        if len(order_depth.sell_orders) != 0 and action != "SELL":
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            if int(best_ask) < take_price:
                
                basic_orders.append(Order(product, best_ask, min(POSITION_LIMIT[product] - new_pos, - best_ask_amount)))
                #new_pos += best_ask_amount
                new_pos += min(POSITION_LIMIT[product] - new_pos, - best_ask_amount)
                

        return basic_orders, new_pos

    def orchid_conversion(self, order_depth, product, position, observation):
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
        gift_orders = {"CHOCOLATE": [], "STRAWBERRIES": [], "ROSES": [], "GIFT_BASKET": []}
        choco_ord = all_order_depths["CHOCOLATE"]
        strb_ord = all_order_depths["STRAWBERRIES"]
        rose_ord = all_order_depths["ROSES"]
        gift_ord = all_order_depths["GIFT_BASKET"]

        new_pos = position

        #gift_check = self.boll_score(Trader.data["GIFT_BASKET"], 10, 10) - self.boll_score(Trader.data["GIFT_ITEMS"], 10, 10)
        gift_check = Trader.data["GIFT_BASKET"][-1] / Trader.data["GIFT_ITEMS"][-1]
        #print(gift_check)

        ratio_u = (self.calc_price_ma(Trader.data["GIFT_BASKET"], 250) + self.calc_price_std(Trader.data["GIFT_BASKET"], 150)) / self.calc_price_ma(Trader.data["GIFT_ITEMS"], 250)
        ratio_l = (self.calc_price_ma(Trader.data["GIFT_BASKET"], 250) - self.calc_price_std(Trader.data["GIFT_BASKET"], 150)) / self.calc_price_ma(Trader.data["GIFT_ITEMS"], 250)
        #ratio = 0
        #for i in range(- 10, 0):
        #    ratio += (Trader.data["GIFT_BASKET"][i] / Trader.data["GIFT_ITEMS"][i]) / 10

        #ratio = 1.0059

        if gift_check > ratio_u:
            best_bid_gift, best_bid_vol_gift = list(gift_ord.buy_orders.items())[0]
            best_ask_choco, best_ask_vol_choco = list(choco_ord.sell_orders.items())[0]
            best_ask_strb, best_ask_vol_strb = list(strb_ord.sell_orders.items())[0]
            best_ask_rose, best_ask_vol_rose = list(rose_ord.sell_orders.items())[0]

            lim_vol = min(best_bid_vol_gift, round(- best_ask_vol_choco / 4), round(- best_ask_vol_strb / 6), - best_ask_vol_rose, POSITION_LIMIT["GIFT_BASKET"] + new_pos)

            gift_orders["GIFT_BASKET"].append(Order("GIFT_BASKET", best_bid_gift, - lim_vol))
            gift_orders["CHOCOLATE"].append(Order("CHOCOLATE", best_ask_choco, 4 * lim_vol))
            gift_orders["STRAWBERRIES"].append(Order("STRAWBERRIES", best_ask_strb, 6 * lim_vol))
            gift_orders["ROSES"].append(Order("ROSES", best_ask_rose, lim_vol))
            
            new_pos -= lim_vol

        if gift_check < ratio_l:
            best_ask_gift, best_ask_vol_gift = list(gift_ord.sell_orders.items())[0]
            best_bid_choco, best_bid_vol_choco = list(choco_ord.buy_orders.items())[0]
            best_bid_strb, best_bid_vol_strb = list(strb_ord.buy_orders.items())[0]
            best_bid_rose, best_bid_vol_rose = list(rose_ord.buy_orders.items())[0]

            lim_vol = min(- best_ask_vol_gift, round(best_bid_vol_choco / 4), round(best_bid_vol_strb / 6), best_bid_vol_rose, POSITION_LIMIT["GIFT_BASKET"] - new_pos)

            gift_orders["GIFT_BASKET"].append(Order("GIFT_BASKET", best_ask_gift, lim_vol))
            gift_orders["CHOCOLATE"].append(Order("CHOCOLATE", best_bid_choco, - 4 * lim_vol))
            gift_orders["STRAWBERRIES"].append(Order("STRAWBERRIES", best_bid_strb, - 6 * lim_vol))
            gift_orders["ROSES"].append(Order("ROSES", best_bid_rose, - lim_vol))

            new_pos += lim_vol

        return gift_orders, new_pos

    def calc_coco(self, all_order_depths, position):
        coco_orders = {"COCONUT": [], "COCONUT_COUPON": []}
        coup_ord = all_order_depths["COCONUT_COUPON"]
        coco_ord = all_order_depths["COCONUT"]

        coup_price = Trader.data["COCONUT_COUPON"][-1]
        coco_price = Trader.data["COCONUT"][-1]

        new_pos = position

        pnl_check = (self.calc_plf_pred(Trader.data["COCONUT"], 250, 250) - 10000) - (coup_price - coco_price)
        coco_check = coco_price - self.calc_plf_pred(Trader.data["COCONUT"], 250, 250)

        if pnl_check > 0 and coco_check > 0:
            best_ask_coup, best_ask_vol_coup = list(coup_ord.sell_orders.items())[0]
            best_bid_coco, best_bid_vol_coco = list(coco_ord.buy_orders.items())[0]
            lim_vol = min(- best_ask_vol_coup, best_bid_vol_coco, POSITION_LIMIT["COCONUT_COUPON"] - new_pos)
            coco_orders["COCONUT_COUPON"].append(Order("COCONUT_COUPON", best_ask_coup, lim_vol))
            coco_orders["COCONUT"].append(Order("COCONUT", best_bid_coco, - lim_vol))
        if pnl_check > 0 and coco_check < 0:
            best_ask_coup, best_ask_vol_coup = list(coup_ord.sell_orders.items())[0]
            best_ask_coco, best_ask_vol_coco = list(coco_ord.sell_orders.items())[0]
            lim_vol = min(- best_ask_vol_coup, - best_ask_vol_coco, POSITION_LIMIT["COCONUT_COUPON"] - new_pos)
            coco_orders["COCONUT_COUPON"].append(Order("COCONUT_COUPON", best_ask_coup, lim_vol))
            coco_orders["COCONUT"].append(Order("COCONUT", best_ask_coco, lim_vol))
        if pnl_check < 0 and coco_check < 0:
            best_bid_coup, best_bid_vol_coup = list(coco_ord.buy_orders.items())[0]
            best_ask_coco, best_ask_vol_coco = list(coco_ord.sell_orders.items())[0]
            lim_vol = min(- best_ask_vol_coco, best_bid_vol_coup, POSITION_LIMIT["COCONUT_COUPON"] + new_pos)
            coco_orders["COCONUT_COUPON"].append(Order("COCONUT_COUPON", best_bid_coup, - lim_vol))
            coco_orders["COCONUT"].append(Order("COCONUT", best_ask_coco, lim_vol))
        if pnl_check < 0 and coco_check > 0:
            best_bid_coup, best_bid_vol_coup = list(coco_ord.buy_orders.items())[0]
            best_bid_coco, best_bid_vol_coco = list(coco_ord.buy_orders.items())[0]
            lim_vol = min(best_bid_vol_coco, best_bid_vol_coup, POSITION_LIMIT["COCONUT_COUPON"] + new_pos)
            coco_orders["COCONUT_COUPON"].append(Order("COCONUT_COUPON", best_bid_coup, - lim_vol))
            coco_orders["COCONUT"].append(Order("COCONUT", best_bid_coco, - lim_vol))
        return coco_orders, new_pos


    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:


        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        #print("Position: " + str(state.position))
        #print("Observations: " + str(state.observations))

        self.update_data(state.order_depths)

        result = {}
        conversions = 0

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
        
            if product == "ORCHIDS" and len(state.observations.conversionObservations) != 0:
                [take_orders, make_position, conv] = self.orchid_conversion(order_depth, product, prod_position, state.observations)
                orders += take_orders
                conversions = conv
                result[product] = orders
            if product == "GIFT_BASKET" and state.timestamp >= 1000:
                [gift_orders, gift_position] = self.calc_gift(state.order_depths, prod_position)
                #result[product] = gift_orders[product]
                for items in gift_orders.keys():
                    result[items] = gift_orders[items]
            if product == "COCONUT_COUPON" and state.timestamp >= 1000:
                [coco_orders, gift_position] = self.calc_coco(state.order_depths, prod_position)
                for items in coco_orders.keys():
                    result[items] = coco_orders[items]
            if product in ["STARFRUIT", "AMETHYSTS"]:
                [take_orders, make_position] = self.basic_bns(order_depth, product, prod_position, take_price)
                make_orders = self.market_make(order_depth, product, prod_position, take_price, MAKE_MARGIN[product], MAKE_VOL[product])
                orders += take_orders
                orders += make_orders
                result[product] = orders
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        trader_data = ''
        logger.flush(state, result, conversions, trader_data)

        return result, conversions, trader_data
