# coding: utf-8

import logging
from collections import Mapping

from .datasource import DataSource, SourceError
from ..results.mcnp import MCTALResult

# set up logging
LOGGER = logging.getLogger(__name__)

_MCTAL_RESULT_CACHE = {}


class MCTALDataSource(DataSource):
    """Represents an MCNP6 MCTAL output file as a data source."""

    def __init__(self, file_name, tally_number, zone_number, label=None,
                 divide_by_bin=True, **options):
        """Initialize the data source from an MCTAL file.

        Arguments:
        file_name -- name of the .root file (string).
        tally_number -- number of the tally
        zone_number -- number of the zone

        Keyword arguments:
        label -- a label for the data source
        size.
        divide_by_bin -- whether the score result should be divided by the bin
        size.
        options -- any additional options (used for plotting).
        """

        if not isinstance(file_name, str):
            raise SourceError('File name for MCTALDataSource must be a '
                              'string.')

        if not isinstance(tally_number, int) or \
                not isinstance(zone_number, int):
            raise SourceError('Tally and zone numbers for MCTALDataSource '
                              'must be ints.')

        if options:
            if isinstance(options, Mapping):
                self.kwargs = options.copy()
            else:
                raise SourceError('The options argument must be a '
                                  'dictionary-like object')
        else:
            self.kwargs = dict()

        # Here we hope that file_name is a valid, well-formed MCTAL file
        try:
            if file_name in _MCTAL_RESULT_CACHE:
                LOGGER.debug('Using cached MCTALResult object for %s',
                             file_name)
                mctal_result = _MCTAL_RESULT_CACHE[file_name]
            else:
                LOGGER.debug('Trying to open %s as a MCTALResult', file_name)
                mctal_result = MCTALResult(file_name)
                _MCTAL_RESULT_CACHE[file_name] = mctal_result
        except IOError as e:
            LOGGER.error('Fail: could not open %s as a MCTALResult: %s',
                         file_name, e.args)
            self.null()
        else:
            LOGGER.debug('Success: opened %s as a MCTALResult', file_name)
            self.result = mctal_result.result(tally_number, zone_number)
            if divide_by_bin:
                self.result.divide_by_bin_size()

            self.xlabel, self.ylabel = mctal_result.labels(tally_number)

            self.label = label if label else mctal_result.label(tally_number)
