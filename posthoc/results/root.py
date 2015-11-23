# coding: utf-8

import logging

import numpy as np
import ROOT

from .result import Result

# set up logging
logger = logging.getLogger(__name__)


class ROOTResult(object):
    def __init__(self, file_name):
        self.file_name = file_name
        self.tfile = ROOT.TFile(self.file_name)

    def result(self, histo_name):
        xs = list()
        ys = list()
        eys = list()
        exs = list()

        histo = self.tfile.Get(histo_name)

        nbins = histo.GetNbinsX()
        for i in range(nbins):
            x = histo.GetXaxis().GetBinLowEdge(i+1)
            y = histo.GetBinContent(i+1)
            ex = histo.GetXaxis().GetBinWidth(i+1)
            ey = histo.GetBinError(i+1)
            xs.append(x)
            ys.append(y)
            exs.append(ex)
            eys.append(ey)
        xs.append(histo.GetXaxis().GetBinUpEdge(nbins))
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

    def labels(self, histo_name):
        histo = self.tfile.Get(histo_name)
        xlabel = histo.GetXaxis().GetTitle()
        ylabel = histo.GetXaxis().GetTitle()
        return xlabel, ylabel
