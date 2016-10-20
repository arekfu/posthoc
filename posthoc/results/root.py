# coding: utf-8

from __future__ import division
import logging

import numpy as np
import ROOT

from .result import Result

# set up logging
logger = logging.getLogger(__name__)


class ROOTResult(object):
    def __init__(self, tfile, histo):
        self.tfile = tfile
        self.histo = histo

    @classmethod
    def fromhisto(cls, file_name, histo_name):
        tfile = ROOT.TFile(file_name)
        histo = tfile.Get(histo_name)
        return ROOTResult(tfile, histo)

    @classmethod
    def fromtree(self, file_name, tree_name, var, cut, bins):
        tfile = ROOT.TFile(file_name)
        tree = tfile.Get(tree_name)
        if bins:
            nx, xmin, xmax, log = bins
            if log:
                logxmin = np.log10(xmin)
                logxmax = np.log10(xmax)
                logbins = np.logspace(logxmin, logxmax, nx+1, base=10)
                histo = ROOT.TH1F('htemp', 'htemp', nx, logbins)
            else:
                histo = ROOT.TH1F('htemp', 'htemp', nx, xmin, xmax)
            tree.Project('htemp', var, cut)
        else:
            tree.Draw(var + '>>htemp', cut, 'goff')
        histo = ROOT.gDirectory.Get('htemp')
        return ROOTResult(tfile, histo)

    def result(self):
        xs = list()
        ys = list()
        eys = list()
        exs = list()

        nbins = self.histo.GetNbinsX()
        for i in range(nbins):
            x = self.histo.GetXaxis().GetBinLowEdge(i+1)
            y = self.histo.GetBinContent(i+1)
            ex = self.histo.GetXaxis().GetBinWidth(i+1)
            ey = self.histo.GetBinError(i+1)
            xs.append(x)
            ys.append(y)
            exs.append(ex)
            eys.append(ey)
        xs.append(self.histo.GetXaxis().GetBinUpEdge(nbins))
        ys.append(0)
        exs.append(0)
        eys.append(0)

        if (len(xs) != len(ys) or
                (eys and len(ys) != len(eys)) or
                (exs and len(exs) != len(xs))):
            raise Exception('Inconsistent lengths of x/y/ey/ex arrays')

        logger.debug('ROOT import succeeded')
        logger.debug('xs=%s', xs)
        logger.debug('ys=%s', ys)
        logger.debug('exs=%s', exs)
        logger.debug('eys=%s', eys)

        xarr = np.array(xs)
        yarr = np.array(ys)
        eyarr = np.array(eys) if eys else None
        exarr = np.array(exs) if exs else None
        result = Result(edges=xarr, contents=yarr, errors=eyarr, xerrors=exarr)
        return result

    def labels(self):
        xlabel = self.histo.GetXaxis().GetTitle()
        ylabel = self.histo.GetXaxis().GetTitle()
        return xlabel, ylabel
