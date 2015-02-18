import numpy as np

class T4Array:
    def __init__(self, array, title):
        self.array = array
        self.title = title

class XMLResult:

    def __init__(self, fname):
        from bs4 import BeautifulSoup
        with open(fname) as f:
            self.soup = BeautifulSoup(f.read(), 'lxml')

    def results(self, batch='mean'):
        pass

    def grids(self):
        for gridxml in self.soup.list_decoupage('decoupage'):
            array = np.fromstring(gridxml.string, sep=' ')
            grid = T4Array(array, gridxml['name'])
            yield grid

