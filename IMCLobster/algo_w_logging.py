import json
from ssl import SSL_ERROR_WANT_X509_LOOKUP
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any

POSITION_LIMIT = {"STARFRUIT" : 20, "AMETHYSTS" : 20, "ORCHIDS": 100}
START_POSITION = {"STARFRUIT" : 0, "AMETHYSTS" : 0, "ORCHIDS": 0}
MAKE_MARGIN = {"STARFRUIT" : 2, "AMETHYSTS" : 4, "ORCHIDS": 2}
MAKE_VOL = {"STARFRUIT": 6, "AMETHYSTS": 6, "ORCHIDS": 6}

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

    data = {'STARFRUIT':[5040], 'AMETHYSTS':[10002], "ORCHIDS": [1150]}

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
                new_pos += min(POSITION_LIMIT[product] - new_pos, - vol)
                new_pos += - vol
                take_orders.append(Order(product, ask, min(POSITION_LIMIT[product] - new_pos, - vol)))

        for bid, vol in order_depth.buy_orders.items():
            if bid > take_price and (new_pos - vol) > - POSITION_LIMIT[product]:
                new_pos -= min(new_pos + POSITION_LIMIT[product], vol)
                new_pos -= vol
                take_orders.append(Order(product, bid, - min(new_pos + POSITION_LIMIT[product], vol)))

        return take_orders, new_pos


    def market_make(self, order_depth, product, position, take_price, make_margin, make_vol):
        make_orders: list[Order] = []
        best_ask = list(order_depth.sell_orders.keys())[0]
        best_bid = list(order_depth.buy_orders.keys())[0]

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
        best_ask = list(order_depth.sell_orders.keys())[0]
        best_bid = list(order_depth.buy_orders.keys())[0]

        new_pos = position

        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            if int(best_ask) < take_price:
                new_pos += best_ask_amount
                basic_orders.append(Order(product, best_ask, -best_ask_amount))
    
        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if int(best_bid) > take_price:
                new_pos -= best_ask_amount
                basic_orders.append(Order(product, best_bid, -best_bid_amount))

        return basic_orders, new_pos


    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:

        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        #print("Position: " + str(state.position))
        #print("Observations: " + str(state.observations))
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
                take_price = self.calc_price_ma(data_s)
            elif product == "AMETHYSTS":
                take_price = 10000
            elif product == "ORCHIDS":
                take_price == self.calc_price_ma(data_o)
        
            #[take_orders, make_position] = self.market_take(order_depth, product, prod_position, take_price)
            [take_orders, make_position] = self.basic_bns(order_depth, product, prod_position, take_price)

            orders += take_orders

            make_orders = self.market_make(order_depth, product, make_position, take_price, MAKE_MARGIN[product], MAKE_VOL[product])

            orders += make_orders

            #print("Acceptable price : " + str(acceptable_price))
            #print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
            
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        trader_data = ''
        conversions = 0
        logger.flush(state, result, conversions, trader_data)

        return result, conversions, trader_data

