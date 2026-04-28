import time
import logging
from pprint import pprint
from urllib.parse import urlparse

import scrapy
from scrapy.http import HtmlResponse

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from datetime import datetime
from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class DraytekSpider(FirmwareSpider):
    name = "draytek"
    allowed_domains = ["draytek.com"]
    start_urls = ["https://draytek.com/download_de/"]
    info_links = []
    firmware_counter = 0  # last count = 74

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
        logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

        self.driver = None
        self._start_browser()

    def _start_browser(self):

        options = Options()
        options.headless = True

        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", self.custom_settings["USER_AGENT"])


        try:
            exec_path = GeckoDriverManager().install()
            self.driver = webdriver.Firefox(
                executable_path=exec_path,
                options=options,
                firefox_profile=profile,
            )
        except Exception as e:
            self.logger.error(f"Error while starting the browser: {e}")

    def closed(self, reason):
        if self.driver:
            self.driver.quit()

    def parse_final(self, response):
        for link in self.info_links:
            parts = urlparse(link).path.strip("/").split("/")
            category = parts[-3]
            mapped_category = self.map_device_class(category)
            name = parts[-2]
            version = parts[-1].split("_", 1)[1].replace("zip", "")
            release_date = "1970-01-01"

            meta_data = {
                "vendor": "draytek",
                "release_date": datetime.strptime(release_date.strip(), "%Y-%m-%d").isoformat(),
                "device_name": name,
                "firmware_version": version,
                "device_class": mapped_category,
                "file_urls": link,
            }
            yield from self.item_pipeline(meta_data)

    def start_requests(self):
        for url in self.start_urls:
            response = self.get_response_with_selenium(url, wait_xpath="//tbody//a")
            if response:
                yield from self.parse(response)

    def parse(self, response):
        categories = response.xpath("//tbody//a/@href").getall()

        filtered_categories = [
            c for c in categories if c.startswith("Firmwares-") and c.endswith("/") and not "sprache" in c
        ]

        for category in filtered_categories:
            full_url = response.urljoin(category)
            yield from self.parse_category(full_url)

        yield scrapy.Request(
            url="https://draytek.com/download_de/",  # dummy url
            callback=self.parse_final,
            dont_filter=True,
        )

    def parse_category(self, url):
        response = self.get_response_with_selenium(url, wait_xpath="//tbody//a")
        if not response:
            return

        products = response.xpath("//tbody//a[not(contains(@href, '?'))]/@href").extract()

        for product in products:

            if not product.endswith("/") or "log" in product or ".html" in product or "gplsource" in product:
                continue

            full_url = response.urljoin(product)
            for item in self.parse_product(full_url):
                yield item

    def get_response_with_selenium(self, url, wait_xpath=None, max_wait=10):

        try:

            self.driver.get(url)

            if wait_xpath:
                self.logger.debug(f"Wait for xpath: {wait_xpath}")
                WebDriverWait(self.driver, max_wait).until(EC.presence_of_element_located((By.XPATH, wait_xpath)))

            body = self.driver.page_source
            return HtmlResponse(url=self.driver.current_url, body=body, encoding="utf-8")

        except Exception as e:
            self.logger.debug("No zipped firmware on this side")
            return None

    def parse_product(self, url):
        response = self.get_response_with_selenium(url, wait_xpath="//tbody//a[contains(@href, 'zip')]")
        if not response:
            return

        download_links = response.xpath("//tbody//a[contains(@href, 'zip')]/@href").extract()
        for link in download_links:
            if link:
                full_link = response.urljoin(link)

                try:
                    for item in self.correct_link(full_link):
                        yield item

                except:
                    continue

    def correct_link(self, url):
        if url:

            print(f"Download Link: {url}")
            self.info_links.append(url)

    def is_browser_alive(self):
        try:
            _ = self.driver.title
            return True
        except Exception as e:
            self.logger.warning(f"Browser crashed: {e}")
            return False

    def map_device_class(self, title: str) -> str:

        if "access" in title.lower():
            return "accesspoint"
        if "router" in title.lower():
            return "router"
        if "switch" in title.lower():
            return "switch"
        if "modem" in title.lower():
            return "modem"

        self.logger.error(f"Unable to determine device class for: {title}")
        return "unknown"
