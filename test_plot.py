#!/usr/bin/env python

from t4.plotmanager import PlotManager
from t4.datasources import XMLDataSource, CSVDataSource
import matplotlib.pyplot as plt
import sys

directory = sys.argv[1] if len(sys.argv)>2 else '/data/tmpdm2s/dm232107/calculations/t4/ttb/sphere/'

photon = XMLDataSource(
        directory + 'photon/photon.t4.xml',
        'photon_spectrum',
        divide_by_bin=False,
        label='T4 photon',
        marker='o'
        )
ttb = XMLDataSource(
        directory + 'ttb/ttb.t4.xml',
        'photon_spectrum',
        divide_by_bin=False,
        label='T4 TTB',
        marker='*'
        )
no_ttb = XMLDataSource(
        directory + 'no_ttb/no_ttb.t4.xml',
        'photon_spectrum',
        divide_by_bin=False,
        label='T4 full',
        marker='s'
        )
no_ttb_no_e = XMLDataSource(
        directory + 'no_ttb_no_e/no_ttb_no_e.t4.xml',
        'photon_spectrum',
        divide_by_bin=False,
        label='T4 no $e^+$/$e^-$',
        marker='D'
        )
mcnp = CSVDataSource(
        directory + 'mcnp/mcnp_bin_norm.dat',
        '0:1:2',
        label='MCNP',
        marker='d'
        )

pm = PlotManager()
pm.draw([photon, ttb, no_ttb, no_ttb_no_e, mcnp])

plt.show()
