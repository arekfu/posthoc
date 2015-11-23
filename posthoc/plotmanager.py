# coding: utf-8

import matplotlib.pyplot as plt
from .plotter import Plotter
import datasources.datasource
import logging

# set up logging
LOGGER = logging.getLogger(__name__)


class PlotManager(object):
    def __init__(self):
        self.axes_plotter = dict()

    def draw(self, to_plot, axes=None, xscale='linear', yscale='log',
             legend=True, legendargs=None, **kwargs):
        if not axes:
            plt.Figure()
            axes = plt.axes(xscale=xscale, yscale=yscale, **kwargs)
        if axes in self.axes_plotter:
            plotter = self.axes_plotter[axes]
        else:
            plotter = Plotter(axes)
            self.axes_plotter[axes] = plotter

        xlabel = ylabel = ''
        for item in to_plot:
            try:
                ds = datasources.datasource.to_datasource(item)
                plotter.draw(ds)
                if not xlabel:
                    xlabel = ds.xlabel
                    LOGGER.debug('Updating xlabel=%s', xlabel)
                if not ylabel:
                    ylabel = ds.ylabel
                    LOGGER.debug('Updating ylabel=%s', ylabel)
            except Exception as e:
                LOGGER.error('Cannot plot datasource: %s', e.args)

        LOGGER.debug('Setting labels: x="%s", y="%s"', xlabel, ylabel)
        axes.set_xlabel(xlabel)
        axes.set_ylabel(ylabel)
        LOGGER.debug('Setting scales: x="%s", y="%s"', xscale, yscale)
        axes.set_xscale(xscale)
        axes.set_yscale(yscale)
        if legend:
            LOGGER.debug('Adding legend')
            if legendargs:
                axes.legend(plotter.handles, plotter.labels, labelspacing=0.05,
                            **legendargs)
            else:
                axes.legend(plotter.handles, plotter.labels, labelspacing=0.05)

        return plotter.handles
