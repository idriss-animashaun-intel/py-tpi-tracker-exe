# -*- coding: utf-8 -*-

"""DBAPI-2-compliant database adapter for Uber.

PiUber is co-written by Daniel Lenski (Intel PTD LYA), 2013-2015
and Victor Uriarte (Intel FSM PDE), 2013-

* Docs, examples, updates: http://github.intel.com/fabnet/PiUber
* Python DBAPI-v2 specification: https://www.python.org/dev/peps/pep-0249

Uber/UNIQE is Intel LTD Automation's new (required!) middleware adapter
thingy for accessing the MAO (MARS, ARIES, OASYS) and XEUS Oracle databases.
More information: http://autowiki.intel.com/index.php?title=UNIQE

I've based PiUber mostly on the Uber example code in Perl, JSL, C#-script,
VBScript which you can find in C:/Uber/Test/ if you have installed Uber.
There are also some documents from Anirudh Modi (Uber dev) found here:
file://amodi-dev1.ltdauto.intel.com/Public/UNIQE/Documents

PiUber accesses Uber via the .NET API (as used in the C#Script examples)
rather than the Win32 API (used in the JMP wrapper and JSL examples).

threadsafety = 2; Based on email discussion between Dan and Anirudh Modi,
sharing connection objects is thread-safe.
"""

__version__ = '1.6.2'
__author__ = 'Victor M. Uriarte <victor.m.uriarte@intel.com>'

paramstyle = 'named'
apilevel = '2.0'
threadsafety = 2

import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

from .exceptions import *
from .types import *
from .core import *
from .rows_factory import *
