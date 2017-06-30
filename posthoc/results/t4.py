# coding: utf-8

import logging

import numpy as np
import re

from .result import Result, DTYPE

# set up logging
logger = logging.getLogger(__name__)

def _is_descending_grid(grid):
    return grid[0]>grid[1]

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
                     cell=(0,0,0,0), divide_by_bin=True):
        """Return the result for a given score in a given batch.

        Arguments:
        score_name -- name of the score (as a string)
        batch_num -- the number of the batch.

        Keyword arguments:
        region_id -- the ID of the score region
        divide_by_bin -- whether the score result should be divided by the bin
                         size.
        cell -- for extended meshes, a 4-tuple giving the time, x, y and z
                indices of the requested energy distribution.

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
        if gelement_def['zone_type']=='SPECIAL_MESH':
            score_div_value = DTYPE(1)
            nt = 1  # FIXME: assume one time bin for the moment being
            nx = int(gelement_def['nx'])
            ny = int(gelement_def['ny'])
            nz = int(gelement_def['nz'])
        else:
            score_div_value_str = gelement_def['div_value']
            if score_div_value_str:
                score_div_value = DTYPE(score_div_value_str)
            else:
                score_div_value = None
        grid = self.grid(score_grid_name)
        score_id = score['id']
        logger.debug('score ID for score "{}" is {}'.format(score_name, score_id))
        results = self.batch_results_xml(batch_num)
        resultxml = (results.find('result', scoreid=score_id)
                     .find('gelement', id=region_id))
        result = np.fromstring(resultxml.string, sep=' ', dtype=DTYPE)
        if gelement_def['zone_type']=='SPECIAL_MESH':
            ne = grid.size - 1
            it, i, j, k = cell
            result = result.reshape(nt, ne, nx, ny, nz)[it,:,i,j,k]
        # divide by the bin width if requested
        if divide_by_bin:
            width = np.ediff1d(grid)
            result /= width
        # divide by the value in the XML tree
        if score_div_value:
            result /= score_div_value
        result = np.append(result, [DTYPE(0)])
        return Result(edges=grid, contents=result, errors=None, xerrors=None)

    def batch_result_keff(self, estimator_name, batch_num):
        """Return the keff result for a given estimator in a given batch.

        Arguments:
        estimator_name -- name of the estimator (one of 'KSTEP', 'KTRACK',
        'KCOLL' or 'MAT_KCOLL')
        batch_num -- the number of the batch.

        Return value:
        the keff value
        """
        if not isinstance(estimator_name, str):
            raise ValueError('argument score_name to '
                             'T4XMLResult.batch_result_keff '
                             'must be a string')
        ename = estimator_name.upper()
        if ename not in ['KCOLL', 'KTRACK', 'KSTEP', 'MAT_KCOLL']:
            raise ValueError('argument uct_estimator_name to '
                             'T4XMLResult.batch_result_keff '
                             'must be one of "KCOLL", "KTRACK", "KSTEP" or '
                             '"MAT_KCOLL"')
        results = self.batch_results_xml(batch_num)
        keffxml = results.find(estimator_name)
        keff = DTYPE(keffxml.string)
        return keff

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
                    cell=(0,0,0), time_step=0, divide_by_bin=True):
        """Return the mean result for a given score.

        Arguments:
        score_name -- name of the score (as a string)

        Keyword arguments:
        batch_num -- results will be presented for the specified batch. Can be
                     an integer, in which case it is interpreted as a batch
                     number, or 'last'.
        region_id -- the ID of the score region
        cell -- for extended meshes, a 3-tuple giving x, y and z indices of the
                requested energy distribution.
        time_step -- index of the requested time step
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
        if gelement_def['zone_type']=='SPECIAL_MESH':
            score_div_value = DTYPE(1)
            nx = int(gelement_def['nx'])
            ny = int(gelement_def['ny'])
            nz = int(gelement_def['nz'])
            nvals = nx*ny*nz
        else:
            score_div_value_str = gelement_def['div_value']
            if score_div_value_str:
                score_div_value = DTYPE(score_div_value_str)
            else:
                score_div_value = None
            nvals = 1
        grid = self.grid(score_grid_name)
        ne = grid.size - 1

        if 'tps_dec' in score.attrs:
            time_grid_name = score['tps_dec']
            time_grid = self.grid(time_grid_name)
            nt = time_grid.size - 1
        else:
            nt = 1

        nvals *= ne

        score_id = score['id']
        logger.debug('score ID for score "{}" is {}'.format(score_name, score_id))
        results = self.mean_results_xml(batch_num)
        resultxml = (results.find('mean_result', scoreid=score_id)
                     .find('gelement', id=region_id))
        val_list = [DTYPE(v.string) for v in resultxml.find_all('val')]
        sd_list = [DTYPE(v.string) for v in resultxml.find_all('sd')]

        if _is_descending_grid(grid):
            grid = np.array(list(reversed(grid)))
            val_list = list(reversed(val_list))
            sd_list = list(reversed(sd_list))

        val = np.array(val_list, dtype=DTYPE)
        sd = np.array(sd_list, dtype=DTYPE)
        if gelement_def['zone_type']=='SPECIAL_MESH':
            it = time_step
            i, j, k = cell
            print(val.shape)
            val = val.reshape(nt, ne, nx, ny, nz)[it,:,i,j,k]
            sd = sd.reshape(nt, ne, nx, ny, nz)[it,:,i,j,k]
        else:
            min_index = time_step*nvals
            max_index = (time_step+1)*nvals
            val = val[min_index:max_index]
            sd = sd[min_index:max_index]
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
        unit = 'source'
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


class T4TXTResult(object):
    """Extract data from the Tripoli-4® output file.

    This class is responsible for extracting the calculation results from the
    Tripoli-4® text output file.
    """

    edition_start_regex = re.compile(r' RESULTS ARE GIVEN FOR SOURCE INTENSITY')
    score_name_regex = re.compile(r'SCORE NAME : (.+)')
    score_start_regex = re.compile(r'RESPONSE FUNCTION : ')
    region_start_regex = re.compile(r'	 scoring mode :')
    region_end_regex = re.compile(r'number of batches used: (\d+)')
    edition_end_regex = re.compile(r' simulation time \(s\)')

    dataline_regex = re.compile(r'([\d.eE+-]+) - ([\d.eE+-]+)	([\d.eE+-]+)'
                                 '	([\d.eE+-]+)	([\d.eE+-]+)$')

    def __init__(self, fname, batch_num):
        """Initialize the instance from the file 'fname'.

        Arguments:
        fname     -- the name of the file.
        batch_num -- the number of the batch.
        """
        self.fname = fname
        self.batch_num = batch_num
        self.parse_endpoints()

    def parse_endpoints(self):
        """Find the start and end offset in the file for the requested batch.
        """
        self.endpoints = []
        score_names = []
        score_endpoints = []
        region_start = None
        this_batch_num = None

        with open(self.fname) as f:
            for line in iter(f.readline, ''):
                if re.match(self.edition_start_regex, line):
                    score_endpoints = []
                    self.endpoints = []
                    score_names = []
                    continue

                if re.match(self.score_start_regex, line):
                    if len(score_endpoints)!=0:
                        self.endpoints.append(score_endpoints)
                    score_endpoints = []
                    score_names.append('')
                    continue

                match = re.match(self.score_name_regex, line)
                if match:
                    score_name = match.group(1)
                    score_names[-1] = score_name
                    continue

                if re.match(self.region_start_regex, line):
                    region_start = f.tell()
                    continue

                match = re.match(self.region_end_regex, line)
                if match:
                    this_batch_num = int(match.group(1))
                    region_end = f.tell()
                    score_endpoints.append((region_start,region_end))
                    continue

                if re.match(self.edition_end_regex, line):
                    self.endpoints.append(score_endpoints)
                    if self.batch_num == this_batch_num:
                        break

        if len(self.endpoints)==0:
            raise ValueError('could not find results for batch_num={}'
                                ' in file {}'.format(self.batch_num, self.fname))

        if self.batch_num == 'last':
            self.batch_num = this_batch_num

        self.score_numbers = { name: index for (index, name) in enumerate(score_names) }

    def result(self, score, region_rank=0, divide_by_bin=True):
        """Return the result for a given score in a given batch.

        Arguments:
        score -- name (string) or rank (int) of the score

        Keyword arguments:
        region_rank -- the rank of the score region
        divide_by_bin -- whether the score result should be divided by the bin
                         size.

        Return value:
        a Result object containing the requested results.
        """
        if not isinstance(score, str) and not isinstance(score, int):
            raise ValueError('argument score_name to T4TXTResult.batch_result '
                             'must be a string or an int')

        if isinstance(score, str):
            try:
                score = self.score_numbers[score]
            except KeyError:
                raise ValueError('could not find score {}'.format(score))

        start, end = self.endpoints[score][region_rank]

        xlo = []
        xhi = []
        val = []
        err = []
        with open(self.fname) as f:
            f.seek(start)
            for line in iter(f.readline, ''):
                if f.tell()>=end:
                    break
                match = re.match(self.dataline_regex, line)
                if match:
                    xlo.append(match.group(1))
                    xhi.append(match.group(2))
                    val.append(match.group(3))
                    err.append(match.group(4))

        edges = []
        contents = []
        errors = []
        for i, x in enumerate(xlo):
            if i<len(xlo)-1:
                edges.append(float(xlo[i]))
                cont = float(val[i])
                contents.append(cont)
                errors.append(float(err[i]) * cont * 0.01)
                if xlo[i+1]!=xhi[i]:
                    edges.append(float(xhi[i]))
                    contents.append(0.0)
                    errors.append(0.0)
            else:
                edges.append(float(xhi[i]))
                contents.append(0.0)
                errors.append(0.0)

        edges = np.array(edges)
        contents = np.array(contents)
        errors = np.array(errors)

        return Result(edges=edges, contents=contents, errors=errors, xerrors=None)

