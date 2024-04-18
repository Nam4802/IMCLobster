

    def calc_slopeLR(self, data, LR_dur):
        time = np.arange(min(len(data), LR_dur)) # take time from 0 to N - 1 with N price in data[product]
        new_data = [data[i] for i in range(- min(len(data), LR_dur), 0)]
        slope, intercept = np.polyfit(time, new_data, 1) # take slope using statistic lib (allowed in IMC)
        return slope

    def calc_polyfit_extremum(self, data, plf_dur):
        time = np.arange(min(len(data), plf_dur))
        new_data = [data[i] for i in range(- min(len(data), plf_dur), 0)]

        coeffs = np.polyfit(time, new_data, 5)

        x_target = - 1

        for x in range(min(len(data), plf_dur), 200):

            dy_dx = coeffs[0] * 5 * x**4 + coeffs[1] * 4 * x**3 + coeffs[2] * 3 * x**2 + coeffs[3] * 2 * x + coeffs[4]

            if dy_dx < 0.1 and dy_dx > -0.1:
                x_target = x
                break

        if x_target == - 1 and coeffs[0] > 0:
            y_target = - 1          # y_target should be higher than current price
        elif x_target == -1 and coeffs[0] < 0: 
            y_target = - 2          # y_target should be lower than current price
        else:
            y_target = coeffs[0] * x_target**5 + coeffs[1] * x_target**4 + coeffs[2] * x_target**3 + coeffs[3] * x_target**2 + coeffs[4] * x_target + coeffs[5]
            
        return y_target

    def plf_bns(self, order_depth, product, position, data):
        plf_orders: list[Order] = []

        new_pos = position

        pred_price = self.calc_polyfit_extremum(data, 100)

        for ask, vol in order_depth.sell_orders.items():
            if ask > pred_price and pred_price != -1:
                new_pos += min(POSITION_LIMIT[product] - new_pos, - vol)
                plf_orders.append(Order(product, ask, min(POSITION_LIMIT[product] - new_pos, - vol)))

        for bid, vol in order_depth.buy_orders.items():
            if bid < pred_price or pred_price == -1:
                new_pos -= min(new_pos + POSITION_LIMIT[product], vol)
                plf_orders.append(Order(product, bid, - min(new_pos + POSITION_LIMIT[product], vol)))      
                
        return plf_orders, new_pos


    def market_sell(self, order_depth, product, position, take_price, make_price, makevl_price):
        sell_orders: List[Order] = []
        new_pos = position

        for bid, vol in order_depth.buy_orders.items():
            if bid >= take_price and (new_pos - vol) > -POSITION_LIMIT[product]:
                new_pos -= min(new_pos + POSITION_LIMIT[product], vol)
                sell_orders.append(Order(product, bid, - vol))

        if new_pos < position_limit[product] / 2:
            buy_orders.append(order(product, make_price, position_limit[product] / 2 - new_pos))
            buy_orders.append(order(product, makevl_price, position_limit[product] / 2))

        if new_pos < position_limit[product]:
            buy_orders.append(order(product, make_price, position_limit[product] - new_pos))

        if new_pos > - (POSITION_LIMIT[product] / 2):
            sell_orders.append(Order(product, make_price, - (POSITION_LIMIT[product] / 2) - new_pos))
            sell_orders.append(Order(product, makevl_price, - (POSITION_LIMIT[product] / 2)))

        if new_pos > - POSITION_LIMIT[product]:
            sell_orders.append(Order(product, make_price, - POSITION_LIMIT[product] - new_pos))

        return sell_orders

    def boll_bns(self, order_depth, product, position, data):
        boll_orders: list[Order] = []

        ma = self.calc_price_ma(data, 10)
        std = self.calc_price_std(data, 10)

        boll_upper = ma + 1.5 * std
        boll_lower = ma - 1.5 * std

        new_pos = position

        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if int(best_bid) > boll_upper and self.calc_slopeLR(data, 10) >= 1:
                new_pos -= best_bid_amount
                boll_orders.append(Order(product, best_bid, -best_bid_amount))

        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            if int(best_ask) < boll_lower and self.calc_slopeLR(data, 10) <= -1:
                new_pos += best_ask_amount
                boll_orders.append(Order(product, best_ask, -best_ask_amount))

        return boll_orders, new_pos

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