import numpy as np

class XMLResult:

    def __init__(self, fname):
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

    def grid_xml(self, name):
        return self.soup.list_decoupage.find('decoupage', recursive=False, attrs={'name': name})

    def grid(self, name):
        gridxml = self.grid_xml(name)
        grid = np.fromstring(gridxml.string, sep=' ', dtype=self.dtype)
        return grid

    def grid_names(self):
        return self._list_from_iterable_attr(self.xgrids_xml(), 'name')

    def xscores_xml(self):
        for scorexml in self.soup.scores_definition.find_all('score', recursive=False):
            yield scorexml

    def scores_xml(self):
        return self.soup.scores_definition.find_all('score', recursive=False)

    def score_names(self):
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
        return self._list_from_iterable_attr(self.xresponses_xml(), 'name')

    def batch_results_xml(self, batch_num):
        if isinstance(batch_num, int):
            results = self.soup.batches.find('batch', recursive=False, num=batch_num)
            return results
        else:
            raise ValueError("argument batch_num to XMLResult.batch_results_xml must be 'last' or a batch number (int)")

    def batch_result(self, score_name, batch_num, normalize=True):
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
        if normalize:
            result /= width
        left = grid[:-1]
        return np.dstack((left, result, width))

    def mean_results_xml(self, batch_num='last'):
        if batch_num=='last':
            results = self.soup.batches.find_all('mean_results', recursive=False)[-1]
        elif isinstance(batch_num, int):
            results = self.soup.batches.find('mean_results', recursive=False, batchnum=batch_num)
        else:
            raise ValueError("argument batch_num to XMLResult.mean_results_xml must be 'last' or a batch number (int)")
        return results

    def mean_result(self, score_name, normalize=True):
        if not isinstance(score_name,str):
            raise ValueError('argument score_name to XMLResult.mean_result must be a string')
        score = self.score(score_name)
        if not score:
            raise ValueError('argument score_name to XMLResult.mean_result must be the name of a score')
        score_grid_name = score['nrj_dec']
        grid = self.grid(score_grid_name)
        score_id = score['id']
        results = self.mean_results_xml()
        resultxml = results.find('mean_result', scoreid=score_id).gelement
        val_list = [ self.dtype(v.string) for v in resultxml.find_all('val') ]
        sd_list = [ self.dtype(v.string) for v in resultxml.find_all('sd') ]
        val = np.array(val_list, dtype=self.dtype)
        sd = np.array(sd_list, dtype=self.dtype)
        # divide by the bin width if requested
        width = np.ediff1d(grid)
        if normalize:
            val /= width
            sd /= width
        left = grid[:-1]
        return np.dstack((left, val, width, sd))

