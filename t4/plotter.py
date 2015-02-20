#!/usr/bin/env python
# coding: utf-8

import matplotlib.pyplot as plt

class Plotter:
    def __init__(self):
        self.set_axes()

    def set_axes(self, axes=None):
        if axes:
            self.axes = axes
            self.axes.set_color_cycle(None)
        else:
            self.axes = plt.axes()

    def draw_step(self, result, batch_num='last', divide_by_bin=True, **kwargs):
        step_artist, = self.axes.step(result.edges, result.contents, where='post', **kwargs)
        centers = 0.5*(result.edges[1:]+result.edges[:-1])
        if not 'color' in kwargs:
            lc = plt.getp(step_artist, 'color')
            kwargs['color'] = lc
        try:
            yerr = result.errors[:-1]
        except TypeError:
            yerr = None
        errorbar_artists = self.axes.errorbar(centers, result.contents[:-1], yerr=yerr, linestyle='none', **kwargs)

