#!/usr/bin/env python
# coding: utf-8

import numpy as np
from collections import namedtuple

class XMLResult:
    """Extract data from the Tripoli-4® output file.

    This class is responsible for extracting the calculation results, grids,
    scores and responses from the Tripoli-4® XML output file.
    """

    def __init__(self, fname):
        """Initialize the instance from the XML file 'fname'.

        Arguments:
        fname -- the name of the XML file.
        """
        from bs4 import BeautifulSoup
        with open(fname) as f:
            self.soup = BeautifulSoup(f.read(), 'lxml')
        self.dtype = float
        self.BatchResultTuple = namedtuple('BatchResult', ['edges', 'contents', 'widths'])
        self.MeanResultTuple = namedtuple('MeanResult', ['edges', 'contents', 'errors', 'widths'])

    def _list_from_iterable_attr(self, iterable, attr):
        return [ s[attr] for s in iterable ]

    def xgrids_xml(self):
        for gridxml in self.soup.list_decoupage.find_all('decoupage', recursive=False):
            yield gridxml

    def grids_xml(self):
        return self.soup.list_decoupage.find_all('decoupage', recursive=False)

    def grid_xml(self, name):
        return self.soup.list_decoupage.find('decoupage', recursive=False, attrs={'name': name})

    def grid(self, name):
        """Return the specified grid as a numpy array.

        Arguments:
        name -- the name of the grid
        """
        gridxml = self.grid_xml(name)
        grid = np.fromstring(gridxml.string, sep=' ', dtype=self.dtype)
        return grid

    def grid_names(self):
        """Return the names of all defined grids, as a list."""
        return self._list_from_iterable_attr(self.xgrids_xml(), 'name')

    def xscores_xml(self):
        for scorexml in self.soup.scores_definition.find_all('score', recursive=False):
            yield scorexml

    def scores_xml(self):
        return self.soup.scores_definition.find_all('score', recursive=False)

    def score_names(self):
        """Return the names of all defined scores, as a list."""
        return self._list_from_iterable_attr(self.xscores_xml(), 'name')

    def score_xml(self, name):
        score = self.soup.scores_definition.find('score', recursive=False, attrs={'name': name})
        return score

    def xresponses_xml(self):
        for responsexml in self.soup.response_definition.find_all('response', recursive=False):
            yield responsexml

    def responses_xml(self):
        return self.soup.response_definition.find_all('response', recursive=False)

    def response_xml(self, name):
        response = self.soup.response_definition.find('response', recursive=False, attrs={'name': name})
        return response

    def response_names(self):
        """Return the names of all defined responses, as a list."""
        return self._list_from_iterable_attr(self.xresponses_xml(), 'name')

    def batch_results_xml(self, batch_num):
        if isinstance(batch_num, int):
            results = self.soup.batches.find('batch', recursive=False, num=batch_num)
            return results
        else:
            raise ValueError("argument batch_num to XMLResult.batch_results_xml must be 'last' or a batch number (int)")

    def batch_result(self, score_name, batch_num, divide_by_bin=True):
        """Return the result for a given score in a given batch.

        Arguments:
        score_name -- name of the score (as a string)
        batch_num -- the number of the batch.

        Keyword arguments:
        divide_by_bin -- whether the score result should be divided by the bin
        size.
        """
        if not isinstance(score_name,str):
            raise ValueError('argument score_name to XMLResult.batch_result must be a string')
        score = self.score(score_name)
        if not score:
            raise ValueError('argument score_name to XMLResult.batch_result must be the name of a score')
        score_grid_name = score['nrj_dec']
        grid = self.grid(score_grid_name)
        score_id = score['id']
        results = self.batch_results_xml(batch_num)
        resultxml = results.find('result', scoreid=score_id).gelement
        result = np.fromstring(resultxml.string, sep=' ', dtype=self.dtype)
        # divide by the bin width if requested
        width = np.ediff1d(grid)
        if divide_by_bin:
            result /= width
        left = grid[:-1]
        return self.BatchResultTuple(edges=left, contents=result, widths=width)

    def mean_results_xml(self, batch_num='last'):
        if batch_num=='last':
            results = self.soup.batches.find_all('mean_results', recursive=False)[-1]
        elif isinstance(batch_num, int):
            results = self.soup.batches.find('mean_results', recursive=False, batchnum=batch_num)
        else:
            raise ValueError("argument batch_num to XMLResult.mean_results_xml must be 'last' or a batch number (int)")
        return results

    def mean_result(self, score_name, batch_num='last', divide_by_bin=True):
        """Return the mean result for a given score.

        Arguments:
        score_name -- name of the score (as a string)

        Keyword arguments:
        batch_num -- results will be presented for the specified batch. Can be
        an integer, in which case it is interpreted as a batch number, or
        'last'.
        divide_by_bin -- whether the score result should be divided by the bin
        size.
        """
        if not isinstance(score_name,str):
            raise ValueError('argument score_name to XMLResult.mean_result must be a string')
        score = self.score(score_name)
        if not score:
            raise ValueError('argument score_name to XMLResult.mean_result must be the name of a score')
        score_grid_name = score['nrj_dec']
        grid = self.grid(score_grid_name)
        score_id = score['id']
        results = self.mean_results_xml(batch_num)
        resultxml = results.find('mean_result', scoreid=score_id).gelement
        val_list = [ self.dtype(v.string) for v in resultxml.find_all('val') ]
        sd_list = [ self.dtype(v.string) for v in resultxml.find_all('sd') ]
        val = np.array(val_list, dtype=self.dtype)
        sd = np.array(sd_list, dtype=self.dtype)
        # divide by the bin width if requested
        width = np.ediff1d(grid)
        if divide_by_bin:
            val /= width
            sd /= width
        left = grid[:-1]
        return self.MeanResultTuple(edges=left, contents=val, widths=width, errors=sd)

