# coding: utf-8

import matplotlib.pyplot as plt

class Plotter(object):
    def __init__(self, axes=None):
        self.axes = axes
        self.handles = list()
        self.labels = list()

    def draw(self, data_source):
        step = data_source.kwargs.get('steps', False)
        if step:
            self.draw_step(data_source)
        else:
            self.draw_line(data_source)

    def draw_step(self, data_source):
        result = data_source.result
        step_args = data_source.kwargs.copy()
        self.strip_from_dict(step_args, ['steps', 'errorbars', 'drawstyle', 'marker'])
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

    def draw_line(self, data_source):
        result = data_source.result
        args = data_source.kwargs.copy()
        centers = 0.5*(result.edges[1:]+result.edges[:-1])
        try:
            yerr = result.errors[:-1]
        except TypeError:
            yerr = None
        artist = self.axes.errorbar(
                centers,
                result.contents[:-1],
                yerr=yerr,
                label=None,
                **args
                )

        self.handles += [artist]
        self.labels += [data_source.label]

    def strip_from_dict(self, d, keys):
        for key in keys:
            if key in d:
                del d[key]
