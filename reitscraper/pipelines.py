# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from dateutil import parser


class ReitscraperPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Strip whitespace from fields that is not description
        field_names = adapter.field_names()

        for field_name in field_names:

            # if field_name == "percent_yield":
            #     value = adapter.get(field_name)
            #     adapter[field_name] = str(value) + "%"

            if field_name == "payment_date":
                value = adapter.get(field_name)
                if value:
                    adapter[field_name] = parser.parse(value).strftime("%d %b %Y")
                else:
                    adapter[field_name] = "-"

            if field_name == "x_date":
                value = adapter.get(field_name)
                adapter[field_name] = parser.parse(value).strftime("%d %b %Y")

            if field_name == "operation_period":
                value = adapter.get(field_name)
                if value[0]:
                    date_beg = parser.parse(value[0]).strftime("%d %b %Y")
                    date_end = parser.parse(value[1]).strftime("%d %b %Y")
                    adapter[field_name] = f"{date_beg} - {date_end}"
                else:
                    adapter[field_name] = "-"

            # if field_name == "win_dates":
            #     value = adapter.get(field_name)
            #     adapter[field_name] = [
            #         parser.parse(date).strftime("%d %b %Y") for date in value
            #     ]

            # if field_name == "win_price":
            #     value = adapter.get(field_name)
            #     adapter[field_name] = [
            #         (round(price, 2) if price else None) for price in value
            #     ]

        return item
