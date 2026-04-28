from scrapy.http import Response, Request
from typing import Generator
from datetime import datetime
from lfwc_scraper.custom_spiders import FirmwareSpider
from lfwc_scraper.items import FirmwareItem


class ZyxelSpider(FirmwareSpider):
    name = "zyxel"
    allowed_domains = ["zyxel.com", "www.zyxel.com", "download.zyxel.com"]
    start_urls = ["https://www.zyxel.com/de/de/products"]
    base_url = "https://www.zyxel.com"
    firmware_counter = 0
    sign_in_needed_firmware_counter = 0

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 10,
        "DOWNLOAD_DELAY": 0.75,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "REFERER_ENABLED": False,
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    }

    xpath = {
        "many_products": "//div[@class = 'product-list-item']//@href",
        "pagination": "//li[@class='pager__item']/a/@href",
        "category": "//div[@class = 'product-list-item']//h5/text()",
        "product": "(//div[@class='product-item-info']/a)[1]/@href",
        "pages": "//section[@id='block-products-list']//@href",
        "download_page": "//div[@class='product-header-tabs']//a[contains(@href, 'download')]/@href",
        "versions": "//table[@class='table table-hover table-striped']//tbody/tr[td[@headers='view-nothing-2-table-column' and contains(normalize-space(.), 'Firmware')]]/td[@headers='view-field-version-table-column']/text()",
        "dates": "//table[@class='table table-hover table-striped']//tbody/tr[td[@headers='view-nothing-2-table-column' and contains(normalize-space(.), 'Firmware')]]/td[@headers='view-field-release-date-table-column']/text()",
        "data_target": "//table[@class='table table-hover table-striped']//tbody/tr[td[@headers='view-nothing-2-table-column' and contains(normalize-space(.), 'Firmware')]]/td[@headers='view-nothing-1-table-column']//a/@data-target",
    }

    def parse(self, response: Response, **kwargs) -> Generator[Request, None, None]:
        products_page = response.xpath(self.xpath["many_products"]).extract()
        device_class = response.xpath(self.xpath["category"]).extract()

        for count in range(len(products_page)):
            product_url = response.urljoin(products_page[count])
            yield Request(
                url=product_url,
                callback=self.parse_product_page,
                cb_kwargs={"device_class": device_class[count]},
            )

        next_page = response.xpath(self.xpath["pagination"]).get()
        if next_page:
            next_page_url = response.urljoin(next_page.strip())
            if not next_page_url.startswith(("http://", "https://")):

                next_page_url = response.urljoin(next_page_url)
            yield Request(url=next_page_url, callback=self.parse)

    def parse_product_page(self, response: Response, device_class: str) -> Generator[Request, None, None]:

        yield Request(
            url=response.url, callback=self.product, cb_kwargs={"device_class": device_class}, dont_filter=True
        )

        next_page = response.xpath(self.xpath["pagination"]).get()
        if next_page:
            next_page_url = response.urljoin(next_page)
            yield Request(url=next_page_url, callback=self.parse_product_page, cb_kwargs={"device_class": device_class})

    def product(self, response: Response, device_class: str) -> Generator[Request, None, None]:
        pages = response.xpath(self.xpath["pages"]).extract()

        pages = [v for v in pages if "store" not in v]
        seen = set()
        unique_pages = []
        for v in pages:
            if v not in seen:
                unique_pages.append(v)
                seen.add(v)

        for page in unique_pages:
            device_class = self.get_class(page)
            if page and "page" not in page:
                yield Request(
                    url=page,
                    callback=self.to_download_page,
                    cb_kwargs={"device_class": device_class},
                )

    def to_download_page(self, response: Response, device_class: str) -> Generator[Request, None, None]:

        download_page = response.xpath(self.xpath["download_page"]).get()
        if download_page:
            model = download_page.split("=", 1)[1]
            yield Request(
                url=download_page,
                callback=self.get_firmware_stuff,
                cb_kwargs={"device_class": device_class, "product_name": model},
            )

    def get_firmware_stuff(
        self, response: Response, device_class: str, product_name: str
    ) -> Generator[FirmwareItem, None, None]:

        versions = response.xpath(self.xpath["versions"]).extract()
        dates = response.xpath(self.xpath["dates"]).extract()

        data_target = response.xpath(self.xpath["data_target"]).extract()

        for counter in range(0, len(versions)):
            data_target[counter] = data_target[counter].replace("#", "")
            download_link = response.xpath(f"//div[@id='{data_target[counter]}']//a/@href").extract()
            dates[counter] = self.map_date(dates[counter])
            if dates[counter] is None:
                dates[counter] = "January 1, 1970"
            else:
                dates[counter] = dates[counter].strip()

            if len(download_link) == 1:

                meta_data = {
                    "vendor": "zyxel",
                    "release_date": datetime.strptime(dates[counter], "%B %d, %Y").isoformat(),
                    "device_name": product_name,
                    "firmware_version": versions[counter].strip(),
                    "device_class": device_class,
                    "file_urls": download_link,
                }
                yield from self.item_pipeline(meta_data)

    def get_class(self, link: str):
        title_lower = link.lower()
        if "switch" in title_lower:
            return "switch"
        if "access-point" in title_lower:
            return "Accesspoint"
        if "router" in title_lower:
            return "router"
        if "wifi" in title_lower:
            return "router"
        if "range extender" or "repeater" in title_lower:
            return "repeater"
        if "recorder" in title_lower:
            return "recorder"
        if "controller" in title_lower:
            return "controller"

        return "unknown yet"

    def map_date(self, date: str):
        month_map = {
            "Januar": "January",
            "Februar": "February",
            "März": "March",
            "April": "April",
            "Mai": "May",
            "Juni": "June",
            "Juli": "July",
            "August": "August",
            "September": "September",
            "Oktober": "October",
            "November": "November",
            "Dezember": "December",
        }

        for de_month, en_month in month_map.items():
            if de_month in date:
                date = date.replace(de_month, en_month)
                return date
