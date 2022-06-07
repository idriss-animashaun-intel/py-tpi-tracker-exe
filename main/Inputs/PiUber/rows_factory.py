# -*- coding: utf-8 -*-

from collections import namedtuple

from ._compat import zip

__all__ = ['Row', 'NamedTupleRow', 'DictionaryRow', ]


class Row(object):
    """Default Row Factory.

    Default row factory leaves rows alone except for Pythonizing datetime
    objects and un-derping Int64 and fixing BLOB objects.
    """
    __slots__ = '_conv'

    def __init__(self, description, apidt2pydt):
        self._conv = [None] * len(description)
        for ii, d in enumerate(description):
            if d[1] == (16, 'System.DateTime'):
                self._conv[ii] = apidt2pydt
            elif d[1] == (11, 'System.Int64'):
                # Uber 4.0 API returns Int64 as a string... derp
                self._conv[ii] = int
            elif d[1] == (1, 'System.Object'):
                self._conv[ii] = bytearray

    def __call__(self, row):
        return [c(v) if (c and v is not None) else v
                for c, v in zip(self._conv, row)]


class NamedTupleRow(Row):
    __slots__ = '_ntt'
    _nt_cache = {}

    def __init__(self, description, apidt2pydt):
        super(NamedTupleRow, self).__init__(description, apidt2pydt)

        colnames = tuple(x[0] for x in description)
        if colnames in self._nt_cache:
            self._ntt = self._nt_cache[colnames]
        else:
            self._nt_cache[colnames] = self._ntt = namedtuple(
                'PiUberNamedTupleRow', colnames, rename=True)

    def __call__(self, row):
        return self._ntt._make(super(NamedTupleRow, self).__call__(row))


class DictionaryRow(Row):
    __slots__ = '_cn'

    def __init__(self, description, apidt2pydt):
        self._cn = tuple(x[0] for x in description)
        super(DictionaryRow, self).__init__(description, apidt2pydt)

    def __call__(self, row):
        return dict(zip(self._cn, super(DictionaryRow, self).__call__(row)))
