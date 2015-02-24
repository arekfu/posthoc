# coding: utf-8

import matplotlib.pyplot as plt
from plotter import Plotter
import datasources

class PlotManager(object):
    def __init__(self):
        self.plotter = Plotter()

    def draw(self, to_plot, axes=None, xscale='linear', yscale='log', **kwargs):
        if not axes:
            axes = plt.axes(xscale=xscale, yscale=yscale, **kwargs)
        self.plotter.set_axes(axes)

        xlabel = ylabel = ''
        for item in to_plot:
            ds = datasources.to_datasource(item)
            self.plotter.draw(ds)

            if not xlabel:
                xlabel = ds.xlabel
            if not ylabel:
                ylabel = ds.ylabel

        axes.set_xlabel(xlabel)
        axes.set_ylabel(ylabel)
        axes.set_xscale(xscale)
        axes.set_yscale(yscale)
        axes.legend(self.plotter.handles, self.plotter.labels)

