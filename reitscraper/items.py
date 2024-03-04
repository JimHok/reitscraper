# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ReitscraperItem(scrapy.Item):
    stock = scrapy.Field()
    price = scrapy.Field()
    per_price_diff = scrapy.Field()
    div_yield = scrapy.Field()
    per_div_yield = scrapy.Field()
    per_gain = scrapy.Field()
    payment_date = scrapy.Field()
    x_date = scrapy.Field()
    operation_period = scrapy.Field()
    type = scrapy.Field()
    # win_dates = scrapy.Field()
    # win_prices = scrapy.Field()


class PriceHistItem(scrapy.Item):
    date = scrapy.Field()
    price = scrapy.Field()
