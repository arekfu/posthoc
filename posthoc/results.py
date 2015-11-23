# coding: utf-8

import numpy as np
import copy
import warnings
import logging
import re

try:
    import ROOT
    HAS_ROOT = True
except ImportError:
    HAS_ROOT = False

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
        if tolerance:
            tol = tolerance
        else:
            tol = 100. * np.maximum(
                np.finfo(self.edges.dtype).eps,
                np.finfo(other.edges.dtype).eps
                )

        try:
            diff = np.allclose(self.edges, other.edges, atol=tol)
        except ValueError:
            raise Exception('ResultTuple edges have different sizes.')
        if not diff:
            raise Exception('ResultTuples have incompatible edges:\ntolerance = ' + str(tol) + '\ndifferences = ' + str(diff))

        if self.xerrors is None or other.xerrors is None:
            return

        try:
            diff = np.allclose(self.xerrors, other.xerrors, atol=tol)
        except ValueError:
            raise Exception('ResultTuple xerrors have different sizes.')
        if not diff:
            raise Exception('ResultTuple have incompatible xerrors.')

    def __add__(self, other):
        edges = copy.deepcopy(self.edges)
        xerrors = copy.deepcopy(self.xerrors)
        if np.isscalar(other):
            contents = self.contents + other
            errors = copy.deepcopy(self.errors)
        else:
            self._check_consistency_edges(other)
            contents = self.contents + other.contents
            if not self.errors is None and not other.errors is None:
                errors = np.sqrt(self.errors**2 + other.errors**2)
            elif not other.errors is None:
                errors = copy.deepcopy(other.errors)
            else:
                errors = copy.deepcopy(self.errors)
        return Result(edges, contents, errors, xerrors)

    def __sub__(self, other):
        edges = copy.deepcopy(self.edges)
        xerrors = copy.deepcopy(self.xerrors)
        if np.isscalar(other):
            contents = self.contents - other
            errors = copy.deepcopy(self.errors)
        else:
            self._check_consistency_edges(other)
            contents = self.contents - other.contents
            if not self.errors is None and not other.errors is None:
                errors = np.sqrt(self.errors**2 + other.errors**2)
            elif not other.errors is None:
                errors = copy.deepcopy(other.errors)
            else:
                errors = copy.deepcopy(self.errors)
        return Result(edges, contents, errors, xerrors)

    def __mul__(self, other):
        edges = copy.deepcopy(self.edges)
        xerrors = copy.deepcopy(self.xerrors)
        if np.isscalar(other):
            contents = self.contents * other
            errors = self.errors * other
        else:
            self._check_consistency_edges(other)
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

            edges = copy.deepcopy(self.edges)
            xerrors = copy.deepcopy(self.xerrors)
            if np.isscalar(other):
                contents = self.contents / other
                errors = self.errors / other
            else:
                self._check_consistency_edges(other)
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
        self.edges = self.edges[::nbins]
        if mean:
            self.contents = self.contents[:-1].reshape(n1//nbins, nbins).mean(axis=1)
        else:
            self.contents = self.contents[:-1].reshape(n1//nbins, nbins).sum(axis=1)
        self.contents = np.append(self.contents, [dtype(0)])

        if not self.xerrors is None:
            if mean:
                self.xerrors = np.sqrt((self.xerrors[:-1].reshape(n1//nbins, nbins)**2).mean(axis=1))
            else:
                self.xerrors = np.sqrt((self.xerrors[:-1].reshape(n1//nbins, nbins)**2).sum(axis=1))
            self.xerrors = np.append(self.xerrors, [dtype(0)])

        if not self.errors is None:
            if mean:
                self.errors = np.sqrt((self.errors[:-1].reshape(n1//nbins, nbins)**2).mean(axis=1))
            else:
                self.errors = np.sqrt((self.errors[:-1].reshape(n1//nbins, nbins)**2).sum(axis=1))
            self.errors = np.append(self.errors, [dtype(0)])

        logger.debug('rebin: new result is %s', self)

    def rescale_edges(self, factor, rescale_contents=True):
        """Apply a scale factor to the bin edges (and xerrors, if present).

        Arguments:
        factor -- the factor

        Keyword arguments:
        rescale_contents: if True, apply 1/factor to contents and errors.
        """

        self.edges *= factor
        self.xerrors = self.xerrors * factor if not self.xerrors is None else None
        if rescale_contents:
            self.contents /= factor
            self.errors = self.errors / factor if not self.errors is None else None
        logger.debug('rescale_edges: new result is %s', self)

    def rescale_errors(self, factor):
        """Apply a scale factor to the bin errors."""

        self.errors = self.errors * factor if not self.errors is None else None
        logger.debug('rescale_errors: new result is %s', self)


    def append_bin(self, edge=None, content=0., error=0., xerror=0.):
        new_bin_edge = edge if edge else 2.*self.edges[-1] - self.edges[-2]
        self.edges = np.append(self.edges, new_bin_edge)
        self.contents = np.append(self.contents, content)
        if not self.errors is None:
            self.errors = np.append(self.errors, error)
        if not self.xerrors is None:
            self.xerrors = np.append(self.xerrors, error)

    def chop(self, threshold=1e-30):
        chop_indices = self.contents<threshold
        self.contents[chop_indices] = 0.
        self.errors[chop_indices] = 0.

    def divide_by_bin_size(self, pad='last'):
        bin_sizes = np.ediff1d(self.edges)
        if pad == 'first':
            bin_sizes = np.insert(bin_sizes, 0, 1.)
        elif pad == 'last':
            bin_sizes = np.insert(bin_sizes, len(bin_sizes), 1.)
        else:
            raise Exception("unrecognized 'pad' option value in divide_by_bin; must be 'first' or 'last'")
        self.contents /= bin_sizes

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
            raise ValueError("argument batch_num to T4XMLResult.batch_results_xml must be 'last' or a batch number (int)")

    def batch_result(self, score_name, batch_num, region_id=1, divide_by_bin=True):
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
        if not isinstance(score_name,str):
            raise ValueError('argument score_name to T4XMLResult.batch_result must be a string')
        score = self.score_xml(name=score_name)
        if not score:
            raise ValueError('argument score_name to T4XMLResult.batch_result must be the name of a score')
        score_grid_name = score['nrj_dec']
        gelement_def = score.find('gelement_def', id=region_id)
        score_div_value_str = gelement_def['div_value']
        if score_div_value_str:
            score_div_value = dtype(score_div_value_str)
        else:
            score_div_value = None
        grid = self.grid(score_grid_name)
        score_id = score['id']
        results = self.batch_results_xml(batch_num)
        resultxml = results.find('result', scoreid=score_id).find('gelement', id=region_id)
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
            raise ValueError("argument batch_num to T4XMLResult.mean_results_xml must be 'last' or a batch number (int)")
        return results

    def mean_result(self, score_name, batch_num='last', region_id=1, divide_by_bin=True):
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

        if not isinstance(score_name,str):
            raise ValueError('argument score_name to T4XMLResult.mean_result must be a string')
        score = self.score_xml(name=score_name)
        if not score:
            raise ValueError('argument score_name to T4XMLResult.mean_result must be the name of a score')
        score_grid_name = score['nrj_dec']
        gelement_def = score.find('gelement_def', id=region_id)
        score_div_value_str = gelement_def['div_value']
        if score_div_value_str:
            score_div_value = dtype(score_div_value_str)
        else:
            score_div_value = None
        grid = self.grid(score_grid_name)
        score_id = score['id']
        results = self.mean_results_xml(batch_num)
        resultxml = results.find('mean_result', scoreid=score_id).find('gelement', id=region_id)
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

                if n_tokens is None:
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
                    eys.append(ey)
                elif n_tokens==4:
                    x, y, ey, ex = parsed
                    eys.append(ey)
                    exs.append(ex)

                xs.append(x)
                ys.append(y)

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

if HAS_ROOT:
    class ROOTResult(object):
        def __init__(self, file_name):
            self.file_name = file_name
            self.tfile = ROOT.TFile(self.file_name)

        def result(self, histo_name):
            xs = list()
            ys = list()
            eys = list()
            exs = list()

            histo = self.tfile.Get(histo_name)

            nbins = histo.GetNbinsX()
            for i in range(nbins):
                x = histo.GetXaxis().GetBinLowEdge(i+1)
                y = histo.GetBinContent(i+1)
                ex = histo.GetXaxis().GetBinWidth(i+1)
                ey = histo.GetBinError(i+1)
                xs.append(x)
                ys.append(y)
                exs.append(ex)
                eys.append(ey)
            xs.append(histo.GetXaxis().GetBinUpEdge(nbins))
            ys.append(0)
            exs.append(0)
            eys.append(0)

            if len(xs) != len(ys) or (eys and len(ys)!=len(eys)) or (exs and len(exs)!=len(xs)):
                raise Exception('Inconsistent lengths of x/y/ey/ex arrays')

            logger.debug('ROOT import succeeded')
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

        def labels(self, histo_name):
            histo = self.tfile.Get(histo_name)
            xlabel = histo.GetXaxis().GetTitle()
            ylabel = histo.GetXaxis().GetTitle()
            return xlabel, ylabel


class MCTALResult(object):
    SEARCH_TALLY = 0
    SEARCH_F = 1
    READ_F = 2
    SEARCH_X = 3
    READ_X = 4
    SEARCH_ZONE = 5
    SEARCH_VALS = 6
    READ_VALS = 7

    def __init__(self, file_name):
        self.file_name = file_name
        self.start_dict = {}
        self.result_dict = {}
        self.parse()

    def parse(self):
        with open(self.file_name) as f:
            line = f.readline()
            while line:
                match = re.match('tally +([0-9]+)', line, re.I)
                if match:
                    tally_number = int(match.group(1))
                    logger.debug('Found tally %d', tally_number)
                    self.start_dict[tally_number] = f.tell()
                line = f.readline()

    def result(self, tally_number, zone_number):
        res = self.result_dict.get((tally_number, zone_number), None)
        if res is None:
            res = self.extract_result(tally_number, zone_number)
            self.result_dict[(tally_number, zone_number)] = res
        return res

    def extract_result(self, tally_number, zone_number):
        xs = []
        ys = []
        eys = []
        exs = []
        state = self.SEARCH_F

        last_pos = self.start_dict.get(tally_number, None)
        if last_pos is None:
            raise Exception('Could not find tally ' + str(tally_number))

        with open(self.file_name) as f:
            f.seek(last_pos)
            line = f.readline()
            while line:
                if state == self.SEARCH_F:
                    match = re.match('f +([0-9]+)', line, re.I)
                    if match:
                        n_zones = int(match.group(1))
                        if n_zones > 0:
                            logger.debug('Found %d zones', n_zones)
                            state = self.READ_F
                            zones = []
                elif state == self.READ_F:
                    # split the string
                    splitted = re.split(' +', line.strip())
                    ints = map(int, splitted)
                    logger.debug('Parsed %d ints: %s', len(ints), str(ints))
                    zones += ints
                    if len(zones) >= n_zones:
                        zone_index = zones.index(zone_number)
                        state = self.SEARCH_X
                elif state == self.SEARCH_X:
                    match = re.match('([usmcet][tc]?) +([0-9]+)', line, re.I)
                    if match:
                        n_vals = int(match.group(2)) - 1
                        if n_vals > 0:
                            logger.debug('Found independent variable: %s, %d values', match.group(1), n_vals)
                            state = self.READ_X
                elif state == self.READ_X:
                    # split the string
                    splitted = re.split(' +', line.strip())
                    floats = map(float, splitted)
                    logger.debug('Parsed %d floats: %s', len(floats), str(floats))
                    xs += floats
                    if len(xs) >= n_vals:
                        state = self.SEARCH_VALS
                        xs = xs[:n_vals]
                elif state == self.SEARCH_VALS:
                    if re.match('vals', line, re.I):
                        logger.debug('Found values')
                        must_skip = 2*zone_index*(n_vals+1)
                        logger.debug('Will skip %d items', must_skip)
                        state = self.SEARCH_ZONE
                elif state == self.SEARCH_ZONE:
                    # split the string
                    splitted = re.split(' +', line.strip())
                    must_skip -= len(splitted)
                    logger.debug('Read %d values, %d to go: starts with %s', len(splitted), must_skip, splitted[0])
                    if must_skip < 0:
                        logger.debug('Moving to READ_VALS state')
                        line = ' '.join(splitted[must_skip:])
                        logger.debug('Handing over %s to parser', line)
                        state = self.READ_VALS

                if state == self.READ_VALS:
                    stripped = line.strip()
                    if stripped:
                        # split the string
                        splitted = re.split(' +', stripped)
                        floats = map(float, splitted)
                        logger.debug('Parsed %d floats: %s', len(floats), str(floats))
                        ys += floats[::2]
                        eys += floats[1::2]
                        if len(ys) >= n_vals + 1:
                            ys = ys[1:n_vals]
                            eys = eys[1:n_vals]
                            break

                line = f.readline()


        # fill exs here
        ys.append(0)
        eys.append(0)

        if len(xs) != len(ys) or (eys and len(ys)!=len(eys)) or (exs and len(exs)!=len(xs)):
            raise Exception('Inconsistent lengths of x ({})/y ({})/ey ({})/ex ({}) arrays'.format(len(xs), len(ys), len(eys), len(exs)))

        logger.debug('Parsing succeeded')
        logger.debug('xs=%s', xs)
        logger.debug('ys=%s', ys)
        logger.debug('exs=%s', exs)
        logger.debug('eys=%s', eys)

        xarr = np.array(xs, dtype=dtype)
        yarr = np.array(ys, dtype=dtype)
        eyarr = np.array(eys, dtype=dtype)
        exarr = np.ediff1d(xs)
        result = Result(
                edges=xarr,
                contents=yarr,
                errors=eyarr,
                xerrors=exarr
                )
        return result

    def labels(self, tally_number):
        return ('', '')

    def label(self, tally_number):
        return ''

