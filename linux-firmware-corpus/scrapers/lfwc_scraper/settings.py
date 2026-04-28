# Scrapy settings for firmware project

from webdriver_manager.firefox import GeckoDriverManager

BOT_NAME = "lfwc_scraper"

SPIDER_MODULES = ["lfwc_scraper.spiders"]
NEWSPIDER_MODULE = "lfwc_scraper.spiders"

FILES_STORE = "firmware_files/"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True
DOWNLOAD_TIMEOUT = 320
LOG_LEVEL = "DEBUG"
FTP_USER = "anonymous"
FTP_PASSWORD = "guest"

SELENIUM_DRIVER_NAME = "firefox"
SELENIUM_DRIVER_ARGUMENTS = ["--headless"]
SELENIUM_DRIVER_EXECUTABLE_PATH = GeckoDriverManager().install()

DOWNLOAD_HANDLERS = {"ftp": "lfwc_scraper.handlers.FTPHandler"}

DOWNLOADER_MIDDLEWARES = {
    "scrapy_selenium.SeleniumMiddleware": 800,
#    "lfwc_scraper.middlewares.FirmwareDownloaderMiddleware": 543,
}


ITEM_PIPELINES = {
    "lfwc_scraper.pipelines.HpPipeline": 300,
    "lfwc_scraper.pipelines.AsusPipeline": 300,
    "lfwc_scraper.pipelines.AvmPipeline": 1,
    "lfwc_scraper.pipelines.LinksysPipeline": 1,
}
