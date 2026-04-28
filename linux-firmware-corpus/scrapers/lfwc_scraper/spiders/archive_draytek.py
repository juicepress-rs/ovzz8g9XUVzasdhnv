import time
import logging
from pprint import pprint
from urllib.parse import urlparse
from scrapy import Request
from scrapy.http import Response


import scrapy
from scrapy.http import HtmlResponse

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class DraytekSpider(FirmwareSpider):
    name = "archive_draytek"
    allowed_domains = ["fw.draytek.com.tw"]
    start_urls = ["https://fw.draytek.com.tw/"]
    info_links = []
    firmware_counter = 0  # ca 2800
    responses_429 = 0

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 3,  # needs to be this high (no 429 errors)
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0",
    }

    def parse(self, response):
        if response.status == 429:
            self.responses_429 += 1
        categories = response.xpath("//table//tr//td/a/@href").extract()

        filtered_categories = [c for c in categories if c.endswith("/")]

        for category in filtered_categories:
            full_url = response.urljoin(category)
            try:

                yield Request(url=f"{full_url}", callback=self.is_firmware)

            except:
                continue

    def is_firmware(self, response):
        if response.status == 429:
            self.responses_429 += 1
        categories = response.xpath("//table//tr//td/a/@href").extract()

        for cat in categories:
            if "Firmware" in cat:

                yield Request(url=response.urljoin(cat), callback=self.get_versions)

    def get_versions(self, response):
        if response.status == 429:
            self.responses_429 += 1

        title = response.xpath("//title/text()").get()
        self.logger.info(f"Title: {title}")

        versions = response.xpath("//table//a/@href").extract()

        for version in versions:
            if version.endswith("/") and "v" in version:
                yield Request(url=response.urljoin(version), callback=self.get_firmware)

    def get_firmware(self, response):
        if response.status == 429:
            self.responses_429 += 1
        items = response.xpath("//table//a/@href").extract()
        ctr = len([item for item in items if ".zip" in item])
        c = 1
        for item in items:
            if ".zip" in item:
                release_date = response.xpath(
                    f"//table//tr/td[a[contains(@href, '.zip')]]/following-sibling::td[{c}]/text()"
                ).get()
                url = response.urljoin(item)
                self.logger.info(f"Firmware URL to extract: {url}")
                firmware_version = url.split("/")[-2]
                device_name = url.split("/")[-4]
                device_class = self.map_device_class(device_name)

                meta_data = {
                    "vendor": "draytek",
                    "release_date": datetime.strptime(release_date.strip(), "%Y-%m-%d %H:%M").isoformat(),
                    "device_name": device_name,
                    "firmware_version": firmware_version,
                    "device_class": device_class,
                    "file_urls": [url],
                }
                yield from self.item_pipeline(meta_data)

                c += 1

    def map_device_class(self, title: str) -> str:

        if "access" in title.lower() or "ap" in title.lower():
            return "accesspoint"
        if "router" in title.lower():
            return "router"
        if "switch" in title.lower():
            return "switch"
        if "modem" in title.lower():
            return "modem"

        return "unknown"
