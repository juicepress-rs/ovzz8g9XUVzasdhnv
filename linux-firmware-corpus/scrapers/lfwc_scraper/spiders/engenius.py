import json
from datetime import datetime
from json import JSONDecodeError
from typing import Generator

from scrapy import Request
from scrapy.http import Response
from typing_extensions import override

from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class Engenius(FirmwareSpider):
    name = "engenius"
    manufacturer = "engenius"
    allowed_domains = (
        "www.engeniustech.com",
        "drive.google.com",
        "drive.usercontent.google.com",
        "static.engeniuscdn.com",
        "docs.engenius.ai",
    )

    custom_settings = {
        #"FILES_STORE": "/mnt/fwstore/00-firmware/09-engenius/firmware_files/",
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 3,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
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

    @override
    def start_requests(self):
        yield Request(
            url="https://www.engeniustech.com/eu/wp-json/wp/v2/file?status=publish&page=1&per_page=100&type=file",
            callback=self.parse_page,
            cb_kwargs={"current_page": 1},
        )

    def parse_page(
        self, response: Response, current_page: int, **_
    ) -> Generator[Request | FirmwareItem, None, None]:
        try:
            data = json.loads(response.body.decode())
        except (UnicodeDecodeError, JSONDecodeError):
            return

        for item in data:
            if item["acf"]["type"].lower() != "firmware":
                continue
            try:
                download_link = item["acf"]["download_link"]["url"]
            except Exception:
                download_link = item["acf"]["external_link"]["url"]

            release_date = datetime.strptime(
                item["date"].split("T")[0], "%Y-%m-%d"
            ).isoformat()

            firmware_version = item["acf"]["version"]
            try:
                device_class = item["pure_taxonomies"]["categories"][0][
                    "category_nicename"
                ]
            except Exception:
                device_class = "unknown"
            try:
                device_name = item["acf"]["download_link"]["name"]
            except Exception:
                device_name = item["slug"]
            meta_data = {
                "vendor": "engenius",
                "release_date": release_date,
                "device_name": device_name,
                "firmware_version": firmware_version,
                "device_class": device_class,
                "file_urls": download_link.replace(
                    "drive.google.com/uc", "drive.usercontent.google.com/download"
                ),
            }
            yield from self.item_pipeline(meta_data)

        yield Request(
            url="https://www.engeniustech.com/eu/wp-json/wp/v2/file?status=publish"
            f"&page={current_page + 1}&per_page=100&type=file",
            callback=self.parse_page,
            cb_kwargs={"current_page": current_page + 1},
        )
