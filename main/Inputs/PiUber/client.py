# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import logging
import os

logger = logging.getLogger(__name__)

try:
    from ._uCLR import UniqeClientHelper
except ImportError:
    from ._win32com import UniqeClientHelper


class FtpClient(object):
    """Client wrapper to hold `Uber` instance for FTP access

    Python wrapper for `Uber` using `pythonnet` `CLR` protocol to interact with
    the `Uber` object and access it methods.

    Attributes
    ----------
    path : str
        Relative or absolute path where the files are going to be downloaded to
        in the local space. This directory will be scanned to check if files
        were previously downloaded.
    _helper : UniqeClientHelper
        CLR representation of the Intel Uber libraries used to access the
        databases and FTP into the fileservers.
    """

    def __init__(self, path=None):
        """Create new FTP Client

        A new private UniqeClient Helper is created for each client. Though all
        the work can done with only one client, do not want to restrict the
        user from the possibilities.

        Note
        ----
        Do not include the `self` parameter in the ``Parameters`` section.

        Parameters
        ----------
        path : str
            User provided path for storing the downloaded files from the
            fileserver. If no path is provided a warning is raised that we are
            going to default to the current working directory (cwd).
        """
        # Not going to fully configure helper with datasource
        # Following PiUber conventions
        logger.debug("Initializing FTP Client")
        self.path = path or os.getcwd()
        self._helper = UniqeClientHelper()

        if not path:
            logger.warning("No path given, using %s", self.path)

    def download(self, files, filesource):
        """Download files from `Uber` enabled FTP fileserver

        Downloads file or files from the fileserver after verifying that
        it isn't located in the user provided path.

        Parameters
        ----------
        files : str or list of str
            Remote fileserver path where files are located. Can be taken as a
            string or a list of strings that will all be downloaded from the
            same fileserver
        filesource : str
            Name of fileserver to connect to and download the files from.

        Returns
        -------
        list of dict
            returns a list filled with dictionaries containing remote and
            local filepaths and filename for the input files.

                [{
                    'local_path': str,
                    'remote_path': str,
                    'filename': str,
                }, ...]
        """

        # Make it so that locations can be either a list or str
        if isinstance(files, str):
            files = (files,)

        remote = ','.join([str(x) for x in files
                           if not os.path.exists(
                os.path.join(self.path, os.path.basename(x)))])

        if not remote:
            logger.warning("All files found locally")
        else:
            logger.info("Downloading files")
            self._helper.download(filesource, remote, self.path, False)

        return [{'local_path': os.path.join(self.path, os.path.basename(x)),
                 'filename': os.path.basename(x),
                 'remote_path': x} for x in files]
