import numpy as np

class XMLResult:

    def __init__(self, fname):
        from bs4 import BeautifulSoup
        with open(fname) as f:
            self.soup = BeautifulSoup(f.read(), 'lxml')

    def results(self, batch='mean'):
        pass

    def grids(self):
        for gridxml in self.soup.list_decoupage('decoupage'):
            grid = np.fromstring(gridxml.string, sep=' ')
            name = gridxml['name']
            yield name, grid

