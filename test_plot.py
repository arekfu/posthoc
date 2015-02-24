#!/usr/bin/env python

from t4.plotmanager import PlotManager
from t4.datasources import XMLDataSource, CSVDataSource
import matplotlib.pyplot as plt
import sys

directory = sys.argv[1] if len(sys.argv)>=2 else '/data/tmpdm2s/dm232107/calculations/t4/ttb/sphere/'

photon = XMLDataSource(
        directory + 'photon/photon.t4.xml',
        'photon_spectrum',
        divide_by_bin=False,
        label='T4 photon',
        marker='o',
        color='green',
        linestyle=':'
        )
ttb = XMLDataSource(
        directory + 'ttb/ttb.t4.xml',
        'photon_spectrum',
        divide_by_bin=False,
        label='T4 TTB',
        marker='s',
        color='red',
        linestyle='-'
        )
no_ttb = XMLDataSource(
        directory + 'no_ttb/no_ttb.t4.xml',
        'photon_spectrum',
        divide_by_bin=False,
        label='T4 full',
        marker='s',
        color='k',
        linestyle='--'
        )
no_ttb_no_e = XMLDataSource(
        directory + 'no_ttb_no_e/no_ttb_no_e.t4.xml',
        'photon_spectrum',
        divide_by_bin=False,
        label='T4 no $e^+$/$e^-$',
        marker='D',
        color='blue',
        linestyle='-.'
        )

mcnp = CSVDataSource(
        directory + 'mcnp/mcnp_bin_norm.dat',
        '0:1:2',
        label='MCNP full',
        marker='d',
        color='g',
        linestyle='--'
        )

mcnp_ttb = CSVDataSource(
        directory + 'mcnp_ttb/mcnp_ttb_bin_norm.dat',
        '0:1:2',
        label='MCNP TTB',
        marker='d',
        color='b',
        linestyle='-'
        )

g4emy = CSVDataSource(
        directory + 'g4EMY/EMY.dat',
        '0:1:2',
        label='Geant4 EMY',
        marker='d'
        )

ttb_over_full = ttb/no_ttb
ttb_over_full.label = 'T4 TTB/full'
ttb_over_full.kwargs['color']='r'
ttb_over_full.kwargs['linestyle']='-'
ttb_over_full.ylabel='ratio'

mcnp_ttb_over_full = mcnp_ttb/mcnp
mcnp_ttb_over_full.label = 'MCNP TTB/full'
mcnp_ttb_over_full.kwargs['color']='k'
mcnp_ttb_over_full.kwargs['linestyle']='--'
mcnp_ttb_over_full.ylabel='ratio'

t4_over_mcnp_full = no_ttb/mcnp
t4_over_mcnp_full.label = 'T4/MCNP full'
t4_over_mcnp_full.kwargs['color']='k'
t4_over_mcnp_full.kwargs['linestyle']='--'
t4_over_mcnp_full.ylabel='ratio'

t4_over_mcnp_ttb = ttb/mcnp_ttb
t4_over_mcnp_ttb.label = 'T4/MCNP TTB'
t4_over_mcnp_ttb.kwargs['color']='r'
t4_over_mcnp_ttb.kwargs['linestyle']='-'
t4_over_mcnp_ttb.ylabel='ratio'

fig, ax = plt.subplots(2,2, sharex=True, sharey='row')

pm = PlotManager()

pm.draw([no_ttb, ttb, photon, no_ttb_no_e], axes=ax[0,0])

pm.draw([no_ttb, ttb, mcnp, mcnp_ttb], axes=ax[0,1])

pm.draw([ttb_over_full, mcnp_ttb_over_full], axes=ax[1,0], yscale='linear')

pm.draw([t4_over_mcnp_full, t4_over_mcnp_ttb], axes=ax[1,1], yscale='linear')

fig.tight_layout()

plt.show()
