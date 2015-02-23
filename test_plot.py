#!/usr/bin/env python

from t4.plotmanager import PlotManager
from t4.datasources import XMLDataSource, CSVDataSource

pm = PlotManager()

directory = '/data/tmpdm2s/dm232107/calculations/t4/ttb/sphere/'

photon_ds = XMLDataSource(directory + 'photon/photon.t4.xml', 'photon_spectrum', divide_by_bin=False)
ttb_ds = XMLDataSource(directory + 'ttb/ttb.t4.xml', 'photon_spectrum', divide_by_bin=False)
no_ttb_ds = XMLDataSource(directory + 'no_ttb/no_ttb.t4.xml', 'photon_spectrum', divide_by_bin=False)
mcnp_ds = CSVDataSource(directory + 'mcnp/mcnp_bin_norm.dat', '0:1:2', linestyle='none', marker='o')

pm.energy_score([photon_ds, ttb_ds, no_ttb_ds, mcnp_ds])

