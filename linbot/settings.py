import os

BOT_NAME = 'linbot'

# Scrapy settings for dirbot project

SPIDER_MODULES = ['dirbot.spiders']
NEWSPIDER_MODULE = 'dirbot.spiders'

DUPEFILTER_DEBUG = False

"""
DOWNLOADER_MIDDLEWARES = {
    'dirbot.scrapyjs.SplashMiddleware': 725,
}

SPLASH_URL = 'http://localhost:8050/'

DUPEFILTER_CLASS = 'dirbot.scrapyjs.SplashAwareDupeFilter'
HTTPCACHE_STORAGE = 'dirbot.scrapyjs.SplashAwareFSCacheStorage'
"""

# Set your own download folder
DOWNLOAD_FILE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "download_file")

# Enable auto throttle
AUTOTHROTTLE_ENABLED = True

LOG_LEVEL = 'DEBUG'

DOWNLOAD_DELAY = 3

COOKIES_ENABLED = True
COOKIES_DEBUG = False