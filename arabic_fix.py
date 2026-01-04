
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import codecs

# Set stdout encoding to UTF-8
if sys.version_info[0] < 3:
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
else:
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

# Flask app configuration for Arabic
class ArabicConfig:
    JSON_AS_ASCII = False
    JSONIFY_MIMETYPE = 'application/json; charset=utf-8'
