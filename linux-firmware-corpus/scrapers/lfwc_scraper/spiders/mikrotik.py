import scrapy

from datetime import datetime
from typing import Generator
from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class MikrotikSpider(FirmwareSpider):

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 10,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    name = "mikrotik"
    allowed_domains = ["mikrotik.com"]
    start_urls = ["https://mikrotik.com/products/"]
    base_url = "https://mikrotik.com"
    firmware_counter = 0

    def parse(self, response: Response, **kwargs) -> Generator[Request, None, None]:
        categories_link = response.xpath(
            "//div[@id='sidebar']/ul[@class='categories hide-for-small']//a/@href"
        ).extract()

        categories_link = categories_link[2:]
        filtered_categories_links = [x for x in categories_link if "product" in x]

        categories = []
        for link in filtered_categories_links:
            cat = link.rsplit("/", 1)[-1]
            categories.append(cat)

        for c in range(0, len(filtered_categories_links)):
            yield Request(
                url=f"{self.base_url}{filtered_categories_links[c]}",
                callback=self.get_products,
                cb_kwargs={"category": categories[c]},
            )

    def get_products(self, response: Response, category: str) -> Generator[Request, None, None]:
        product_links = response.xpath("//div[@class='medium-9 columns productlist']//h2/a/@href").extract()

        for product in product_links:
            name = product.rsplit("/", 1)[-1]
            yield Request(
                url=f"{self.base_url}{product}#fndtn-downloads",
                callback=self.parse_download_page,
                cb_kwargs={"product_name": name, "product_category": category},
            )

    def parse_download_page(
        self, response: Response, product_category: str, product_name: str
    ) -> Generator[FirmwareItem, None, None]:

        download_links = response.xpath("//div[@id='downloads']//a[contains(text(), 'Download')]/@href").extract()

        if download_links and any("download" in link.lower() for link in download_links):
            for link in download_links:
                if "download" in link.lower():
                    mapped_category = self.map_device_class(product_category)
                    assert mapped_category != "unknown"

                    version = link.split("/")[-2]

                    meta_data = {
                        "vendor": "mikrotik",
                        "release_date": datetime.strptime("1970-01-01", "%Y-%m-%d").isoformat(),
                        "device_name": product_name,
                        "firmware_version": version,
                        "device_class": mapped_category,
                        "file_urls": [link],
                    }
                    yield from self.item_pipeline(meta_data)

    @staticmethod
    def map_device_class(device_title: str) -> str:
        title = device_title.lower()

        if "router" in title:
            return "router"
        if "switches" in title:
            return "switch"
        if "wireless" in title or "ghz" in title:
            return "accesspoint"
        if "lte" in title or "iot" in title:
            return "gateway"
        if "enclosures" in title:
            return "power_supply"
        if "accessories" in title or "antennas" in title:
            return "unknown"
        if "interfaces" in title:
            return "converter"
        if "sfp" in title:
            return "converter"

        return "unknown"
