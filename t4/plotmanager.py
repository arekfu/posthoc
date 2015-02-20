# coding: utf-8

import matplotlib.pyplot as plt
from plotter import Plotter
from datasource import DataSource

plt.ion()

class PlotManager:
    def __init__(self):
        self.plotter = Plotter()

    def energy_score(self, to_plot, axes=None, xscale='linear', yscale='log', **kwargs):
        if not axes:
            axes = plt.axes(xscale=xscale, yscale=yscale, **kwargs)
        self.plotter.set_axes(axes)

        xlabel = ylabel = ''
        for item in to_plot:
            ds = DataSource(item)
            self.plotter.draw_step(ds)

            if not xlabel:
                xlabel = ds.result.xlabel
            if not ylabel:
                ylabel = ds.result.ylabel

        plt.gca().set_xlabel(xlabel)
        plt.gca().set_ylabel(ylabel)
        plt.gca().set_xscale(xscale)
        plt.gca().set_yscale(yscale)
        plt.draw()

