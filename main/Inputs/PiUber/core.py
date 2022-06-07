# -*- coding: utf-8 -*-

# references for this module:
# \\amodi-dev1.ltdauto.intel.com\Public\UNIQE\Documents, esp. Uber HOW-TO.docx
# C:\Uber\Test, contains Uber example code in Perl, JSL, C#-script, VBCScript

from __future__ import print_function

import logging
from functools import wraps
from itertools import islice
from tempfile import NamedTemporaryFile

from ._compat import string_types, map
from .backend import get_backend
from .exceptions import DatabaseError, ProgrammingError
from .rows_factory import Row

__all__ = ['connect', ]
logger = logging.getLogger(__name__)


def check_active(f):
    """Validates cursor state.

    Checks that cursor has issued a query, and activates Cursor to start
    getting the results.
    """

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self._uniqeTables is None:
            raise ProgrammingError("Attempt to access data from cursor without "
                                   "having issued a query.")
        elif not self._active:
            self._activate()
        return f(self, *args, **kwargs)

    return wrapper


class Cursor(object):
    def __init__(self, connection, datasource, timeout=60, row_factory=Row,
                 backend=None):
        self.be = backend
        self.connection = connection
        # we ignore self.helper.DataSource and set datasource for each query
        self.helper = connection.helper
        # Connection object may have taken datasource from helper.DataSource,
        # see below
        self.datasource = datasource
        self.timeout = timeout
        self.row_factory = row_factory
        self.arraysize = 1
        self._reset()

    def _reset(self):
        # put cursor in a state where it's ready for a new query
        self._description = None
        self._uniqeTables = None
        self._rownumber = 0
        self._rowstream = None
        self._make_row = None
        self._active = False

    # Can't use check_active() because these are supposed to return specific
    # values rather than raise Exception if no query has been issued.
    @property
    def description(self):
        if self._uniqeTables is None:
            return None
        elif not self._active:
            self._activate()
        return self._description

    @property
    def rowcount(self):
        if self._uniqeTables is None:
            return -1
        elif not self._active:
            self._activate()
        return sum(t.row_count for t in self._uniqeTables)

    @property
    def rownumber(self):
        # Warning Message: `DB-API extension cursor.rownumber used`
        if self._uniqeTables is None:
            return -1
        elif not self._active:
            self._activate()
        return self._rownumber

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        pass

    def setinputsizes(self, sizes):
        pass

    def setoutputsize(self, size, column=None):
        pass

    def __del__(self):
        self.close()

    def execute(self, query, parameters=None, datasource=None, _activate=True,
                **kwargs):
        if parameters is None:
            parameters = kwargs
        else:
            duplicates = set(kwargs.keys()) & set(parameters.keys())
            if duplicates:
                raise ProgrammingError(
                    "same query parameters passed by keyword and dict: %s" %
                    ', '.join(duplicates))
            parameters.update(kwargs)
        self._reset()  # clear any remaining state from prior query
        self._submit(query, parameters, datasource, _activate)

    def executemany(self, query, parameters=None, datasource=None,
                    _activate=True):
        if not isinstance(parameters, (list, tuple)):
            raise ProgrammingError("Expect List of Parameters")
        self._reset()
        self._submit(query, parameters, datasource, _activate)

    def _submit(self, query, parameters, datasource, _activate):
        datasource = datasource or self.datasource
        if not datasource:
            raise ProgrammingError("datasource was not specified (on connect, "
                                   "on .cursor, or on .execute)")

        job = self.be.UniqeJob()
        logger.info("Running:\n%s\n%s", query, parameters)
        [job.add_operation(op) for op in
         self._make_uniqe_operations(query, parameters, datasource,
                                     self.timeout)]

        logger.info("ExecuteJob starting")
        self._uniqeTables = tuple(self.helper.execute_job(job))
        logger.info("ExecuteJob done")
        # normally, we force synchronous activation so that we get error msg
        self._activate() if _activate else None

    def _make_uniqe_operations(self, query, parameters, datasource, timeout):
        if isinstance(datasource, string_types):
            # If single datasource string. Convert it to a List/Tuple
            datasource = (datasource,)

        if isinstance(parameters, dict):
            # If single parameters dict. Convert it to a List/Tuple
            parameters = (parameters,)

        for ds in datasource:
            operation = self.be.UniqeOperation(ds)

            # Params refers to single dict.
            # Parameters to tuple of dict for executemany.
            for params in parameters:
                q = self.be.UniqeQuery(query, timeout)
                q.add_parameters(params)
                q.add_parameter('PyUber_DATASOURCE', ds) if (
                    'MIDAS' not in ds
                    and 'FTP' not in ds
                    and 'ELASTIC' not in ds
                ) else None
                operation.add_query(q)
            yield operation

    # make the cursor ready to read data from it
    def _activate(self):
        t = self._uniqeTables[0]
        logger.info("Activating cursor for %d IUberTables",
                    len(self._uniqeTables))

        try:
            self._columncount = t.column_count
        except self.be.APIException as e:
            raise DatabaseError(self.be.apiexmsg(e))
        logger.info("ColumnCount done")

        self._description = [(c.Name, (c.TypeCodeInt, c.TypeName))
                             for c in t.columns()]  # build description field
        self._rowstream = self._rowstreamer()
        # _make_row will convert raw rows to user-visible rows
        self._make_row = self.row_factory(self._description,
                                          self.be.apidt2pydt)
        self._active = True

    # generator to fetch chunks from IUberTables and yield rows one-at-a-time
    def _rowstreamer(self):
        self._rownumber = 0
        for t in self._uniqeTables:
            for row in t:
                self._rownumber += 1
                yield row

    @check_active
    def fetchone(self):
        return next(self, None)

    @check_active
    def fetchmany(self, size=None):
        size = size or self.arraysize
        return list(map(self._make_row, islice(self._rowstream, size)))

    @check_active
    def fetchall(self):
        return list(map(self._make_row, self._rowstream))

    @check_active
    def __next__(self):
        return self._make_row(next(self._rowstream))

    next = __next__

    def __iter__(self):
        return self

    @check_active
    def to_csv(self, fn=None, headers=True, sep=',',
               dateformat='yyyy-MM-ddTHH:mm:ss', append=False):
        # file output starts with the next chunk
        if self._rownumber:
            raise ProgrammingError("CSV output would skip first %d rows of "
                                   "result set" % self._rownumber)
        if fn is None:
            f = NamedTemporaryFile(prefix='PyUber_', suffix='.csv',
                                   delete=False)
            f.close()
            fn = f.name
        try:
            for t in self._uniqeTables:
                t.saveToFile(fn, sep, dateformat, append, not headers)
                # concat tables, suppress headers after first
                append, headers = True, False
        except self.be.APIException as e:
            raise DatabaseError(self.be.apiexmsg(e))
        return fn


class Connection(object):
    def __init__(self, connstr=None, datasource=None, row_factory=Row,
                 backend=None, **kwargs):
        self.be = backend
        self.helper = self.be.UniqeClientHelper()
        self.datasource = datasource
        self.row_factory = row_factory

        # set attributes specified via connection string, then keyword params
        attrs = [] if connstr is None else [('ConnectionString', connstr)]
        attrs += kwargs.items()
        for k, v in attrs:
            try:
                setattr(self.helper, k, v)
            # TODO: Should only be APIException
            except (self.be.APIException, AttributeError, TypeError):
                raise ProgrammingError("connection setting rejected by UBER: "
                                       "%s=%s" % (k, repr(v)))

        if self.datasource is None:
            # after this we IGNORE helper.DataSource
            self.datasource = self.helper.DataSource
        elif self.helper.DataSource is not None:
            raise ProgrammingError("datasource double-specified")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def cursor(self, datasource=None, row_factory=None, timeout=None):
        row_factory = row_factory or self.row_factory
        datasource = datasource or self.datasource
        timeout = timeout or self.helper.timeout
        return Cursor(self, datasource, timeout=timeout,
                      row_factory=row_factory, backend=self.be)

    def execute(self, query, parameters=None, datasource=None,
                row_factory=None, timeout=None, **kwargs):
        c = self.cursor(datasource, row_factory, timeout)
        c.execute(query, parameters, **kwargs)
        return c

    def executemany(self, query, parameters=None, datasource=None,
                    row_factory=None, timeout=None, **kwargs):
        c = self.cursor(datasource, row_factory, timeout)
        c.executemany(query, parameters, **kwargs)
        return c

    def rollback(self):
        pass

    def commit(self):
        pass

    def close(self):
        pass

    def __del__(self):
        pass


def connect(connstr=None, row_factory=Row, timeout=None, backend=None,
            **kwargs):
    """Create a connection to the Uber database (underlying object is
    Intel.FabAuto.ESFW.DS.UBER.UniqeClientHelper).

    connstr = UniqeClientHelper connection string, or string/tuple datasource
        for backwards-compatibility
    kwargs = connection string parameters
    timeout = same as TimeOutInSeconds parameter (backwards-compatibility)
    row_factory = default is PiUber.Row, can use PiUber.NamedTupleRow as well

    Connection string parameters may be specified either as string, or by
    keyword parameters, e.g.:
        connect('Site=BEST;Application=Test;TimeOutInSeconds=360')
        connect(Site='BEST', Application='Test', TimeOutInSeconds=360)

    Data source for Uber queries may be arbitrarily chosen for every query, but
    a default may be specified for the connection or cursor using the
    DataSource parameter:
        connect('Site=BEST;DataSource=D1D_PROD_MAO;Application=Test')

    For compatibility with previous version of PiUber, single or multiple
    default datasources may also be specified with a string or tuple as the
    first parameter:
        connect('D1D_PROD_MAO', Site='BEST', Application='Test')
        connect(('D1D_PROD_MAO','D1C_PROD_MAO'), Site='BEST')

    Connection string parameters (see README_ConnectionStringParams.txt in
    Uber distribution for latest updates):
        Application (string): Application name used to identify to
            UNIQE server with
        Authentication (AuthMode): User Authentication Mode (IWA, UNP
            or UPWD)
        ChunkSizeInBytes (int): Chunk size in bytes for each chunk of
            data sent by server
        DataAccessor (string): Data accessor to use on the server side
            when executing the query (e.g., default, ODP, SQL,
            DevArtODP)
        DataSource (string): UNIQE data source to query
        DumpSQL (bool): Dump SQLs to log file before executing
        EnableCompression (bool): Enable compression for data returned
            by server
        EnableSequentialModeForWrites (bool, default='true'): Enable
            sequential mode for writes
        EnableTransactionModeForWrites (bool, default='true'): Enable
            transaction mode for Writes
        EnableWrites (bool, default='false'): Enable write support for
            the data-source
        GetSchemaTable (bool, default='false'): Get only the schema
            table for the output query table
        IgnoreOrderBy (bool): Ignore order by/group by when splitting
            query
        MaxNumOfChildThreads (int): Maximum number of child threads
            for query splitting
        MetaData (string): Client-side meta-data
        MinThresholdPeriodInSecondsForQueryBreakUp (long,
            default='604800'): Minimum number of seconds for breaking
            date-time range in queries
        Password (string, default=''): User password for UPWD
            authentication
        Site (string, default=''): Default UNIQE Server to connect to
            (leave it empty or BEST to auto-route)
        TimeOutInSeconds (int, default='7200'): Transaction time-out
            in seconds
        UserId (string, default=''): User ID for authentication"""

    # Before checking arguments, verify valid backend is available
    backend = get_backend(backend)

    # backwards-compatibility for explicit timeout parameter
    if timeout is not None and 'TimeOutInSeconds' in kwargs:
        raise ProgrammingError("timeout specified twice with `timeout` and "
                               "`TimeOutInSeconds` keyword arguments.")
    if timeout is not None:
        kwargs['TimeOutInSeconds'] = timeout

    if 'DataSource' in kwargs and 'datasource' in kwargs:
        raise ProgrammingError("Double specified datasource by using both "
                               "`DataSource` and `datasource` keywords.")

    datasource = kwargs.pop('datasource', None)
    datasource = kwargs.pop('DataSource', None) or datasource

    # backwards-compatibility for datasource as first parameter
    # check datasources as an iterable. ie, lists, tuples
    if (isinstance(connstr, (list, tuple))
        or (isinstance(connstr, string_types) and '=' not in connstr)
    ):
        if datasource is not None:
            raise ProgrammingError("Double specified datasource by using both "
                                   "Positional and Keyword argument.")
        datasource = connstr
        connstr = None

    return Connection(connstr, datasource, row_factory, backend, **kwargs)
