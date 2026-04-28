import scrapy
from datetime import datetime
from typing import Generator
from typing import List
from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class Totolink(FirmwareSpider):
    name = "totolink"
    allowed_domains = ["www.totolink.net"]
    start_urls = ["https://www.totolink.net/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 10,
        "CONCURRENT_ITEMS": 10,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    base_url = "https://www.totolink.net"

    xpath = {
        "product_page": "//h4/parent::a/@href",
        "device_class_hint": "//h4/text()",
        "download_page": "//h3/child::a/@href",
        "date": "normalize-space(td[@class='name']/following-sibling::td[2]//text())",
        "version": "td[@class='name']/following-sibling::td[1]/text()",
        "download_link": "td[@class='name']/following-sibling::td[3]//a[@class ='download_a']/@href",
        "dis_mod_link": "//li[@class='two-li']/child::a/@href",
        "dis_mod_class": "//li[@class='two-li']/child::a//text()",
        "next_page_dis_mod": "//ul[@class='pagination']/li//@href[not(. = preceding::li//@href)]",
    }

    def parse(self, response: Response, **kwargs) -> Generator[Request, None, None]:
        product_pages = response.xpath(self.xpath["product_page"]).extract()
        device_class_hint = response.xpath(self.xpath["device_class_hint"]).getall()
        device_class = self.map_device_class(device_class_hint)

        counter = 0

        for link in product_pages:
            if (
                link == "/home/menu/menu/menu_listtpl/prod/id/151.html"
            ):  # workaround for the section "discontinued model"
                yield Request(url=f"{self.base_url}{link}", callback=self.discontinued_model)
                continue
            yield Request(
                url=f"{self.base_url}{link}",
                callback=self.parse_download_page,
                cb_kwargs={
                    "device_class": device_class[counter],
                },
            )

            counter = counter + 1

    def discontinued_model(self, response: Response, **kwargs) -> Generator[Request, None, None]:
        product_pages = response.xpath(self.xpath["dis_mod_link"]).extract()
        product_classes = response.xpath(self.xpath["dis_mod_class"]).extract()
        device_class = self.map_device_class(product_classes)

        counter = 0

        for link in product_pages:
            yield Request(
                url=f"{self.base_url}{link}",
                callback=self.more_pages,
                cb_kwargs={
                    "device_class": device_class[counter],
                    "original_url": f"{self.base_url}{link}",
                },
            )
            counter = counter + 1

    def more_pages(self, response: Response, device_class: str, original_url: str) -> Generator[Request, None, None]:

        pages = response.xpath(self.xpath["next_page_dis_mod"]).extract()
        pages = [f"{self.base_url}{page}" for page in pages]

        yield Request(
            url=f"{original_url}",
            callback=self.parse_download_page,
            cb_kwargs={"device_class": device_class},
        )
        for page in pages:
            yield Request(
                url=f"{page}",
                callback=self.parse_download_page,
                cb_kwargs={"device_class": device_class},
            )

    def parse_download_page(self, response: Response, device_class: str) -> Generator[Request, None, None]:

        not_really_download_pages = response.xpath(self.xpath["download_page"]).extract()

        download_pages = self.replace_keywords(not_really_download_pages)

        for link in download_pages:

            yield Request(
                url=f"{self.base_url}{link}",
                callback=self.get_info,
                cb_kwargs={
                    "device_class": device_class,
                },
            )

    def get_info(self, response: Response, device_class: str) -> Generator[Request, None, None]:
        rows = response.xpath("//tbody/tr")
        for row in rows:
            name = row.xpath("td[@class='name']/text()").get()
            if name and "Firmware" in name:
                date = row.xpath(self.xpath["date"]).get()
                version = row.xpath(self.xpath["version"]).get()
                download_link_part = row.xpath(self.xpath["download_link"]).get()

                clean_name = self.clean_text(name)
                better_date = self.make_pretty_date(date)
                clean_version = self.clean_text(version)
                download_link = f"{self.base_url}{download_link_part}"

                assert (
                    device_class != "discontinued_model"
                ), "Please check the discontinued model category, the device class is wrong."
                assert (
                    device_class != "unknown yet"
                ), "Another device class showed up on totolink. Please add it to the mapping."
                assert (
                    device_class != "not_known"
                ), "Firmware showed up in the adapter, iot, or smart conference systems category. Please classify it."

                meta_data = {
                    "vendor": "totolink",
                    "release_date": datetime.strptime(better_date, "%Y-%m-%d").isoformat(),
                    "device_name": clean_name,
                    "firmware_version": clean_version,
                    "device_class": device_class,
                    "file_urls": download_link,
                }
                yield from self.item_pipeline(meta_data)

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        cleaned = text.replace("\n", "").replace("\t", "").replace("_Firmware", "").strip()

        return cleaned

    def make_pretty_date(self, date: str) -> None:
        date = date.replace(" ", "")
        if not date:
            date = "1970-01-01"

        return date

    def replace_keywords(self, texts: List[str]) -> List[str]:
        def replace(text: str) -> str:

            text = text.replace("menu_newstpl", "menu_listtpl")
            text = text.replace("newstpl", "detail")
            text = text.replace("products", "download")

            if ".html" in text:
                text = text.replace(".html", "/ids/36.html")

            return text

        return [replace(text) for text in texts]

    @staticmethod
    def map_device_class(
        device_titles: List[str],
    ) -> List[str]:
        def classify(title: str) -> str:
            title_lower = title.lower()

            if "switch" in title_lower:
                return "switch"
            if "adapter" in title_lower:
                return "not_known"
            if "router" in title_lower:
                return "router"
            if "pon" in title_lower:
                return "router"
            if "range extender" in title_lower:
                return "repeater"
            if "camera" in title_lower:
                return "ipcam"
            if "iot" in title_lower:
                return "not_known"
            if "smart conference system" in title_lower:
                return "not_known"
            if "cpe" in title_lower:
                return "accesspoint"
            if "discontinued model" in title_lower:
                return "discontinued_model"

            return "unknown yet"

        return [classify(title) for title in device_titles]
