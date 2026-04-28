from datetime import datetime
from typing import Generator
from scrapy import Request
from scrapy.http import Response
from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem
from urllib.parse import urlparse


class MoxaScraperSpider(FirmwareSpider):
    name = "moxa"
    allowed_domains = []

    start_urls = ["https://www.moxa.com/en/products"]

    base_url = "https://www.moxa.com"
    categories = []

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": True,
        "OFFSITE_ENABLED": False,  # own logic implemented and checked in extract_firmware because of dynamic URLs
    }

    xpath = {
        "categories": "//div[@class='container']//div[starts-with(@id, 'series')]//@href",
        "products": "(//div[@class='container'])[9]//a/@href",
        "product_name": "//tr[.//a[@data-type='Firmware']]//span[@class='js-checksum-filename']/text()",
        "firmware_link": "//tbody//a[@data-type='Firmware']//@href",
        "version": "//tr[.//a[@data-type='Firmware']]//span[@class='version-short']/text()",
        "release_date": "//tr[.//a[@data-type='Firmware']]//span[@class='date-short hide']/text()",
    }

    def parse(self, response: Response, **kwargs) -> Generator[Request, None, None]:
        category_pages = response.xpath(self.xpath["categories"]).extract()

        for page in category_pages:
            yield Request(
                url=f"{self.base_url}{page}",
                callback=self.get_products,
            )

    def get_products(self, response: Response, **kwargs) -> Generator[Request, None, None]:
        products = response.xpath(self.xpath["products"]).extract()
        for product in products:
            firmware_url = f"{self.base_url}{product}#resources"

            yield Request(
                url=f"{firmware_url}",
                callback=self.extractFirmware,
                cb_kwargs={
                    "device_class": self.map_device_class(self.extract_category_url(firmware_url)),
                    "device_name": self.extract_name_from_url(firmware_url),
                },
            )

    def extractFirmware(
        self, response: Response, device_class: str, device_name: str
    ) -> Generator[FirmwareItem, None, None]:

        firmware_link = response.xpath(self.xpath["firmware_link"]).extract()
        firmware_version = self.clean_text(response.xpath(self.xpath["version"]).extract())
        firmware_release_date = self.make_pretty_date(response.xpath(self.xpath["release_date"]).extract())

        counter = len(firmware_link)

        if counter > 0:

            for count in range(0, counter):
                assert device_class != "unknown", f"Unknown device class for device: {device_name}"
                if not self.is_allowed_domain(firmware_link[count]):
                    continue

                meta_data = {
                    "vendor": "moxa",
                    "release_date": datetime.strptime(firmware_release_date[count], "%b%d,%Y").isoformat(),
                    "device_name": device_name,
                    "firmware_version": firmware_version[count],
                    "device_class": device_class,
                    "file_urls": [firmware_link[count]],
                }
                yield from self.item_pipeline(meta_data)

    def clean_text(self, text):
        if not text:
            return "" if isinstance(text, str) else []

        def _clean(t):
            return t.replace("\n", "").replace("\t", "").strip()

        if isinstance(text, list):
            return [_clean(t) for t in text if isinstance(t, str)]
        elif isinstance(text, str):
            return _clean(text)
        else:
            return ""

    def make_pretty_date(self, date):
        def _format(d):
            d = d.replace(" ", "").replace("\r", "").replace("\n", "") if d else ""
            return d if d else "1970-01-01"

        if isinstance(date, list):
            return [_format(d) for d in date]
        elif isinstance(date, str):
            return _format(date)
        else:
            return "1970-01-01"

    def extract_name_from_url(self, url: str) -> str:
        if not url:
            return ""

        url = url.split("#")[0]
        url = url.rstrip("/")
        slug = url.split("/")[-1]

        return slug

    def extract_category_url(self, url: str) -> str:
        if not url:
            return ""

        url = url.split("#")[0].rstrip("/")
        parts = url.split("/")
        return "/".join(parts[-3:-1]) if len(parts) >= 3 else ""

    @staticmethod
    def map_device_class(device_title: str) -> str:
        title = device_title.lower()

        if "camera" in title or "video" in title or "ip-cameras" in title:
            return "ipcam"
        if "recorder" in title or "video-server" in title:
            return "recorder"
        if "switch" in title or "ethernet-embedded-modules" in title:
            return "switch"
        if "router" in title or "secure-router" in title:
            return "router"
        if "gateway" in title or "iiot-gateway" in title or "protocol-gateway" in title:
            return "gateway"
        if "controller" in title or "i-os" in title or "i-o-library" in title:
            return "controller"
        if "wireless-access" in title or "ap-bridge" in title or "wlan" in title:
            return "accesspoint"
        if "extender" in title or "repeater" in title:
            return "repeater"
        if "power-adapter" in title or "power-cord" in title or "power-suppl" in title:
            return "power_supply"
        if "converter" in title:
            return "converter"
        if "serial-board" in title or "pcie" in title or "pc-104" in title or "canbus" in title:
            return "board"
        if "usb" in title and ("serial" in title or "hub" in title):
            return "wifi-usb"
        if "media-converter" in title or "video" in title:
            return "media"
        if "poe-injector" in title or "poe-splitter" in title:
            return "power_supply"
        if "sfp-module" in title:
            return "converter"
        if "mounting-kit" in title:
            return "accessory"
        if "antenna" in title or "cable" in title or "amplifier" in title:
            return "accessory"
        if "serial-device-server" in title or "terminal-server" in title:
            return "converter"

        return "unknown"

    def is_allowed_domain(self, url: str) -> bool:
        parsed = urlparse(url)
        domain = parsed.hostname or ""
        if domain == "moxa.com":
            return True
        if domain.endswith(".moxa.com"):
            return True
        if domain.endswith(".azurefd.net"):
            return True
        return False
