from datamodel import OrderDepth
from typing import List, Dict

order_depth = OrderDepth()
order_depth.buy_orders = {10: 7, 9: 5}
order_depth.sell_orders = {12: -5, 13: -3}

current_price = list(order_depth.sell_orders.keys())

print("abc" + str(current_price))

print(order_depth.buy_orders[10][-1])
