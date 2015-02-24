# coding: utf-8

import numpy as np
from collections import namedtuple
import re
import copy
import warnings

ResultTuple = namedtuple('ResultTuple', ['edges', 'contents', 'errors', 'xerrors'])

class Result(ResultTuple):
    def _check_consistency_edges(self, other):
        try:
            diff = np.abs(self.edges - other.edges)
        except ValueError:
            raise SourceError('ResultTuple edges have different sizes.')
        tolerance = 10. * np.maximum(
                np.finfo(self.edges.dtype).eps,
                np.finfo(other.edges.dtype).eps
                )
        if np.amax(diff)>tolerance:
            raise SourceError('ResultTuples have incompatible edges.')

        if self.xerrors is None or other.xerrors is None:
            return

        try:
            diff = np.abs(self.xerrors - other.xerrors)
        except ValueError:
            raise SourceError('ResultTuple xerrors have different sizes.')
        if np.amax(diff)>tolerance:
            raise SourceError('ResultTuple have incompatible xerrors.')

    def __add__(self, other):
        self._check_consistency_edges(other)
        edges = copy.deepcopy(self.edges)
        xerrors = copy.deepcopy(self.xerrors)
        contents = self.contents + other.contents
        if not self.errors is None and not other.errors is None:
            errors = np.sqrt(self.errors**2 + other.errors**2)
        elif not other.errors is None:
            errors = copy.deepcopy(other.errors)
        else:
            errors = copy.deepcopy(self.errors)
        return Result(edges, contents, errors, xerrors)

    def __sub__(self, other):
        self._check_consistency_edges(other)
        edges = copy.deepcopy(self.edges)
        xerrors = copy.deepcopy(self.xerrors)
        contents = self.contents - other.contents
        if not self.errors is None and not other.errors is None:
            errors = np.sqrt(self.errors**2 + other.errors**2)
        elif not other.errors is None:
            errors = copy.deepcopy(other.errors)
        else:
            errors = copy.deepcopy(self.errors)
        return Result(edges, contents, errors, xerrors)

    def __mul__(self, other):
        self._check_consistency_edges(other)
        edges = copy.deepcopy(self.edges)
        xerrors = copy.deepcopy(self.xerrors)
        contents = self.contents * other.contents
        if not self.errors is None and not other.errors is None:
            errors = np.sqrt((self.contents*other.errors)**2 + (self.errors*other.contents)**2)
        elif not other.errors is None:
            errors = self.contents*other.errors
        elif not self.errors is None:
            errors = self.errors*other.contents
        else:
            errors = None
        return Result(edges, contents, errors, xerrors)

    def __div__(self, other):
        with warnings.catch_warnings():
            # we ignore warnings from div-by-zero
            warnings.filterwarnings('ignore', 'invalid value', RuntimeWarning)

            self._check_consistency_edges(other)
            edges = copy.deepcopy(self.edges)
            xerrors = copy.deepcopy(self.xerrors)
            contents = self.contents/other.contents
            if not self.errors is None and not other.errors is None:
                errors = np.nan_to_num(
                        contents * np.sqrt((self.errors/self.contents)**2 + (other.errors/other.contents)**2)
                        )
            elif not other.errors is None:
                errors = np.nan_to_num(
                        contents * other.errors / other.contents
                        )
            elif not self.errors is None:
                errors = np.nan_to_num(
                        self.errors / other.contents
                        )
            else:
                errors = None
            return Result(edges, contents, errors, xerrors)


class XMLResult(object):
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

    def _list_from_iterable_attr(self, iterable, attr):
        return [ s[attr] for s in iterable ]

    def xgrids_xml(self):
        for gridxml in self.soup.list_decoupage.find_all('decoupage', recursive=False):
            yield gridxml

    def grids_xml(self):
        return self.soup.list_decoupage.find_all('decoupage', recursive=False)

    def grid_xml(self, **kwargs):
        return self.soup.list_decoupage.find('decoupage', recursive=False, attrs=kwargs)

    def grid(self, name):
        """Return the specified grid as a numpy array.

        Arguments:
        name -- the name of the grid
        """
        gridxml = self.grid_xml(name=name)
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

    def score_xml(self, **kwargs):
        score = self.soup.scores_definition.find('score', recursive=False, attrs=kwargs)
        return score

    def xresponses_xml(self):
        for responsexml in self.soup.response_definition.find_all('response', recursive=False):
            yield responsexml

    def responses_xml(self):
        return self.soup.response_definition.find_all('response', recursive=False)

    def response_xml(self, **kwargs):
        response = self.soup.response_definition.find('response', recursive=False, attrs=kwargs)
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

        Return value:
        a NamedTuple containing two numpy arrays: the lower bin edges (edges)
        and the bin contents (contents). The third (errors) and fourth
        (xerrors) tuple elements are set to None.
        """
        if not isinstance(score_name,str):
            raise ValueError('argument score_name to XMLResult.batch_result must be a string')
        score = self.score_xml(name=score_name)
        if not score:
            raise ValueError('argument score_name to XMLResult.batch_result must be the name of a score')
        score_grid_name = score['nrj_dec']
        grid = self.grid(score_grid_name)
        score_id = score['id']
        results = self.batch_results_xml(batch_num)
        resultxml = results.find('result', scoreid=score_id).gelement
        result = np.fromstring(resultxml.string, sep=' ', dtype=self.dtype)
        # divide by the bin width if requested
        if divide_by_bin:
            width = np.ediff1d(grid)
            result /= width
        result = np.append(result, [self.dtype(0)])
        return Result(edges=grid, contents=result, errors=None, xerrors=None)

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

        Return value:
        a NamedTuple containing three numpy arrays: the lower bin edges
        (edges), the bin contents (contents) and the standard deviations on the
        bin contents (errors). The x errors member (xerrors) is set to None.
        """
        if not isinstance(score_name,str):
            raise ValueError('argument score_name to XMLResult.mean_result must be a string')
        score = self.score_xml(name=score_name)
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
        if divide_by_bin:
            width = np.ediff1d(grid)
            val /= width
            sd /= width
        val = np.append(val, [self.dtype(0)])
        sd = np.append(sd, [self.dtype(0)])
        return Result(edges=grid, contents=val, errors=sd, xerrors=None)

    def labels(self, score_name):
        """Suggest axis labels for the given score."""

        score = self.score_xml(name=score_name)
        response_id = score['response_id']
        response = self.response_xml(id=response_id)
        particle = response['particle'].lower()
        response_type = response['type'].lower()
        ylabel = particle + ' ' + response_type
        if 'tps_dec' in score.attrs:
            xlabel = 'time'
        elif 'mu_dec' in score.attrs:
            xlabel = '$\mu$'
        else:
            xlabel = 'energy (MeV)'
        return xlabel, ylabel

class CSVResult(object):
    def __init__(self, file_name, column_spec='1:2', comment_chars='#@', delimiter_chars=' \t'):
        self.file_name = file_name
        self.column_spec = column_spec
        self.comment_chars = comment_chars
        self.delimiter_chars = delimiter_chars

        # extract column indices and verify their number
        self.column_indices = self.column_spec.split(':')
        n_indices = len(self.column_indices)
        if n_indices<2 or n_indices>4:
            raise ValueError('column_indices must contain 2, 3 or 4 indices')

    def result(self):
        xs = list()
        ys = list()
        eys = list()
        exs = list()
        with open(self.file_name) as f:
            for line in f:
                # the following line assigns to comment_index the index of the
                # first comment character encountered in the splitted string
                comment_index = next(
                        (i for (i, char) in enumerate(line) for comment_char in self.comment_chars if char==comment_char),
                        None
                        )
                non_comment = line[:comment_index]

                # split the string
                splitted = re.split(self.delimiter_chars, non_comment)

                # skip blank lines
                if not splitted:
                    continue

                try:
                    x = splitted[self.column_indices[0]]
                    y = splitted[self.column_indices[1]]
                    xs += [x]
                    ys += [y]
                    if n_indices>=3:
                        ey = splitted[self.column_indices[2]]
                        eys += [ey]
                        if n_indices==4:
                            ex = splitted[self.column_indices[3]]
                            exs += [ex]
                except IndexError as error:
                    error.args = ('Column specification out of range. Check your column_spec argument. I choked on this line:\n' + line, )
                    raise error

            if len(xs) != len(ys) or (eys and len(ys)!=len(eys)) or (exs and len(exs)!=len(xs)):
                raise Exception('Inconsistent lengths of x/y/ey/ex arrays')
            xarr = np.array(xs)
            yarr = np.array(ys)
            eyarr = np.array(eyarr) if eys else None
            exarr = np.array(exarr) if exs else None
            result = Result(
                    edges=xarr,
                    contents=yarr,
                    errors=eyarr,
                    xerrors=exarr
                    )
            return self.result

