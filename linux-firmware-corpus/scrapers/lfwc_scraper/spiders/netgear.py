import json
import re
from datetime import datetime
from typing import Generator
from scrapy_selenium import SeleniumRequest

from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class Netgear(FirmwareSpider):
    name = "netgear"
    manufacturer = "NETGEAR"

    start_urls = ["https://www.netgear.com/api/v2/getsearchjson/?componentId=52117&publicationId=65"]

    custom_settings = {
        # "FILES_STORE": "/mnt/fwstore/00-firmware/02-netgear/firmware_files/",
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": True,
        "COOKIES_ENABLED": True,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.5",
            "Dnt": "1",
            "Priority": "u=0, i",
            "Sec-Ch-Ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Linux",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-Gpc": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        },
    }

    xpath = {
        "get_firmware_text_a": '//div[@class="accordion-item"]//a[contains(text(), "Firmware")]',
        "get_firmware_text_b": '//div[@class="accordion-item"]//button[contains(text(), "Firmware")]',
        "get_release_date": '//p[@class="last-updated"]/text()',
    }

    regex = {"firmware_version": re.compile(r".*Firmware(?:\s?\-?[vV]ersion)?\s([\d\.]+).*$", flags=re.MULTILINE)}

    def parse(self, response: Response, **kwargs) -> Generator[Request, None, None]:
        raw_data = json.loads(response.text)
        all_products = json.loads(raw_data["data"]["componentPresentation"]["rawContent"]["content"].rstrip("\x00"))
        for product in all_products:
            device_class = self.map_device_class(product["title"])
            if device_class == "unknown" or product["external"] != "":
                continue
            support_url = response.urljoin(product["url"])
            device_name = product["model"]
            yield SeleniumRequest(
                url=support_url,
                callback=self.consult_support_pages,
                cb_kwargs={
                    "device_name": device_name,
                    "device_class": device_class,
                },
            )

    def consult_support_pages(
        self, response: Response, device_name: str, device_class: str
    ) -> Generator[Request | FirmwareItem, None, None]:
        fw_text_selectors = response.xpath(self.xpath["get_firmware_text_a"]) + response.xpath(
            self.xpath["get_firmware_text_b"]
        )

        for sel in fw_text_selectors:
            dirty_firmware_version = sel.xpath("./text()").get()
            content_sel = sel.xpath("./parent::h2/parent::div")
            download_link = content_sel.xpath('.//a[contains(@href,"downloads.netgear.com")]/@href').get()
            kb_article_link = content_sel.xpath('.//a[contains(@href, "kb.netgear.com")]/@href').get()
            firmware_version = self.regex["firmware_version"].findall(dirty_firmware_version)
            if len(firmware_version) == 1:
                firmware_version = firmware_version[0]
            else:
                firmware_version = "0.0.0.0"
            if kb_article_link is not None:
                yield Request(
                    url=kb_article_link,
                    callback=self.parse_kb_article,
                    cb_kwargs={
                        "firmware_version": firmware_version,
                        "download_link": download_link,
                        "device_name": device_name,
                        "device_class": device_class,
                    },
                )
            else:
                meta_data = {
                    "vendor": "netgear",
                    "release_date": datetime.strptime("01-01-1970", "%m-%d-%Y").isoformat(),
                    "device_name": device_name,
                    "firmware_version": firmware_version,
                    "device_class": device_class,
                    "file_urls": [download_link.strip()],
                }
                yield from self.item_pipeline(meta_data)

    def parse_kb_article(
        self,
        response: Response,
        device_name: str,
        firmware_version: str,
        download_link: str,
        device_class: str,
    ) -> Generator[FirmwareItem, None, None]:
        dirty_release_date = response.xpath(self.xpath["get_release_date"]).get()

        release_date = dirty_release_date.split(":")[-1].strip().replace("/", "-")

        meta_data = {
            "vendor": "netgear",
            "release_date": datetime.strptime(release_date, "%m-%d-%Y").isoformat(),
            "device_name": device_name,
            "firmware_version": firmware_version,
            "device_class": device_class,
            "file_urls": [download_link.strip()],
        }
        yield from self.item_pipeline(meta_data)

    @staticmethod
    def map_device_class(device_title: str) -> str:
        if any(substr in device_title.lower() for substr in ["usb", "unmanaged"]):
            return "unknown"
        if "switch" in device_title.lower():
            return "switch"
        if "access" in device_title.lower():
            return "accesspoint"
        if "repeater" in device_title.lower():
            return "repeater"
        if "powerline" in device_title.lower():
            return "powerline"
        if "router" in device_title.lower():
            return "router"
        if "modem" in device_title.lower():
            return "modem"
        if "mesh" in device_title.lower():
            return "mesh"
        return "unknown"
