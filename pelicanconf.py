#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Начаров Михаил'
SITENAME = 'Заметки о Django'
SITEURL = 'https://www.webnach.ru'
# SITEURL = '.'

PATH = 'content'

TIMEZONE = 'Asia/Yekaterinburg'

DEFAULT_LANG = 'ru_RU'

DEFAULT_DATE_FORMAT = '%x'

LOCALE = ('ru_RU.utf8', 'en_US.utf8')

# Blogroll
LINKS_WIDGET_NAME = 'Ссылки'
LINKS = (('Python.org', 'http://python.org/'),
         ('Django', 'https://www.djangoproject.com/'),
         ('Debian', 'https://www.debian.org/'),)

# Social widget
SOCIAL = (('GitHub', 'https://github.com/mnach/'),)

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True


DISPLAY_PAGES_ON_MENU = True
SLUGIFY_SOURCE = 'basename'
STATIC_PATHS = ['images', 'extra/robots.txt']
# path-specific metadata
EXTRA_PATH_METADATA = {
    'extra/robots.txt': {'path': 'robots.txt'},
    }
# Аналитика
YANDEX_METRIKA = 45091683

THEME = 'themes/notmyidea/'

# Feed settings #
RSS_FEED_SUMMARY_ONLY = True
FEED_DOMAIN = SITEURL
FEED_ALL_RSS = 'feeds/all.rss.xml'
CATEGORY_FEED_RSS = 'feeds/%s.rss.xml'

FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

PELICAN_COMMENT_SYSTEM = True
PELICAN_COMMENT_SYSTEM_IDENTICON_DATA = ('author', 'email')
# Plugins #
PLUGIN_PATHS = ['pelican-plugins']
PLUGINS = ['sitemap', 'pelican_comment_system']

# Markdown for comments
MARKDOWN = {
    'extension_configs': {
        'markdown.extensions.codehilite': {'css_class': 'highlight'},
        'markdown.extensions.extra': {},
        'markdown.extensions.meta': {},
    },
    'output_format': 'html5',
}

# Sitemap
SITEMAP = {
    'format': 'xml',
    'priorities': {
        'articles': 0.9,
        'indexes': 0.8,
        'pages': 0.5
    },
    'changefreqs': {
        'articles': 'monthly',
        'indexes': 'weekly',
        'pages': 'monthly'
    }
}
