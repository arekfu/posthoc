# coding: utf-8

import matplotlib.pyplot as plt

class Plotter(object):
    def __init__(self, axes=None):
        self.set_axes(axes)
        self.handles = list()
        self.labels = list()

    def set_axes(self, axes=None):
        if axes:
            self.axes = axes
            self.axes.set_color_cycle(None)
        else:
            self.axes = plt.axes()

    def draw_step(self, data_source):
        result = data_source.result
        step_args = data_source.kwargs.copy()
        if 'marker' in step_args:
            del step_args['marker']
        if 'drawstyle' in step_args:
            del step_args['drawstyle']
        step_artist, = self.axes.plot(
                result.edges,
                result.contents,
                drawstyle='steps-post',
                marker=None,
                label=None,
                **step_args
                )
        centers = 0.5*(result.edges[1:]+result.edges[:-1])

        errorbar_args = data_source.kwargs.copy()
        if not 'color' in errorbar_args:
            lc = plt.getp(step_artist, 'color')
            errorbar_args['color'] = lc
        if 'linestyle' in errorbar_args:
            del errorbar_args['linestyle']
        try:
            yerr = result.errors[:-1]
        except TypeError:
            yerr = None
        errorbar_artists = self.axes.errorbar(
                centers,
                result.contents[:-1],
                yerr=yerr,
                linestyle = 'None',
                label=None,
                **errorbar_args
                )

        self.handles += [(step_artist, errorbar_artists)]
        self.labels += [data_source.label]

