# coding: utf-8

import logging

import numpy as np
from bs4 import BeautifulSoup

from .result import Result, DTYPE

# set up logging
logger = logging.getLogger(__name__)


class T4XMLResult(object):
    """Extract data from the Tripoli-4® output file.

    This class is responsible for extracting the calculation results, grids,
    scores and responses from the Tripoli-4® XML output file.
    """

    def __init__(self, fname):
        """Initialize the instance from the XML file 'fname'.

        Arguments:
        fname -- the name of the XML file.
        """
        with open(fname) as f:
            self.soup = BeautifulSoup(f.read(), 'lxml')

    def _list_from_iterable_attr(self, iterable, attr):
        return [s[attr] for s in iterable]

    def xgrids_xml(self):
        for gridxml in self.soup.list_decoupage.find_all('decoupage',
                                                         recursive=False):
            yield gridxml

    def grids_xml(self):
        return self.soup.list_decoupage.find_all('decoupage', recursive=False)

    def grid_xml(self, **kwargs):
        return self.soup.list_decoupage.find('decoupage',
                                             recursive=False, attrs=kwargs)

    def grid(self, name):
        """Return the specified grid as a numpy array.

        Arguments:
        name -- the name of the grid
        """
        gridxml = self.grid_xml(name=name)
        grid = np.fromstring(gridxml.string, sep=' ', dtype=DTYPE)
        return grid

    def grid_names(self):
        """Return the names of all defined grids, as a list."""
        return self._list_from_iterable_attr(self.xgrids_xml(), 'name')

    def xscores_xml(self):
        for scorexml in self.soup.scores_definition.find_all('score',
                                                             recursive=False):
            yield scorexml

    def scores_xml(self):
        return self.soup.scores_definition.find_all('score', recursive=False)

    def score_names(self):
        """Return the names of all defined scores, as a list."""
        return self._list_from_iterable_attr(self.xscores_xml(), 'name')

    def score_xml(self, **kwargs):
        score = self.soup.scores_definition.find('score',
                                                 recursive=False, attrs=kwargs)
        return score

    def xresponses_xml(self):
        for responsexml in (self.soup.response_definition.find_all('response',
                            recursive=False)):
            yield responsexml

    def responses_xml(self):
        return self.soup.response_definition.find_all('response',
                                                      recursive=False)

    def response_xml(self, **kwargs):
        response = self.soup.response_definition.find('response',
                                                      recursive=False,
                                                      attrs=kwargs)
        return response

    def response_names(self):
        """Return the names of all defined responses, as a list."""
        return self._list_from_iterable_attr(self.xresponses_xml(), 'name')

    def batch_results_xml(self, batch_num):
        if isinstance(batch_num, int):
            results = self.soup.batches.find('batch',
                                             recursive=False, num=batch_num)
            return results
        else:
            raise ValueError("argument batch_num to "
                             "T4XMLResult.batch_results_xml must be 'last' or "
                             "a batch number (int)")

    def batch_result(self, score_name, batch_num, region_id=1,
                     divide_by_bin=True):
        """Return the result for a given score in a given batch.

        Arguments:
        score_name -- name of the score (as a string)
        batch_num -- the number of the batch.

        Keyword arguments:
        region_id -- the ID of the score region
        divide_by_bin -- whether the score result should be divided by the bin
        size.

        Return value:
        a NamedTuple containing two numpy arrays: the lower bin edges (edges)
        and the bin contents (contents). The third (errors) and fourth
        (xerrors) tuple elements are set to None.
        """
        if not isinstance(score_name, str):
            raise ValueError('argument score_name to T4XMLResult.batch_result '
                             'must be a string')
        score = self.score_xml(name=score_name)
        if not score:
            raise ValueError('argument score_name to T4XMLResult.batch_result '
                             'must be the name of a score')
        score_grid_name = score['nrj_dec']
        gelement_def = score.find('gelement_def', id=region_id)
        score_div_value_str = gelement_def['div_value']
        if score_div_value_str:
            score_div_value = DTYPE(score_div_value_str)
        else:
            score_div_value = None
        grid = self.grid(score_grid_name)
        score_id = score['id']
        results = self.batch_results_xml(batch_num)
        resultxml = (results.find('result', scoreid=score_id)
                     .find('gelement', id=region_id))
        result = np.fromstring(resultxml.string, sep=' ', dtype=DTYPE)
        # divide by the bin width if requested
        if divide_by_bin:
            width = np.ediff1d(grid)
            result /= width
        # divide by the value in the XML tree
        if score_div_value:
            result /= score_div_value
        result = np.append(result, [DTYPE(0)])
        return Result(edges=grid, contents=result, errors=None, xerrors=None)

    def mean_results_xml(self, batch_num='last'):
        if batch_num == 'last':
            results = self.soup.batches.find_all('mean_results',
                                                 recursive=False)[-1]
        elif isinstance(batch_num, int):
            results = self.soup.batches.find('mean_results', recursive=False,
                                             batchnum=batch_num)
        else:
            raise ValueError("argument batch_num to "
                             "T4XMLResult.mean_results_xml must be 'last' or "
                             "a batch number (int)")
        return results

    def mean_result(self, score_name, batch_num='last', region_id=1,
                    divide_by_bin=True):
        """Return the mean result for a given score.

        Arguments:
        score_name -- name of the score (as a string)

        Keyword arguments:
        batch_num -- results will be presented for the specified batch. Can be
                     an integer, in which case it is interpreted as a batch
                     number, or 'last'.
        region_id -- the ID of the score region
        divide_by_bin -- whether the score result should be divided by the bin
                         size.

        Return value:
        a NamedTuple containing three numpy arrays: the lower bin edges
        (edges), the bin contents (contents) and the standard deviations on the
        bin contents (errors). The x errors member (xerrors) is set to None.
        """

        if not isinstance(score_name, str):
            raise ValueError('argument score_name to T4XMLResult.mean_result '
                             'must be a string')
        score = self.score_xml(name=score_name)
        if not score:
            raise ValueError('argument score_name to T4XMLResult.mean_result '
                             'must be the name of a score')
        score_grid_name = score['nrj_dec']
        gelement_def = score.find('gelement_def', id=region_id)
        score_div_value_str = gelement_def['div_value']
        if score_div_value_str:
            score_div_value = DTYPE(score_div_value_str)
        else:
            score_div_value = None
        grid = self.grid(score_grid_name)
        score_id = score['id']
        results = self.mean_results_xml(batch_num)
        resultxml = (results.find('mean_result', scoreid=score_id)
                     .find('gelement', id=region_id))
        val_list = [DTYPE(v.string) for v in resultxml.find_all('val')]
        sd_list = [DTYPE(v.string) for v in resultxml.find_all('sd')]
        val = np.array(val_list, dtype=DTYPE)
        sd = np.array(sd_list, dtype=DTYPE)
        # divide by the bin width if requested
        self.divide_by_bin = divide_by_bin
        if self.divide_by_bin:
            width = np.ediff1d(grid)
            val /= width
            sd /= width
        # divide by the value in the XML tree
        if score_div_value:
            val /= score_div_value
            sd /= score_div_value
        val = np.append(val, [DTYPE(0)])
        sd = np.append(sd, [DTYPE(0)])
        return Result(edges=grid, contents=val, errors=sd, xerrors=None)

    def labels(self, score_name):
        """Suggest axis labels for the given score."""

        score = self.score_xml(name=score_name)
        response_id = score['response_id']
        response = self.response_xml(id=response_id)
        particle = response['particle'].lower()
        response_type = response['type'].lower()
        score_div_value_str = score.gelement_def['div_value']
        unit = 'source'
        if score_div_value_str:
            unit += ' cm$^2$'
        if self.divide_by_bin:
            unit += ' MeV'
        if ' ' in unit:
            unit = '[1/(' + unit + ')]'
        else:
            unit = '[1/' + unit + ']'
        ylabel = particle + ' ' + response_type + ' ' + unit
        if 'tps_dec' in score.attrs:
            xlabel = 'time'
        elif 'mu_dec' in score.attrs:
            xlabel = '$\mu$'
        else:
            xlabel = 'energy [MeV]'
        return xlabel, ylabel
