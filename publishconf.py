#!/usr/bin/env python
# This file is only used if you use `make publish` or
# explicitly specify it as your config file.

from __future__ import unicode_literals

import os
import sys
sys.path.append(os.curdir)
from pelicanconf import *  # NOQA

OUTPUT_PATH = 'public'
SITEURL = 'https://www.webnach.ru'
RELATIVE_URLS = True

FEED_ALL_ATOM = 'feeds/all.atom.xml'
CATEGORY_FEED_ATOM = 'feeds/%s.atom.xml'

DELETE_OUTPUT_DIRECTORY = True

# Following items are often useful when publishing

# DISQUS_SITENAME = ""
# GOOGLE_ANALYTICS = ""
