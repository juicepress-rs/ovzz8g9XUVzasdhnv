import os
import re
from datetime import datetime
from typing import Generator

from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem
from scrapy_selenium import SeleniumRequest

from urllib.parse import urljoin
from urllib.parse import unquote, urlparse
import os
from pprint import pprint
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import requests
from selenium.common.exceptions import (
    TimeoutException,
    MoveTargetOutOfBoundsException,
    ElementClickInterceptedException,
)
import logging


class Netis(FirmwareSpider):

    name = "netis"

    start_urls = ["https://www.netis-systems.com/support/download.html"]
    base_url = "https://www.netis-systems.com"
    firmware_counter = 0
    allowed_domains = (
        "www.netis-systems.com",
        "oss.netis-systems.com",
    )
    logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)

    downloadable_firmware_counter = 0
    item_counter = 0
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    xpath = {}

    def parse(self, response: Response, **_) -> Generator[Request, None, None]:
        categories = response.xpath("//div[@class='top']//span[@class='pc']/text()").extract()

        for c1 in range(1, len(categories)):
            good_category = self.map_device_class(categories[c1])
            link = response.xpath(f"(//div[@class='a_link_box'])[{c1}]//@href").extract()
            name = response.xpath(f"(//div[@class='a_link_box'])[{c1}]//a/text()").extract()
            for c2 in range(1, len(link)):
                yield SeleniumRequest(
                    url=f"{self.base_url}{link[c2]}",
                    callback=self.download_page,
                    cb_kwargs={
                        "product_class": good_category,
                        "product_name": name[c2],
                    },
                )

    def download_page(
        self, response: Response, product_class: str, product_name: str
    ) -> Generator[Request | FirmwareItem, None, None]:
        items = []
        self.item_counter += 1
        version = response.xpath(
            "//div[@class='d-title'][contains(., 'Firmware')]/following::div[@class='t-title']/text()"
        ).extract()

        date = response.xpath(
            "//div[@class='d-title'][contains(., 'Firmware')]/following::div[@class='time']/text()"
        ).extract()

        tabs = response.xpath("//div[@class='tabs']//text()").extract()
        pretty_tabs = self.clean_tabs(tabs)
        if "Firmware" in pretty_tabs:
            driver = response.meta["driver"]

            driver.get(response.url)

            self.firmware_counter += 1
            time.sleep(5)
            download_buttons_2 = response.xpath(
                "//div[@class='t-mid']//a[contains(@onclick, 'download_file')]"
            ).extract()
            download_buttons = driver.find_elements(
                By.XPATH,
                "//div[@class='t-mid']//a[contains(@onclick, 'download_file')]",
            )

            c = 0

            for c in range(0, len(download_buttons)):
                try:
                    driver.maximize_window()
                    driver.execute_script("document.body.style.zoom='50%'")

                    data = self.extract_id(download_buttons_2[c])

                    actions = ActionChains(driver)
                    actions.move_to_element(download_buttons[c]).perform()
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_buttons[c])
                    time.sleep(0.5)

                    download_buttons[c].click()

                    try:
                        WebDriverWait(driver, 30).until(
                            EC.invisibility_of_element_located((By.ID, "layui-layer-shade1"))
                        )
                    except TimeoutException:
                        driver.refresh()
                        time.sleep(5)
                        download_buttons = driver.find_elements(
                            By.XPATH,
                            "//div[@class='t-mid']//a[contains(@onclick, 'download_file')]",
                        )
                        download_buttons_2 = response.xpath(
                            "//div[@class='t-mid']//a[contains(@onclick, 'download_file')]"
                        ).extract()

                        continue

                    time.sleep(1)

                    headers = {
                        "User-Agent": "Mozilla/5.0",
                        "X-Requested-With": "XMLHttpRequest",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Referer": driver.current_url,
                    }

                    selenium_cookies = driver.get_cookies()
                    cookie_dict = {cookie["name"]: cookie["value"] for cookie in selenium_cookies}

                    url = "https://www.netis-systems.com/support/download_file.html"
                    r = requests.post(url, headers=headers, data=data, cookies=cookie_dict)
                    resp = r.json()
                    url = resp.get("file")

                    clean_date = self.clean_date(date[c])

                    meta_data = {
                        "vendor": "netis",
                        "release_date": datetime.strptime(clean_date, "%d-%m-%Y").isoformat(),
                        "device_name": product_name,
                        "firmware_version": version[c],
                        "device_class": product_class,
                        "file_urls": [url],
                    }

                    items.append(meta_data)

                except (MoveTargetOutOfBoundsException, ElementClickInterceptedException):

                    continue
        if items:
            for item in items:
                yield from self.item_pipeline(item)

    @staticmethod
    def map_device_class(device_title: str) -> str:
        if "switch" in device_title.lower():
            return "switch"
        if "lte" in device_title.lower():
            return "router"
        if "adapter" in device_title.lower():
            return "wlan-usb"
        if "powerline" in device_title.lower():
            return "powerline"
        if "router" in device_title.lower():
            return "router"
        if "pcie" in device_title.lower():
            return "wlan-usb"
        if "access" in device_title.lower():
            return "accesspoint"
        if "swit" in device_title.lower():
            return "switch"
        if "poe" in device_title.lower():
            return "switch"
        if "bridge" in device_title.lower():
            return "accesspoint"
        if "extender" in device_title.lower():
            return "repeater"
        if "bridge" in device_title.lower():
            return "accesspoint"
        if "pon" in device_title.lower():
            return "gateway"
        return "unknown"

    def clean_tabs(self, tabs: list) -> list:
        cleaned = []
        for tab in tabs:
            if tab:
                text_clean = tab.replace("\n", "").strip()
                if text_clean:
                    cleaned.append(text_clean)
        return cleaned

    def clean_date(self, date: str) -> str:
        if date:
            date = date.split(":", 1)[-1].strip()
            return date
        else:
            return "01-01-1970"

    def extract_id(self, url: str) -> dict:
        id = url.split("?", 1)[-1]
        id_value = id.split("=", 1)[-1]
        if "(" in id_value:
            id_value = id_value.split("(", 1)[-1]
            id_value = id_value.replace(")", "")
        id_dict = {"id": id_value}
        return id_dict
