from t4.plotmanager import PlotManager
from t4.datasources import XMLDataSource, CSVDataSource

pm = PlotManager()

directory = '/data/tmpdm2s/dm232107/calculations/t4/ttb/sphere/'

photon_ds = XMLDataSource(directory + 'photon/photon.t4.xml', 'photon_spectrum_fine')
ttb_ds = XMLDataSource(directory + 'ttb/ttb.t4.xml', 'photon_spectrum_fine')
no_ttb_ds = XMLDataSource(directory + 'no_ttb/no_ttb.t4.xml', 'photon_spectrum_fine')
pm.energy_score([photon_ds, ttb_ds, no_ttb_ds])

