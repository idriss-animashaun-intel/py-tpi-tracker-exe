# -*- coding: utf-8 -*-

import clr
import os
import sys
from datetime import datetime, date

uber_root = os.getenv('UBER_INSTALL_DIR')
uber_bin = os.path.join(uber_root, 'BIN')
sys.path.append(uber_bin)

clr.AddReference('Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory')
clr.AddReference('Intel.FabAuto.ESFW.DS.UBER.UberCommon')
clr.AddReference('Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core')

from Intel.FabAuto.ESFW.DS.UBER import DataServiceFactory
from Intel.FabAuto.ESFW.DS.UBER import MyExtensionMethods as _extensionMethods
from Intel.FabAuto.ESFW.DS.UBER import UniqeClientHelper as _UniqeClientHelper
from Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core import UniqeJob as _UniqeJob
from Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core import Operation as _UniqeOperation
from Intel.FabAuto.ESFW.DS.UBER.Uniqe.Core import Query as _UniqeQuery
from System import DateTime as SystemDatime, Exception as sys_Exception

APIException = sys_Exception


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
    return e.args


def apidt2pydt(dt):
    return datetime(dt.Year, dt.Month, dt.Day, dt.Hour,
                    dt.Minute, dt.Second, dt.Millisecond * 1000)


def pydt2apidt(dt):
    if isinstance(dt, datetime):
        return SystemDatime(dt.year, dt.month, dt.day, dt.hour,
                            dt.minute, dt.second, int(dt.microsecond / 1000))
    elif isinstance(dt, date):
        return SystemDatime(dt.year, dt.month, dt.day)


class UniqeClientHelper(object):
    def __init__(self):
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
                self.UniqeClientHelper.ExecuteJob(_uniqe_job)]

    def download(self, datasource, remotepath, localpath, foldernest=False):
        _helper = self.UniqeClientHelper
        _helper.DataSource = datasource
        _helper.DownloadFilesUsingFTP(remotepath, localpath, foldernest)


class UniqeJob(object):
    # create a single job containing a single operation with one query
    # for each datasource
    def __init__(self):
        self.UniqeJob = _UniqeJob()

    def add_operation(self, uniqe_operation):
        _uniqe_operation = uniqe_operation.UniqeOperation
        self.UniqeJob.AddOperation(_uniqe_operation)


class UniqeOperation(object):
    # create UniqeOperation object(s) (possibly include multiple datasources):
    #   multiple opers in one job:
    #     execute in parallel
    #     result in multi-table output
    #   multiple queries in one oper:
    #     MUST HAVE SAME SHAPE
    #     concatenated into one big table
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
        cc = self.column_count
        chunk = list(_uniqe_table.GetNextChunk2D())
        # Below needed due to pythonnet bug with 2D arrays
        return [chunk[c0:c0 + cc] for c0 in range(0, len(chunk), cc)]

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
        _uniqe_table = self.UniqeTable
        return _extensionMethods.GetJobStatus(_uniqe_table)
