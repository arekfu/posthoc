# coding: utf-8

import numpy as np
import copy
import warnings
import logging

# set up logging
logger = logging.getLogger(__name__)

tolerance = None
dtype = float

class Result:
    def __init__(self, edges=None, contents=None, errors=None, xerrors=None):
        self.edges=edges
        self.contents=contents
        self.errors=errors
        self.xerrors=xerrors

    def __str__(self):
        return '(' \
                + str(self.edges) + ', ' \
                + str(self.contents) + ', ' \
                + str(self.errors) + ', ' \
                + str(self.xerrors) + ')'

    def __repr__(self):
        return str(self)

    def _check_consistency_edges(self, other):
        try:
            diff = np.abs(self.edges - other.edges)
        except ValueError:
            raise Exception('ResultTuple edges have different sizes.')
        if tolerance:
            tol = tolerance
        else:
            tol = 10. * np.maximum(
                np.finfo(self.edges.dtype).eps,
                np.finfo(other.edges.dtype).eps
                )
        if np.amax(diff)>tol:
            raise Exception('ResultTuples have incompatible edges: ' + str(diff))

        if self.xerrors is None or other.xerrors is None:
            return

        try:
            diff = np.abs(self.xerrors - other.xerrors)
        except ValueError:
            raise Exception('ResultTuple xerrors have different sizes.')
        if np.amax(diff)>tol:
            raise Exception('ResultTuple have incompatible xerrors.')

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

    def __getitem__(self, key):
        edges = self.edges[key]
        contents = self.contents[key]
        errors = self.errors[key] if not self.errors is None else None
        xerrors = self.xerrors[key] if not self.xerrors is None else None
        return Result(edges=edges, contents=contents, errors=errors, xerrors=xerrors)

    def rebin(self, nbins, mean=True):
        n = len(self.edges)
        n1 = n-1
        edges = self.edges[::nbins]
        if mean:
            contents = self.contents[:-1].reshape(n1//nbins, nbins).mean(axis=1)
        else:
            contents = self.contents[:-1].reshape(n1//nbins, nbins).sum(axis=1)
        contents = np.append(contents, [dtype(0)])

        if not self.xerrors is None:
            if mean:
                xerrors = np.sqrt((self.xerrors[:-1].reshape(n1//nbins, nbins)**2).mean(axis=1))
            else:
                xerrors = np.sqrt((self.xerrors[:-1].reshape(n1//nbins, nbins)**2).sum(axis=1))
            xerrors = np.append(xerrors, [dtype(0)])
        else:
            xerrors = None

        if not self.errors is None:
            if mean:
                errors = np.sqrt((self.errors[:-1].reshape(n1//nbins, nbins)**2).mean(axis=1))
            else:
                errors = np.sqrt((self.errors[:-1].reshape(n1//nbins, nbins)**2).sum(axis=1))
            errors = np.append(errors, [dtype(0)])
        else:
            errors = None

        return Result(edges=edges, contents=contents, errors=errors, xerrors=xerrors)

    def rescale_x(self, factor, rescale_y=True):
        """Apply a scale factor to the bin edges (and xerrors, if present).

        Arguments:
        factor -- the factor

        Keyword arguments:
        rescale_y: if True, apply 1/factor to contents and errors.
        """

        edges = self.edges * factor
        xerrors = self.xerrors * factor if not self.xerrors is None else None
        if rescale_y:
            contents = self.contents / factor
            errors = self.errors / factor if not self.errors is None else None

        new_result = Result(edges=edges, contents=contents, errors=errors, xerrors=xerrors)
        logger.debug('rescale_x: new result is %s', new_result)
        return new_result

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
        grid = np.fromstring(gridxml.string, sep=' ', dtype=dtype)
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
        score_div_value_str = score.gelement_def['div_value']
        if score_div_value_str:
            score_div_value = dtype(score_div_value_str)
        else:
            score_div_value = None
        grid = self.grid(score_grid_name)
        score_id = score['id']
        results = self.batch_results_xml(batch_num)
        resultxml = results.find('result', scoreid=score_id).gelement
        result = np.fromstring(resultxml.string, sep=' ', dtype=dtype)
        # divide by the bin width if requested
        if divide_by_bin:
            width = np.ediff1d(grid)
            result /= width
        # divide by the value in the XML tree
        if score_div_value:
            result /= score_div_value
        result = np.append(result, [dtype(0)])
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
        score_div_value_str = score.gelement_def['div_value']
        if score_div_value_str:
            score_div_value = dtype(score_div_value_str)
        else:
            score_div_value = None
        grid = self.grid(score_grid_name)
        score_id = score['id']
        results = self.mean_results_xml(batch_num)
        resultxml = results.find('mean_result', scoreid=score_id).gelement
        val_list = [ dtype(v.string) for v in resultxml.find_all('val') ]
        sd_list = [ dtype(v.string) for v in resultxml.find_all('sd') ]
        val = np.array(val_list, dtype=dtype)
        sd = np.array(sd_list, dtype=dtype)
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
        val = np.append(val, [dtype(0)])
        sd = np.append(sd, [dtype(0)])
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

class TXTResult(object):
    def __init__(self, file_name, parser):
        self.file_name = file_name
        self.parser = parser

    def result(self):
        xs = list()
        ys = list()
        eys = list()
        exs = list()
        n_tokens = None
        with open(self.file_name) as f:
            for line in f:
                parsed = self.parser(line)

                logger.debug('Parsed line\n%s as %s', line, parsed)

                if not parsed:
                    continue

                if n_tokens==None:
                    n_tokens = len(parsed)

                if len(parsed)!=n_tokens:
                    raise Exception('Inconsistent number of fields (expected ' +
                            str(n_tokens) + ') returned when parsing' +
                            self.file_name + '\nThe problematic line was ' +
                            line)

                if n_tokens==2:
                    x, y = parsed
                elif n_tokens==3:
                    x, y, ey = parsed
                    eys += [ey]
                elif n_tokens==4:
                    x, y, ey, ex = parsed
                    eys += [ey]
                    exs += [ex]

                xs += [x]
                ys += [y]

        if len(xs) != len(ys) or (eys and len(ys)!=len(eys)) or (exs and len(exs)!=len(xs)):
            raise Exception('Inconsistent lengths of x/y/ey/ex arrays')

        logger.debug('Parsing succeeded')
        logger.debug('xs=%s', xs)
        logger.debug('ys=%s', ys)
        logger.debug('exs=%s', exs)
        logger.debug('eys=%s', eys)

        xarr = np.array(xs)
        yarr = np.array(ys)
        eyarr = np.array(eys) if eys else None
        exarr = np.array(exs) if exs else None
        result = Result(
                edges=xarr,
                contents=yarr,
                errors=eyarr,
                xerrors=exarr
                )
        return result

