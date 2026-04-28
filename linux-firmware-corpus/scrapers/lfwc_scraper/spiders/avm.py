import os
import re
from datetime import datetime
from typing import Generator, Union

from scrapy import Request
from scrapy.http import Response

from lfwc_scraper.custom_spiders import FTPSpider
from lfwc_scraper.items import FirmwareItem

from urllib.parse import urljoin
from urllib.parse import unquote, urlparse
import os



class AVM(FTPSpider):
    handle_httpstatus_list = [404]
    name = "avm"
    allowed_domains = ["ftp.avm.de", "avm.de", "download.avm.de"]
    start_urls = ["http://download.avm.de/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    meta_regex = {
        "device_name": re.compile(r"^\s?(?:Produkt|Controller|Product)\s*:\s+(.*)$", flags=re.MULTILINE | re.IGNORECASE),
        "firmware_version": re.compile(r"^\s?(Update|Version)\s*:\s+(.*)$", flags=re.MULTILINE | re.IGNORECASE),
        "firmware_version_from_name": re.compile(r"-(\d\d\.\d\d)\.(zip|image)$", flags=re.MULTILINE | re.IGNORECASE),
        "release_date": re.compile(r"^(?:Release-Datum|Build)\s*:\s+(.*)$", flags=re.MULTILINE | re.IGNORECASE),
    }

    def parse(self, response: Response, **_):
        if response.xpath('//title/text()').get().startswith( 'Index of '):
            for href in response.css('a::attr(href)').getall():
                next_url = urljoin(response.url, href)

                if href in ["../", "tools/", "develper/"]:
                    continue

                if href.endswith('/'):
                    yield Request(next_url, callback=self.parse)
                else:
                    file_name: str = unquote(os.path.basename(urlparse(next_url).path))

                    if self.is_fw(file_name):
                        yield from self.handle_fw_file(file_name, next_url, response)

        yield None

    def handle_fw_file(
            self, file_name: str, file_url: str, response: Response
    ):
        dir_ents: list[str] = response.xpath('//pre/text()').getall()[1:]
        dir_links: list[str] = response.xpath('//pre/a')[1:]
        info_path: str = urljoin(response.url, "info_de.txt")

        release_date = None
        for i, link in enumerate(dir_links):
            cur_filename: str = link.xpath('text()').get()

            if cur_filename.endswith("..>"):
                cur_filename = cur_filename[:-3]

            if file_name.startswith(cur_filename):
                sibling_text = dir_ents[i].strip()
                date_part = ' '.join(sibling_text.split()[:2])
                release_date = datetime.strptime(date_part, "%d-%b-%Y %H:%M")
        assert release_date is not None, f"Failed to find date for: {file_url}"

        yield Request(
            info_path,
            callback=self.check_info_file_exists,
            cb_kwargs={
                "info_file": info_path,
                "backup_info_files": [urljoin(response.url, url) for url in ["recover_de.txt", "info.txt", "info_en.txt"]],
                "image_path": file_url,
                "release_date": release_date
            },
        )

    def check_info_file_exists(self, response, **kwargs):
        if response.status == 200:
            self.logger.debug(f"Info file:\n{kwargs['info_file']}\nexists for:\n{kwargs['image_path']}")

            yield Request(
                kwargs["info_file"],
                dont_filter=True,
                callback=self.parse_metadata_and_download_image,
                cb_kwargs=kwargs
            )
        else:
            self.logger.info(f"Info file:\n{kwargs['info_file']}\nDOES NOT exist for:\n{kwargs['image_path']}.")

            if len(kwargs["backup_info_files"]) == 0:
                self.logger.error(f"Ran out of info files for: {kwargs['image_path']}")
                yield None
            else:
                info_path = kwargs["backup_info_files"][0]
                kwargs["backup_info_files"] = kwargs["backup_info_files"][1:]
                kwargs["info_file"] = info_path

                yield Request(
                    info_path,
                    callback=self.check_info_file_exists,
                    cb_kwargs=kwargs
                )


    def parse_metadata_and_download_image(
        self, response: Response, image_path, release_date, **_
    ) -> Generator[Union[Request, FirmwareItem], None, None]:
        info_txt = response.body.decode("latin-1")

        device_name_matches = self.meta_regex["device_name"].findall(info_txt)
        if len(device_name_matches) == 0:
            self.logger.info(
                f"No device_name matches: {len(device_name_matches)}\n" \
                f"Image: {image_path}\n" \
                f"Info:\n" \
                f"{info_txt}"
            )
            device_name = self.device_name_from_url(image_path)
            assert device_name is not None, \
                    f"Unable to extract device name for: {image_path}"
        else:
            device_name = device_name_matches[0].strip()
        if len(device_name_matches) > 1:
            self.logger.info(
                f"Unexpected number of device_name matches: {len(device_name_matches)}\n" \
                f"Image: {image_path}\n" \
                f"Matches: {[match.strip() for match in device_name_matches]}\n" \
                f"Info:\n" \
                f"{info_txt}"
            )

        fw_version_matches = self.meta_regex["firmware_version"].findall(info_txt)
        if len(fw_version_matches) == 0:
            self.logger.info(
                f"No firmware_version matches: {len(fw_version_matches)}\n" \
                f"Image: {image_path}\n" \
                f"Info:\n" \
                f"{info_txt}"
            )
            firmware_version = self.fw_version_from_url(image_path)
            assert firmware_version is not None, \
                    f"Unable to extract version name for: {image_path}"
        else:
            firmware_version = fw_version_matches[0][1].strip().split(" ")[-1]
        if len(fw_version_matches) > 1:
            self.logger.error(
                f"Unexpected number of firmware_version matches: {len(fw_version_matches)}\n" \
                f"Image: {image_path}\n" \
                f"Matches: {[match[1].strip() for match in fw_version_matches]}\n" \
                f"Info:\n" \
                f"{info_txt}"
            )

        meta_data = {
            "vendor": "AVM",
            "source": "vendor",
            "file_urls": [image_path],
            "device_name": device_name,
            "device_class": self.map_device_class(image_path),
            "firmware_version": firmware_version,
            "release_date": release_date.isoformat(),
        }

        yield from self.item_pipeline(meta_data)

    @staticmethod
    def is_fw(filename: str) -> bool:
        return (
                filename.endswith(".zip")
                or filename.endswith(".image")
                or filename.endswith(".bin")
                or filename.endswith(".raw")
        )

    @staticmethod
    def device_name_from_url(image_path: str) -> str | None:
        for d in image_path.split("/"):
            if d.startswith("fritzbox-"):
                return d

    @classmethod
    def fw_version_from_url(cls, image_path: str) -> str | None:
        fw_file_name = image_path.split("/")[-1]
        matches = cls.meta_regex["firmware_version_from_name"].findall(fw_file_name)
        if len(matches) == 0:
            return None
        else:
            return matches[0][0]

    def map_device_class(self, image_path: str) -> str:
        if any(substr in image_path.lower() for substr in ["repeater", "repeater"]):
            return "repeater"
        if "fritzwlan-usb" in image_path.lower():
            return "wifi-usb"
        if "fritzwlanusb" in image_path.lower():
            return "wifi-usb"
        if "powerline" in image_path.lower():
            return "powerline"
        if "fritzsmart-gateway" in image_path.lower():
            return "gateway"
        if "smartgateway" in image_path.lower():
            return "gateway"
        if "avm_voip_gateway" in image_path.lower():
            return "gateway"
        if "fritzfon" in image_path.lower():
            return "phone"
        if any(substr in image_path.lower() for substr in ["fritzbox", "fritz.box", "box.", "box_"]):
            return "router"
        self.logger.error(
            f"Unable to determine device class for: {image_path}"
        )
        return "unknown"
