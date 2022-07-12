# -*- coding: utf-8 -*-

"""Python 2.7.x, 3.3+ compatibility module.

Using Python 3 syntax to encourage upgrade unless otherwise noted.
http://lucumr.pocoo.org/2013/5/21/porting-to-python-3-redux/
"""

from __future__ import absolute_import, unicode_literals

import contextlib
import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
    from itertools import izip, imap

    string_types = (str, unicode)
    map = imap
    zip = izip
    UTC = None


    @contextlib.contextmanager
    def supress(*exceptions):
        try:
            yield
        except exceptions:
            pass


elif PY3:
    from datetime import timezone

    string_types = (str,)
    map = map
    zip = zip
    UTC = timezone.utc

    supress = contextlib.suppress
