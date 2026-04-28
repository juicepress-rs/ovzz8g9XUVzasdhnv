from datetime import datetime
from typing import Generator
from typing import List
from scrapy import Request
from scrapy.http import Response
import re
import json

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class FoscamScraperSpider(FirmwareSpider):
    name = "foscam"
    allowed_domains = ["www.foscam.com"]
    base_url = "https://www.foscam.com"
    start_urls = ["https://www.foscam.com/products.html"]

    Firmware_List_PID = []

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 10,
        "CONCURRENT_ITEMS": 10,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    xpath = {
        "categories": "//foreach[@name='category']//a[contains(text(), '\u00a0')]/@href",
        "device_class_hint": "//foreach[@name='category']//a[contains(text(), '\u00a0')]/text()",
        "firmware_product": "//div[@class='list']//p//text()",
        "firmware_table": "//div[@class='down_product_list_title']/a/@href",
        "pagination": "//div[@class='page']//ul[contains(@class, 'pagination')]/li[not(contains(@class,'next'))][last()]/a/text()",
    }

    def parse(self, response: Response, **kwargs) -> Generator[Request, None, None]:

        categories = response.xpath(self.xpath["categories"]).extract()

        raw_hints = response.xpath(self.xpath["device_class_hint"]).extract()
        device_class_hint = [self.clean_text(h) for h in raw_hints]

        device_class = self.map_device_class(device_class_hint)

        counter = 0

        yield Request(
            url="https://www.foscam.com/downloads/firmwareajaxjson.html?big_category=&count=10000&pagename=index&q=",
            callback=self.parse_api_response,
            priority=1000,
        )

        for category in categories:

            yield Request(
                url=f"https://www.foscam.com{category}?page=1&amp;per-page=9",
                callback=self.pagination,
                cb_kwargs={
                    "category": category,
                    "device_class": device_class[counter],
                },
                priority=0,
            )

            counter = counter + 1

    def pagination(self, response: Response, category: str, device_class: str) -> Generator[Request, None, None]:
        pages = response.xpath(self.xpath["pagination"]).extract()

        if pages:
            max_pages = max(pages)
        else:
            max_pages = 1
        for page in range(1, int(max_pages) + 1):

            yield Request(
                url=f"https://www.foscam.com{category}?page={page}&per-page=9",
                callback=self.parse_firmware_product,
                cb_kwargs={
                    "device_class": device_class,
                    "url": f"https://www.foscam.com{category}?page={page}&per-page=9",
                },
            )

    def parse_firmware_product(self, response: Response, device_class: str, url: str) -> Generator[Request, None, None]:
        firmware_products = response.xpath(self.xpath["firmware_product"]).extract()
        firmware_products = [self.clean_text(p) for p in firmware_products]

        yield from self.search_products_in_list(device_class, firmware_products)

    def parse_api_response(self, response: Response) -> Generator[Request, None, None]:
        try:
            data = json.loads(response.text)
        except Exception:
            return

        rows = data.get("row")

        self.Firmware_List_PID = rows

    def search_products_in_list(self, device_class: str, product_names: list[str]) -> Generator[Request, None, None]:

        for row in self.Firmware_List_PID:
            productname = row.get("productname", "").strip()
            pid = row.get("pid")

            if not pid or not productname:
                continue

            normalized_names = [n.strip().lower() for n in re.split(r"[/,\-|]", productname)]

            for name in product_names:
                if any(name.lower() in n for n in normalized_names):

                    firmware_detail_url = f"{self.base_url}/downloads/firmware_details.html?id={pid}"

                    yield Request(
                        url=firmware_detail_url,
                        callback=self.get_info,
                        cb_kwargs={
                            "device_class": device_class,
                            "name": name,
                        },
                        dont_filter=True,
                    )
                    break

    def get_info(self, response: Response, device_class: str, name: str) -> Generator[FirmwareItem, None, None]:

        rows = response.xpath("//table[contains(@class,'down_table')]//tr[not(contains(@class, 'down_table_head'))]")

        for row in rows:
            version = row.xpath("td[1]/text()").get()
            date = row.xpath("td[2]/text()").get()
            if not date:
                date = "1970-01-01"
            download_link = row.xpath("td[6]/a/@href").get()
            download_link_full = response.urljoin(download_link) if download_link else None
            device_class_clean = self.clean_text(device_class)

            meta_data = {
                "vendor": "foscam",
                "release_date": datetime.strptime(date, "%Y/%m/%d").isoformat(),
                "device_name": name,
                "firmware_version": version,
                "device_class": device_class_clean,
                "file_urls": [download_link_full] if download_link_full else [],
            }

            yield from self.item_pipeline(meta_data)

    def clean_text(self, text: str | list[str]) -> str | list[str]:
        def _clean(t: str) -> str:
            if not t:
                return ""
            t = re.sub(r"\s+", " ", t)
            t = re.sub(r"[^\w\s]", "", t)
            return t.strip()

        if isinstance(text, list):
            return [_clean(t) for t in text]
        else:
            return _clean(text)

    @staticmethod
    def map_device_class(
        device_titles: List[str],
    ) -> List[str]:
        def classify(title: str) -> str:
            title_lower = title.lower()
            if "camera" in title_lower:
                return "ipcam"
            if "video" in title_lower:
                return "ipcam"
            if "monitor" in title_lower:
                return "ip_cam"
            if "extender" in title_lower:
                return "repeater"
            if "recorder" in title_lower:
                return "recorder"
            if "system" in title_lower:
                return "ip_cam"
            if "webcam" in title_lower:
                return "ip_cam"

            return "unknown yet/irrelevant"

        return [classify(title) for title in device_titles]
