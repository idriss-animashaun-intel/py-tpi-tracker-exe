# -*- coding: utf-8 -*-

from datetime import date, datetime, time

__all__ = ['Date', 'Time', 'Timestamp', 'DateFromTicks',
           'TimeFromTicks', 'TimestampFromTicks', 'Binary',
           'STRING', 'BINARY', 'DATETIME', 'ROWID',
           'NUMBER_INTEGER', 'NUMBER_FLOAT', 'NUMBER',
           ]


def Date(year, month, day):
    """
    This function constructs an object holding a date value.
    """
    return date(year, month, day)


def Time(hour, minute, second):
    """
    This function constructs an object holding a time value
    """
    return time(hour, minute, second)


def Timestamp(year, month, day, hour, minute, second):
    """
    This function constructs an object holding a time stamp value.
    """
    return datetime(year, month, day, hour, minute, second)


def DateFromTicks(ticks):
    """
    This function constructs an object holding a date value from the given
    ticks value (number of seconds since the epoch; see the documentation of
    the standard Python time module for details).
    """
    return date.fromtimestamp(ticks)


def TimeFromTicks(ticks):
    """
    This function constructs an object holding a time value from the given
    ticks value (number of seconds since the epoch; see the documentation of
    the standard Python time module for details).
    """
    return datetime.fromtimestamp(ticks).time()


def TimestampFromTicks(ticks):
    """
    This function constructs an object holding a timestamp value from the given
    ticks value (number of seconds since the epoch; see the documentation of
    the standard Python time module for details).
    """
    return datetime.fromtimestamp(ticks)


def Binary(string):
    """
    This function constructs an object capable of holding a binary (long)
    string value.
    """
    return memoryview(string)


class DBAPITypeObject(object):
    def __init__(self, *values):
        self.values = values

    def __eq__(self, other):
        return other in self.values

    def __repr__(self):
        return repr(self.values)


# seems to be how raw Oracle columns show up(ARIES.A_ALL_RAW_TEST_DATA)
BINARY = DBAPITypeObject((1, 'System.Object'), )

# FIXME: Are ROWID *always* strings?
ROWID = DBAPITypeObject((18, 'System.String'), )

STRING = DBAPITypeObject((18, 'System.String'), )

DATETIME = DBAPITypeObject((16, 'System.DateTime'), )

NUMBER_FLOAT = DBAPITypeObject((15, 'System.Decimal'),
                               (14, 'System.Double'), )
NUMBER_INTEGER = DBAPITypeObject((7, 'System.Int16'),
                                 (9, 'System.Int32'),
                                 (11, 'System.Int64'), )
NUMBER = DBAPITypeObject((7, 'System.Int16'),
                         (9, 'System.Int32'),
                         (11, 'System.Int64'),
                         (14, 'System.Double'),
                         (15, 'System.Decimal'), )
