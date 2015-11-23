# coding: utf-8

import matplotlib.pyplot as plt
from .plotter import Plotter
from . import datasources
import logging

# set up logging
logger = logging.getLogger(__name__)

class PlotManager(object):
    def __init__(self):
        self.axes_plotter = dict()

    def draw(self, to_plot, axes=None, xscale='linear', yscale='log', legend=True, legendargs=None, **kwargs):
        if not axes:
            figure = plt.Figure()
            axes = plt.axes(xscale=xscale, yscale=yscale, **kwargs)
        if axes in self.axes_plotter:
            plotter = self.axes_plotter[axes]
        else:
            plotter = Plotter(axes)
            self.axes_plotter[axes] = plotter

        xlabel = ylabel = ''
        for item in to_plot:
            try:
                ds = datasources.to_datasource(item)
                plotter.draw(ds)
                if not xlabel:
                    xlabel = ds.xlabel
                    logger.debug('Updating xlabel=%s', xlabel)
                if not ylabel:
                    ylabel = ds.ylabel
                    logger.debug('Updating ylabel=%s', ylabel)
            except Exception as e:
                logger.error('Cannot plot datasource: %s', e.args)


        logger.debug('Setting labels: x="%s", y="%s"', xlabel, ylabel)
        axes.set_xlabel(xlabel)
        axes.set_ylabel(ylabel)
        logger.debug('Setting scales: x="%s", y="%s"', xscale, yscale)
        axes.set_xscale(xscale)
        axes.set_yscale(yscale)
        if legend:
            logger.debug('Adding legend')
            if legendargs:
                axes.legend(plotter.handles, plotter.labels, labelspacing=0.05, **legendargs)
            else:
                axes.legend(plotter.handles, plotter.labels, labelspacing=0.05)

        return plotter.handles
