import json
import scrapy
from urllib.parse import urlencode
import requests
from datetime import datetime, timedelta
from dotenv import dotenv_values

# from scrapy_splash import SplashRequest

from reitscraper.items import ReitscraperItem, PriceHistItem


class ReitspiderSpider(scrapy.Spider):
    name = "reitspider"
    allowed_domains = ["www.set.or.th", "proxy.scrapeops.io"]
    stocks = ["siri", "ktb", "sena", "kbank", "scb", "tacc"]
    date_diff = 5
    env_vars = dotenv_values(".env")
    start_urls = [
        f"https://www.set.or.th/en/market/product/stock/quote/{stock}/factsheet"
        for stock in stocks
    ]
    current_price_urls = [
        f"https://www.set.or.th/api/set/stock/{stock.upper()}/historical-trading?lang=en"
        for stock in stocks
    ]
    price_urls = [
        f"https://www.set.or.th/api/set/stock/{stock.upper()}/chart-comparison?period=5Y"
        for stock in stocks
    ]
    div_urls = [
        f"https://www.set.or.th/api/set/stock/{stock.upper()}/corporate-action?caType=XD&lang=en"
        for stock in stocks
    ]

    referer_url = "https://www.set.or.th/en/market/product/stock/quote"

    cookie = env_vars.get("COOKIE")

    custom_settings = {
        "FEEDS": {"dividend_data.csv": {"format": "csv", "overwrite": True}},
        # "FEEDS": {"win_data.csv": {"format": "csv", "overwrite": True}},
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls.pop(0),
            callback=self.parse,
        )

    def parse(self, response):

        yield scrapy.Request(
            url=self.current_price_urls.pop(0),
            callback=self.parse_current_price,
            headers={
                "Cookie": self.cookie,
                "Referer": self.referer_url,
            },
        )

    def parse_current_price(self, response):
        current_price_data = response.json()
        current_price = current_price_data[0].get("open")

        yield scrapy.Request(
            url=self.price_urls.pop(0),
            callback=self.parse_price_data,
            headers={
                "Cookie": self.cookie,
                "Referer": self.referer_url,
            },
            meta={"current_price": current_price},
        )

    def parse_price_data(self, response):
        price_data = response.json()
        current_price = response.meta["current_price"]

        quos = price_data.get("quotations")
        history_start_price = current_price / (1 + quos[-1].get("stock") / 100)
        price_hist = {
            quo.get("localDatetime"): history_start_price * (1 + quo.get("stock") / 100)
            for quo in quos
        }

        yield scrapy.Request(
            url=self.div_urls.pop(0),
            callback=self.parse_dividend,
            headers={
                "Cookie": self.cookie,
                "Referer": self.referer_url,
            },
            meta={"price_hist": price_hist, "current_price": current_price},
        )

    def parse_dividend(self, response):
        reit_item = ReitscraperItem()
        price_item = PriceHistItem()
        div_data = response.json()
        price_hist = response.meta["price_hist"]
        current_price = response.meta["current_price"]

        for div in div_data:
            price_now = price_hist.get(div.get("xdate").split("+")[0])
            div_fu = False if price_now else True
            price_now = price_now if price_now else current_price

            xdate_str = div.get("xdate").split("+")[0]
            xdate_obj = datetime.fromisoformat(xdate_str)
            date_range = [xdate_obj + timedelta(days=i) for i in range(-10, 6)]
            date_range_str = [date.isoformat() for date in date_range]
            prices = {date: price_hist.get(date) for date in date_range_str}

            prev_date = xdate_obj
            for _ in range(self.date_diff):
                prev_date -= timedelta(days=1)
                while prev_date.isoformat() not in price_hist:
                    prev_date -= timedelta(days=1)

            prev_price = price_hist[prev_date.isoformat()]

            # Calculate the percentage difference
            per_price_diff = (
                ((price_now - prev_price) / prev_price) * 100 if not div_fu else 0
            )

            per_yield = div.get("dividend") / price_now * 100

            per_gain = per_yield + per_price_diff

            reit_item["stock"] = div.get("symbol")
            reit_item["price"] = round(price_now, 2)
            reit_item["per_price_diff"] = (
                round(per_price_diff, 2) if per_price_diff else None
            )
            reit_item["div_yield"] = div.get("dividend")
            reit_item["per_div_yield"] = round(per_yield, 2)
            reit_item["per_gain"] = round(per_gain, 2)
            reit_item["payment_date"] = div.get("paymentDate")
            reit_item["x_date"] = div.get("xdate")
            reit_item["operation_period"] = [
                div.get("beginOperation"),
                div.get("endOperation"),
            ]
            reit_item["type"] = div.get("dividendType")
            # reit_item["win_dates"] = list(price_hist.keys())
            # reit_item["win_prices"] = list(price_hist.values())

            yield reit_item

        if self.start_urls:
            yield scrapy.Request(
                url=self.start_urls.pop(0),
                callback=self.parse,
                headers={
                    "Cookie": self.cookie,
                    "Referer": self.referer_url,
                },
            )
