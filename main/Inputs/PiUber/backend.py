# -*- coding: utf-8 -*-
import logging
try:
    from Inputs.PiUber import _win32com
except:
    from TPITracker.Inputs.PiUber import _win32com

from ._compat import supress

logger = logging.getLogger(__name__)


def get_backend(backend=None):
    if backend not in (None, 'clr', 'win32com', '__fake__'):
        raise NameError("Invalid backend specified")

    if backend is None:
        logger.info("Backend not specified")


    if backend in ('win32com', None):
        with supress(ImportError):
            return _win32com


    if backend == None:
        raise ImportError("No valid backend avaliable")
    else:
        raise ImportError("%s backend not avaliable" % backend)

print(get_backend())