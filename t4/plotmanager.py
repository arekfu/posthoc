#!/usr/bin/env python
# coding: utf-8

import matplotlib.pyplot as plt
import magic
from xmlresult import XMLResult
from plotter import Plotter

plt.ion()

class PlotManager:
    def __init__(self):
        self.default_options = {
                'batch_num': 'last',
                'divide_by_bin': True,
                }
        self.plotter = Plotter()

    def energy_score(self, to_plot, axes=None, xscale='linear', yscale='log', **kwargs):
        if not axes:
            axes = plt.axes(xscale=xscale, yscale=yscale, **kwargs)
        self.plotter.set_axes(axes)

        xlabel = ylabel = ''
        with magic.Magic() as m:
            set_labels = True
            for item in to_plot:
                file_name = item[0]
                score_name = item[1]
                kwargs = self.default_options.copy()
                try:
                    kwargs.update(item[2])
                except IndexError:
                    pass

                magic_id = m.id_filename(file_name)

                if 'XML' in magic_id:
                    xml_result = XMLResult(file_name)
                    result = xml_result.mean_result(
                            score_name,
                            batch_num=kwargs['batch_num'],
                            divide_by_bin=kwargs['divide_by_bin']
                            )
                    if set_labels:
                        set_labels=False
                        xlabel, ylabel = result.xlabel, result.ylabel
                else:
                    raise Exception('for the moment we only accept XML input')

                self.plotter.draw_step(result, **kwargs)

        plt.gca().set_xlabel(xlabel)
        plt.gca().set_ylabel(ylabel)
        plt.gca().set_xscale(xscale)
        plt.gca().set_yscale(yscale)
        plt.draw()

