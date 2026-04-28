import re
from json import loads

from scrapy.http import Response

from lfwc_scraper.custom_spiders import FirmwareSpider


class ArchiveAVM(FirmwareSpider):
    name = "archive_avm"
    allowed_domains = ["web.archive.org"]
    start_urls = [
        "https://web.archive.org/cdx/search/cdx?url=download.avm.de&matchType=prefix&limit=10000"
        "&filter=urlkey:.*(image|zip|bin|raw)$&output=json&filter=!urlkey:.*(misc|other|english|englisch).*"
        "&filter=statuscode:200"
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 10,
        "CONCURRENT_ITEMS": 1,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
    }

    meta_regex = {
            # https://regex101.com/r/VDVlXb/1
            # groups:
            #   4: device_name
            #   7: version
        "file_name": re.compile(r"^((FRITZ|fritz|AVM_FRITZ|avm_fritz)(\.|_|%21|!))?(.*?)(\.|-|_)(build_|Build_)?((\d{2,3}\.\d\d|\d{2,3}\.\d\d\.\d\d|\d{2,3}_\d\d|\d{2,3}_\d\d_\d{2,3}|(\d{1,2}\.){1,2}\d\d-\d{5,6}|\d{5,6})(-Inhaus|-LabBETA|-LabPLUS|-Release|_CE|e)?)\.(image|zip|raw|bin)$"),
    }

    def parse(self, response: Response, **_):
        images_in_archive = loads(response.text)[1:]

        for _, archive_timestamp, original_url, _, _, _, _ in images_in_archive:
            if "develper" in original_url:
                continue

            file_name = original_url.split("/")[-1]
            device_name, firmware_version = self.parse_file_name(file_name)
            image_url = f"https://web.archive.org/web/{archive_timestamp}if_/{original_url}"
            meta_data = {
                "vendor": "AVM",
                "source": "archive.org",
                "file_urls": [image_url],
                "device_name": device_name if device_name else file_name,
                "device_class": self.map_device_class(image_path=image_url),
                "firmware_version": firmware_version if firmware_version else "manual",
                "release_date": "",
            }

            yield from self.item_pipeline(meta_data)

    def parse_file_name(self, file_name) -> tuple[str | None, str | None]:
        match = self.meta_regex["file_name"].match(file_name)
        if match:
            device_name = match.group(4)
            firmware_version = match.group(7).replace("_", ".")
            self.logger.debug(
                f"Parsed file name: {file_name}: name <{device_name}>, ver. <{firmware_version}>"
            )
            return device_name, firmware_version
        else:
            self.logger.error(
                f"Unable to parse file name: {file_name}"
            )
            return None, None

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
