# coding: utf-8

from __future__ import division
import logging
from collections import Mapping

from ..results.root import ROOTResult
from .datasource import DataSource, SourceError


# set up logging
LOGGER = logging.getLogger(__name__)


_ROOT_RESULT_CACHE = {}


class ROOTHistoDataSource(DataSource):
    """Represents a ROOT histogram in a file as a data source."""

    def __init__(self, file_name, histo_name, label=None, divide_by_bin=False, **options):
        """Initialize the data source from a ROOT histogram.

        Arguments:
        file_name -- name of the .root file (string).
        histo_name -- name of the histogram (string)

        Keyword arguments:
        label -- a label for the data source
                 size.
        divide_by_bin -- whether the score result should be divided by the bin
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
            if (file_name, histo_name) in _ROOT_RESULT_CACHE:
                LOGGER.debug('Using cached ROOTResult object for %s',
                             file_name)
                root_result = _ROOT_RESULT_CACHE[file_name, histo_name]
            else:
                LOGGER.debug('Trying to open %s as a ROOTResult', file_name)
                root_result = ROOTResult(file_name, histo_name)
                _ROOT_RESULT_CACHE[file_name, histo_name] = root_result
        except IOError as e:
            LOGGER.error('Fail: could not open %s as a ROOTResult: %s',
                         file_name, e.args)
            self.null()
        else:
            LOGGER.debug('Success: opened %s as a ROOTResult', file_name)
            self.result = root_result.result()

            if divide_by_bin:
                self.result.divide_by_bin_size()

            self.xlabel, self.ylabel = root_result.labels()

            self.label = label if label else histo_name


class ROOTTreeDataSource(DataSource):
    """Represents a ROOT tree in a file as a data source."""

    def __init__(self, file_name, tree_name, var, cut='', label=None,
            divide_by_bin=True, bins=None, **options):
        """Initialize the data source from a ROOT tree.

        Arguments:
        file_name -- name of the .root file (string).
        tree_name -- name of the tree (string)
        var -- the variable to plot in the histogram

        Keyword arguments:
        cut -- the cut to apply
        label -- a label for the data source
                 size.
        divide_by_bin -- whether the score result should be divided by the bin
                         size.
        bins -- a 4-tuple containing (nx, xmin, xmax, log), where log is a
                boolean
        options -- any additional options (used for plotting).
        """

        if not isinstance(file_name, str) or not isinstance(tree_name, str):
            raise SourceError('File name and tree name for '
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
            if (file_name, tree_name) in _ROOT_RESULT_CACHE:
                LOGGER.debug('Using cached ROOTResult object for %s',
                             file_name)
                root_result = _ROOT_RESULT_CACHE[file_name, tree_name]
            else:
                LOGGER.debug('Trying to open %s as a ROOTResult', file_name)
                root_result = ROOTResult(file_name, tree_name, var, cut, bins)
                _ROOT_RESULT_CACHE[file_name, tree_name] = root_result
        except IOError as e:
            LOGGER.error('Fail: could not open %s as a ROOTResult: %s',
                         file_name, e.args)
            self.null()
        else:
            LOGGER.debug('Success: opened %s as a ROOTResult', file_name)
            self.result = root_result.result()

            if divide_by_bin:
                self.result.divide_by_bin_size()

            self.xlabel, self.ylabel = root_result.labels()

            self.label = label if label else tree_name
