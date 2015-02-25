# coding: utf-8

import matplotlib.pyplot as plt
from plotter import Plotter
import datasources

class PlotManager(object):
    def __init__(self):
        self.axes_plotter = dict()

    def draw(self, to_plot, axes=None, xscale='linear', yscale='log', legend=True, **kwargs):
        if not axes:
            figure = plt.Figure()
            axes = figure.add_axes(xscale=xscale, yscale=yscale, **kwargs)
        if axes in self.axes_plotter:
            plotter = self.axes_plotter[axes]
        else:
            plotter = Plotter(axes)
            self.axes_plotter[axes] = plotter

        xlabel = ylabel = ''
        for item in to_plot:
            ds = datasources.to_datasource(item)
            plotter.draw(ds)

            if not xlabel:
                xlabel = ds.xlabel
            if not ylabel:
                ylabel = ds.ylabel

        axes.set_xlabel(xlabel)
        axes.set_ylabel(ylabel)
        axes.set_xscale(xscale)
        axes.set_yscale(yscale)
        if legend:
            axes.legend(plotter.handles, plotter.labels, labelspacing=0.05)

        return axes
