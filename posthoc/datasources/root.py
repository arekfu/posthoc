# coding: utf-8

import logging
from collections import Mapping

from ..results.root import ROOTResult
from .datasource import DataSource, SourceError


# set up logging
LOGGER = logging.getLogger(__name__)


_ROOT_RESULT_CACHE = {}


class ROOTDataSource(DataSource):
    """Represents a ROOT output file as a data source."""

    def __init__(self, file_name, histo_name, label=None, **options):
        """Initialize the data source from a ROOT histogram.

        Arguments:
        file_name -- name of the .root file (string).
        histo_name -- name of the histogram (string)

        Keyword arguments:
        label -- a label for the data source
        size.
        options -- any additional options (used for plotting).
        """

        if not isinstance(file_name, str) or not isinstance(histo_name, str):
            raise SourceError('File name and histogram name for '
                              'ROOTDataSource must be strings.')

        if options:
            if isinstance(options, Mapping):
                self.kwargs = options.copy()
            else:
                raise SourceError('The options argument must be a '
                                  'dictionary-like object')
        else:
            self.kwargs = dict()

        # Here we hope that file_name is a valid, well-formed ROOT file
        try:
            LOGGER.debug('Trying to open %s as a ROOTResult', file_name)
            if file_name in _ROOT_RESULT_CACHE:
                LOGGER.debug('Using cached ROOTResult object for %s',
                             file_name)
                root_result = _ROOT_RESULT_CACHE[file_name]
            else:
                LOGGER.debug('Trying to open %s as a ROOTResult', file_name)
                root_result = ROOTResult(file_name)
                _ROOT_RESULT_CACHE[file_name] = root_result
        except IOError as e:
            LOGGER.error('Fail: could not open %s as a ROOTResult: %s',
                         file_name, e.args)
            self.null()
        else:
            LOGGER.debug('Success: opened %s as a ROOTResult', file_name)
            self.result = root_result.result(histo_name)

            self.xlabel, self.ylabel = root_result.labels(histo_name)

            self.label = label if label else histo_name
