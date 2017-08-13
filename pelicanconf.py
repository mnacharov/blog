#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Начаров Михаил'
SITENAME = 'Заметки о Django'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'Asia/Yekaterinburg'

DEFAULT_LANG = 'ru'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('Pelican', 'http://getpelican.com/'),
         ('Python.org', 'http://python.org/'),
         ('Jinja2', 'http://jinja.pocoo.org/'),
         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('You can add links in your config file', '#'),
          ('Another social link', '#'),)

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True


DISPLAY_PAGES_ON_MENU = True
SLUGIFY_SOURCE = 'basename'
# PLUGIN_PATHS = ['pelican-plugins']
# PLUGINS = ['read_more_link',]
STATIC_PATHS = ['images', ]

