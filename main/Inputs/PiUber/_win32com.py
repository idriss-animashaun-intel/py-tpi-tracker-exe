# -*- coding: utf-8 -*-

from datetime import date, datetime

from pythoncom import CoInitialize, com_error
from win32com.client import Dispatch

from ._compat import PY3, UTC

DataServiceFactory = lambda: Dispatch(
    'Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory')
_UniqeClientHelper = lambda: Dispatch(
    'Intel.FabAuto.ESFW.DS.UBER.UniqeClientHelper')
_UniqeOperation = lambda: Dispatch(
    'Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Operation')
_UniqeQuery = lambda: Dispatch(
    'Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.Query')
_UniqeJob = lambda: Dispatch(
    'Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core.UniqeJob')
APIException = com_error


def _get_uber_version():
    """Retrieve version number of Uber installation.
    """
    v = DataServiceFactory().GetVersion()
    if '\n' in v:
        vdict = dict(
            (k[:-1], v) for k, v in (l.split(None, 1) for l in v.splitlines()))
        v = vdict['ProductVersion']
    return v


def apiexmsg(e):
    return e.excepinfo[2]


# there is no easy way to get subsecond resolution into or out of PWTime:
# http://sourceforge.net/p/pywin32/bugs/387/
def apidt2pydt(dt):
    # http://timgolden.me.uk/python/win32_how_do_i/use-a-pytime-value.html
    return datetime(year=dt.year, month=dt.month, day=dt.day, hour=dt.hour,
                    minute=dt.minute, second=dt.second)


# there is no easy way to get subsecond resolution into or out of PWTime:
# http://sourceforge.net/p/pywin32/bugs/387/
def pydt2apidt(dt):
    # PY3 win32com requires timezone on datetime objects: https://git.io/vo6LB
    if PY3 and type(dt) == date:
        dt = datetime(dt.year, dt.month, dt.day)
        dt = dt.replace(tzinfo=UTC)
    elif PY3 and dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


class UniqeClientHelper(object):
    def __init__(self):
        CoInitialize()
        self.UniqeClientHelper = _UniqeClientHelper()
        self.datasource = None
        self.timeout = 3600

    def __setattr__(self, name, value):
        if name in ('datasource', 'UniqeClientHelper'):
            super(UniqeClientHelper, self).__setattr__(name, value)
        elif name == 'timeout':
            setattr(self.UniqeClientHelper, 'TimeOutInSeconds', value)
        else:
            setattr(self.UniqeClientHelper, name, value)

    def __getattr__(self, name):
        if name == 'timeout':
            return self.UniqeClientHelper.TimeOutInSeconds
        return getattr(self.UniqeClientHelper, name)

    def execute_job(self, uniqe_job):
        _uniqe_job = uniqe_job.UniqeJob
        return [UniqeTable(ut) for ut in
                self.UniqeClientHelper.ExecuteJobForCOM(_uniqe_job)]

    def download(self, datasource, remotepath, localpath, foldernest=False):
        _helper = self.UniqeClientHelper
        _helper.DataSource = datasource
        _helper.DownloadFilesUsingFTP(remotepath, localpath, foldernest)


class UniqeJob(object):
    def __init__(self):
        self.UniqeJob = _UniqeJob()

    def add_operation(self, uniqe_operation):
        _uniqe_operation = uniqe_operation.UniqeOperation
        self.UniqeJob.AddOperation(_uniqe_operation)


class UniqeOperation(object):
    def __init__(self, datasource):
        self.datasource = datasource

        self.UniqeOperation = _UniqeOperation()
        self.UniqeOperation.DataSource = datasource

    def add_query(self, uniqe_query):
        _uniqe_query = uniqe_query.UniqeQuery
        self.UniqeOperation.AddQuery(_uniqe_query)


class UniqeQuery(object):
    def __init__(self, query, timeout=None, datasource=None):
        self.query = query
        self.timeout = timeout
        self.datasource = datasource

        self.UniqeQuery = _UniqeQuery()
        self.UniqeQuery.DataSource = datasource
        self.UniqeQuery.SQLStatement = query
        self.UniqeQuery.TimeOutInSeconds = timeout

    def add_parameter(self, key, value):
        self.UniqeQuery.AddParameter(key, value)

    def add_parameters(self, params):
        for (k, v) in params.items():
            if isinstance(v, date):
                self.add_parameter(k, pydt2apidt(v))
            elif getattr(v, 'dtype', None) == 'float64':
                self.add_parameter(k, v.astype('object'))
            elif v is None:
                raise NotImplementedError("can't convert None values for "
                                          "parameterized queries %s" % k)
            else:
                self.add_parameter(k, v)


class UniqeTable(object):
    def __init__(self, uniqe_table):
        self.UniqeTable = uniqe_table
        self._column_count = None
        self._rowstream = self._rowstreamer()

    def next_chunk(self):
        _uniqe_table = self.UniqeTable
        return list(_uniqe_table.GetNextChunk2D())

    def _rowstreamer(self):
        for chunk in iter(lambda: self.next_chunk(), []):
            for row in chunk:
                yield row

    def __next__(self):
        return next(self._rowstream)

    next = __next__

    def __iter__(self):
        return self

    def columns(self):
        _uniqe_table = self.UniqeTable
        cc = self.column_count
        return [_uniqe_table.GetColumnByIndex(ii) for ii in range(cc)]

    def saveToFile(self, outputFile, delimeter, dateFormat,
                   append, alwaysSuppressHeader):
        _uniqe_table = self.UniqeTable
        return _uniqe_table.SaveToFile(outputFile, delimeter, dateFormat,
                                       append, alwaysSuppressHeader)

    @property
    def column_count(self):
        if not self._column_count:
            self._column_count = self.UniqeTable.ColumnCount
        return self._column_count

    @property
    def row_count(self):
        _uniqe_table = self.UniqeTable
        return _uniqe_table.RowCount

    @property
    def chunk_count(self):
        _uniqe_table = self.UniqeTable
        return _uniqe_table.ChunkCount

    @property
    def data_available(self):
        _uniqe_table = self.UniqeTable
        return _uniqe_table.IsDataAvailable

    @property
    def status(self):
        # Extension Methods only work on C#, no way to extend to Win32COM.
        raise NotImplementedError
