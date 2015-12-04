# coding: utf-8

from collections import Mapping
import logging
import numpy as np

from ..results.result import Result
from .datasource import DataSource, SourceError

# set up logging
logger = logging.getLogger(__name__)


class ConstDataSource(DataSource):
    """Represents a constant as a data source."""

    def __init__(
            self,
            edges,
            c,
            xlabel=None,
            ylabel=None,
            label=None,
            **options):
        """Set the datasource to a constant

        Arguments:
        edges -- bin edges as a numpy array
        c -- the constant value

        Keyword arguments:
        xlabel -- label for the x-axis
        ylabel -- label for the y-axis
        label -- label for the data source
        options -- any additional options (used for plotting)
        """

        if options:
            if isinstance(options, Mapping):
                self.kwargs = options.copy()
            else:
                raise SourceError('The options argument must be a '
                                  'dictionary-like object')
        else:
            self.kwargs = {}

        self.xlabel = xlabel
        self.ylabel = ylabel
        self.label = label

        # We create the Result object
        self.result = Result(
            edges=edges,
            contents=np.full_like(edges, c)
            )
