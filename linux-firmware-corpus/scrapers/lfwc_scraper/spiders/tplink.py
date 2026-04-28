from datetime import datetime
from typing import Generator

from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class TPLink(FirmwareSpider):
    handle_httpstatus_list = [404]
    name = "tplink"

    allowed_domains = ["www.tp-link.com", "static.tp-link.com"]

    start_urls = [
        "https://www.tp-link.com/de/support/download/",
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": True,
    }

    xpath = {
        "products_on_page": '//a[contains(@class,"tp-product-link")]/@href',
        "product_pages": '//li[@class="tp-product-pagination-item"]/a[@class="tp-product-pagination-btn"]/@href',
        "product_name": '//h2[@class="product-name"]/text()|//label[@class="model-select"]/p/span/text()',
        "product_support_link": '//a[contains(@class,"support")]/@href',
        "firmware_download_link": '//tr[@class="basic-info"]/th[contains(@class, "btnbox")]/a[contains(@class, "download") and '
        '(contains(@data-vars-event-category, "Firmware") or '
        'contains(@href, "firmware"))]/@href',
        "device_revision": '//span[@id="verison-hidden"]/text()',
        "firmware_release_date": '//*[@id="tabpanel-Firmware"]/table/tbody/tr[@class="detail-info"][1]/td[1]/span[2]/text()[1]',
    }

    def parse(self, response: Response, **_: dict) -> Generator[Request, None, None]:
        category_names = response.xpath('//span[@class="tp-m-show"]/text()').extract()
        category_names_hidden = response.xpath('//span[@class="tp-m-hide"]/text()').extract()
        category_xpath_selectors = response.xpath('//div[@class="item-box"]')

        for name, selector, name_hidden in zip(category_names, category_xpath_selectors, category_names_hidden):
            device_class = self.map_device_class(name)

            if device_class == "unknown":
                device_class = self.map_device_class(name_hidden)

            print(f"cls: {name} -> {device_class}")

            links = selector.xpath('.//a[@class="ga-click" and contains(@href, "download")]/@href').extract()
            device_names = selector.xpath('.//a[@class="ga-click" and contains(@href, "download")]/text()').extract()

            if len(links) != len(device_names):
                print(f"WARN: scraping of category {name}, {name_hidden} failed: link-device pairing error.")
                continue

            for device_name, link in zip(device_names, links):

                # There is an egde case for TL-EC5... where many devices share
                # the same entry and we get out of sync...
                # We loose like 5 devices with special characters, but hey,
                # better to have no data than wrong data.
                #if device_name.replace(" ", "-").lower() not in link:
                #    print(f"WARN: maybe device-link pairing error: {device_name}, {link}")
                #    continue

                print(f"dev: {device_name} -> {link}")

                yield Request(
                    url=response.urljoin(link),
                    callback=self.select_hardware_revision,
                    cb_kwargs={
                        "device_name": device_name,
                        "device_class": device_class,
                    },
                )

    @classmethod
    def select_hardware_revision(
        cls, support_page: Response, device_name: str, device_class: str
    ) -> Generator[FirmwareItem | Request, None, None]:
        revisions = support_page.xpath('//dl[@class="select-version"]//ul/li/@data-value').extract()
        links = support_page.xpath('//dl[@class="select-version"]//ul/li/a/@href').extract()

        if not revisions:
            print(f"  rev: {device_name}: no revisions")
            yield from cls.get_firmware_items(support_page, device_name, device_class)
            return

        for rev, link in zip(revisions, links):
            print(f"  rev: {device_name} -> {rev}, {link}")
            yield Request(
                url=link,
                callback=cls.get_firmware_items,
                cb_kwargs={
                    "device_name": f"{device_name} {rev}",
                    "device_class": device_class,
                },
            )

    @classmethod
    def get_firmware_items(
        cls, support_page: Response, device_name: str, device_class: str
    ) -> Generator[FirmwareItem, None, None]:
        file_urls = cls.extract_firmware_download_links(support_page)
        release_dates = cls.extract_firmware_release_dates(support_page)

        if file_urls:
            assert device_class != "unknown", \
                    f"Class of '{device_name}' is not assigned!\n" \
                    f"{file_urls}"

        else:
            assert not release_dates, \
                    f"Failed to parse firmware links for '{device_name}'\n" \
                    f"{release_dates}"
            print(f"    fw: {device_name} -> no firmware")
        assert len(file_urls) == len(release_dates), \
                f"Missmatch: {len(file_urls)=} != {len(release_dates)=} for '{device_name}'\n" \
                f"{file_urls}\n" \
                f"{release_dates}\n"

        for link, release_date in zip(file_urls, release_dates):
            print(f"    fw: {device_name} -> {link}, {release_date}")
            meta_data = cls.prepare_meta_data(device_name, device_class, link, release_date)
            yield from cls.item_pipeline(meta_data)

    @staticmethod
    def prepare_meta_data(device_name: str, device_class: str, file_url: str, firmware_release_date) -> dict:
        return {
            "file_urls": [file_url],
            "vendor": "TP-Link",
            "device_name": f"{device_name}",
            "firmware_version": file_url.replace(".zip", "").split("_")[-1],
            "device_class": device_class,
            "release_date": datetime.strptime(firmware_release_date.strip(), "%Y-%m-%d").isoformat(),
        }

    @classmethod
    def extract_firmware_download_links(cls, support_page: Response) -> list[str]:
        return [
            support_page.urljoin(link) for link in support_page.xpath(cls.xpath["firmware_download_link"]).extract()
        ]

    @classmethod
    def extract_firmware_release_dates(cls, support_page: Response) -> str:
        return support_page.xpath(cls.xpath["firmware_release_date"]).extract()

    @staticmethod
    def map_device_class(category: str) -> str:
        if "repeater" in category.lower():
            return "repeater"
        if "deco" in category.lower():
            return "mesh"
        if "wlan-router" in category.lower():
            return "router"
        if "mobile 3g/4g-router" in category.lower():
            return "router"
        if "managed switches" in category.lower():
            return "switch"
        if "powerline-adapter" in category.lower():
            return "powerline"
        if "dsl-router" in category.lower():
            return "router"
        if "mobil (3g/4g)" in category.lower():
            return "router"
        if "soho switches" in category.lower():
            return "switch"
        if "3g/4g-router" in category.lower():
            return "router"
        if "router" in category.lower():
            return "router"
        if "poe-switches" in category.lower():
            return "switch"
        if "switches" in category.lower():
            return "switch"
        if "accesspoints" in category.lower():
            return "accesspoint"
        if "business-wlan" in category.lower():
            return "accesspoint"
        if "cloud-kameras" in category.lower():
            return "ipcam"
        if "omada-cloud-sdn > controller" in category.lower():
            return "controller"
        if "vpn-router" in category.lower():
            return "router"
        if "aps zur deckenmontage" in category.lower():
            return "accesspoint"
        if "ceiling mount" in category.lower():
            return "accesspoint"
        if "omada-cloud-sdn > switches" in category.lower():
            return "switch"
        if "smart-switches" in category.lower():
            return "switch"
        if "outdoor-aps" in category.lower():
            return "accesspoint"
        if "loadbalance-router" in category.lower():
            return "router"
        if "omada-cloud-sdn > router" in category.lower():
            return "router"
        if "easy-smart-switches" in category.lower():
            return "switch"
        if "aps zur wandmontage" in category.lower():
            return "accesspoint"
        if "outdoor-wlan" in category.lower():
            return "accesspoint"
        if "outdoor-aps" in category.lower():
            return "accesspoint"
        if "hardware-controller" in category.lower():
            return "controller"
        if "vigi netzwerkkameras" in category.lower():
            return "ipcam"
        if "vigi netzwerkvideorecorder" in category.lower():
            return "ipcam-recorder"
        if "wlan stick" in category.lower():
            return "wifi-usb"
        if "verstärker" in category.lower():
            return "repeater"
        if "vdsl" in category.lower():
            return "router"
        if "access point" in category.lower():
            return "accesspoint"
        if "videorekorder" in category.lower():
            return "ipcam-recorder"
        if "solar power system" in category.lower():
            return "power_supply"
        if "omada > wifi > ceiling mount" in category.lower():
            return "accesspoint"
        if "omada > wifi > outdoor" in category.lower():
            return "accesspoint"
        if "festa > wifi" in category.lower():
            return "accesspoint"
        if "gateways" in category.lower():
            return "gateway"
        if "kameras" in category.lower():
            return "ipcam"
        if "smart-home > sicherheit" in category.lower():
            return "ipcam"
        if "cpe" in category.lower():
            return "accesspoint"
        return "unknown"
