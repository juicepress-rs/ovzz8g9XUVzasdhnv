import re
from datetime import datetime
from typing import Generator, Optional, Tuple

from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem

from urllib.parse import urljoin


class ClassIdentifier:
    def __init__(self, shortcuts: tuple):
        self.shortcuts: tuple = shortcuts


class Linksys(FirmwareSpider):
    name = "linksys"

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": True,
    }

    device_classes = {
        ClassIdentifier(("AM",)): "modem",
        ClassIdentifier(("CIT",)): "phone",
        ClassIdentifier(("EF", "EP", "PPS", "PSU", "WPS")): "printer",
        ClassIdentifier(("DMP", "DMC", "DMR", "DMS", "KWH", "MCC")): "media",
        ClassIdentifier(("DMA",)): "media",
        ClassIdentifier(("LAPN", "LAPAC")): "accesspoint",
        ClassIdentifier(("LCA",)): "ipcam",
        ClassIdentifier(("LMR", "LNR")): "video_recorder",
        ClassIdentifier(("LRT",)): "router",
        ClassIdentifier(("LGS",)): "switch",
        ClassIdentifier(("MR", "EA", "WRT", "E", "BEF", "WKU", "WRK")): "router",
        ClassIdentifier(("M10", "M20")): "accesspoint",
        ClassIdentifier(("PL",)): "powerline",
        ClassIdentifier(("RE", "WRE")): "repeater",
        ClassIdentifier(("SE", "EZX")): "switch",
        ClassIdentifier(("WAP",)): "accesspoint",
        ClassIdentifier(("WET", "WUM", "WES")): "repeater",
        ClassIdentifier(("WHW", "VLP", "MX")): "mesh",
        ClassIdentifier(("WMC", "WVC")): "ipcam",
        ClassIdentifier(("WML",)): "media",
        ClassIdentifier(("X", "AG", "WAG")): "router",
    }

    xpath = {
        "device_name": "//div[@class='hf-article_title']/text()",
        "download_page": '//a[contains(@title, "FIRMWARE")]/@href',
        "hardware_version_selectors": '//div[starts-with(@id, "version")]',
        "find_firmware": "//h4[@class='hf-section_item-title']//a[contains(.,'Firmware')]/@href",
        "downloads": "//a[@class='hf-article-item-link'][contains(.,'Downloads')]/@href",
    }

    start_urls = ["https://support.linksys.com/kb/"]
    base_url = "https://support.linksys.com"

    def parse(self, response: Response, **_) -> Generator[Request, None, None]:

        next_page = response.xpath(self.xpath["find_firmware"]).get()

        yield Request(url=urljoin(self.base_url, next_page), callback=self.parse_documentation_page)

    def parse_documentation_page(self, response: Response):
        page_links = response.xpath(self.xpath["downloads"]).getall()
        for link in page_links:
            yield Request(
                url=urljoin(self.base_url, link),
                callback=self.parse_download_page,
            )

    @classmethod
    def extract_date_and_version(cls, response: Response) -> Tuple[str, str]:
        matches = response.xpath(cls.xpath["date_and_version"]).extract()
        if len(matches) < 2:
            return "", ""

        firmware_version = matches[0].replace("Ver.", "")
        release_date = matches[1].split(" ")[-1].replace("/", "-")
        return firmware_version, release_date

    def parse_download_page(
        self,
        response: Response,
    ) -> Generator[FirmwareItem, None, None]:

        device_name = response.xpath(self.xpath["device_name"]).get()

        clean_device_name = device_name.split(" ")[0].replace("\n", "").replace("\t", "").strip()

        hw_version_selectors = response.xpath(self.xpath["hardware_version_selectors"])

        for sel in hw_version_selectors:
            hw_version = "ver. 1.0"
            hw_version_dirty = sel.xpath("./@id").get()

            if hw_version_dirty is not None:
                hw_version = f'ver. {hw_version_dirty.replace("version_", "").replace("_", ".")}'

            clean_device_name = f"{clean_device_name} {hw_version}"

            firmware_download_urls = sel.xpath('.//p//a[contains(@href, "firmware")]/@href').extract()
            versions = []
            release_dates = []

            date_finder = re.compile(r".*\:\s*(\d+\/\d+\/\d{4}).*")

            for text in sel.xpath('.//p[contains(text(), "Ver.")]/text()').extract():
                if "Ver." in text:
                    versions += [text.replace("Ver.", "").replace(" ", "")]
                    continue

                dates = date_finder.findall(text)
                if dates:
                    release_dates += [datetime.strptime(dates[0], "%m/%d/%Y").isoformat()]

            for url, version, date in zip(firmware_download_urls, versions, release_dates):
                meta_data = {
                    "vendor": "linksys",
                    "source": "vendor",
                    "file_urls": [url],
                    "device_name": clean_device_name,
                    "device_class": self.map_device_class(clean_device_name),
                    "firmware_version": version,
                    "release_date": date,
                }

                yield from self.item_pipeline(meta_data)

    @classmethod
    def map_device_class(cls, device_name: str) -> str:
        for identifiers, device_class in cls.device_classes.items():
            if device_name.startswith(identifiers.shortcuts):
                return device_class
        return "unknown"
