import numpy as np

class XMLResult:

    def __init__(self, fname):
        from bs4 import BeautifulSoup
        with open(fname) as f:
            self.soup = BeautifulSoup(f.read(), 'lxml')

    def grids(self):
        for gridxml in self.soup.list_decoupage.find_all('decoupage', recursive=False):
            grid = np.fromstring(gridxml.string, sep=' ')
            name = unicode(gridxml.get('name'))
            yield name, grid

    def grid(self, name):
        gridxml = self.soup.list_decoupage.find('decoupage', recursive=False, attrs={'name': name})
        grid = np.fromstring(gridxml.string, sep=' ')
        return grid

    def scores(self):
        for scorexml in self.soup.scores_definition.find_all('score', recursive=False):
            yield scorexml

    def score(self, name):
        score = self.soup.scores_definition.find('score', recursive=False, attrs={'name': name})
        return score

    def responses(self):
        for responsexml in self.soup.response_definition.find_all('response', recursive=False):
            yield responsexml

    def response(self, name):
        response = self.soup.response_definition.find('response', recursive=False, attrs={'name': name})
        return response

    def batch_results(self, batch_num):
        if isinstance(batch_num, int):
            results = self.soup.batches.find('batch', recursive=False, num=batch_num)
            return results
        else:
            raise ValueError("argument batch_num to XMLResult.batch_results must be 'last' or a batch number (int)")

    def batch_result(self, score_name, batch_num, normalize=True):
        if not isinstance(score_name,str):
            raise ValueError('argument score_name to XMLResult.batch_result must be a string')
        results = self.batch_results(batch_num)
        score = self.score(score_name)
        if not score:
            raise ValueError('argument score_name to XMLResult.batch_result must be the name of a score')
        score_grid_name = score['nrj_dec']
        grid = self.grid(score_grid_name)
        score_id = score['id']
        resultxml = results.find('result', scoreid=score_id)
        result = np.fromstring(resultxml.gelement.string, sep=' ')
        # divide by the bin width if requested
        if normalize:
            width = np.ediff1d(grid)
            result = result/width
        return grid, result

    def mean_results(self, batch_num='last'):
        if batch_num=='last':
            results = self.soup.batches.find_all('mean_results', recursive=False)[-1]
        elif isinstance(batch_num, int):
            results = self.soup.batches.find('mean_results', recursive=False, batchnum=batch_num)
        else:
            raise ValueError("argument batch_num to XMLResult.mean_results must be 'last' or a batch number (int)")
        return results

