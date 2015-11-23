# coding: utf-8

import logging

import numpy as np

from .result import Result

# set up logging
LOGGER = logging.getLogger(__name__)


class TXTResult(object):
    def __init__(self, file_name, parser):
        self.file_name = file_name
        self.parser = parser

    def result(self):
        xs = list()
        ys = list()
        eys = list()
        exs = list()
        n_tokens = None
        with open(self.file_name) as f:
            for line in f:
                parsed = self.parser(line)

                LOGGER.debug('Parsed line\n%s as %s', line, parsed)

                if not parsed:
                    continue

                if n_tokens is None:
                    n_tokens = len(parsed)

                if len(parsed) != n_tokens:
                    raise Exception('Inconsistent number of fields '
                                    '(expected ' + str(n_tokens) + ') '
                                    'returned when parsing' + self.file_name +
                                    '\nThe problematic line was ' + line)

                if n_tokens == 2:
                    x, y = parsed
                elif n_tokens == 3:
                    x, y, ey = parsed
                    eys.append(ey)
                elif n_tokens == 4:
                    x, y, ey, ex = parsed
                    eys.append(ey)
                    exs.append(ex)

                xs.append(x)
                ys.append(y)

        if (len(xs) != len(ys) or
                (eys and len(ys) != len(eys)) or
                (exs and len(exs) != len(xs))):
            raise Exception('Inconsistent lengths of x/y/ey/ex arrays')

        LOGGER.debug('Parsing succeeded')
        LOGGER.debug('xs=%s', xs)
        LOGGER.debug('ys=%s', ys)
        LOGGER.debug('exs=%s', exs)
        LOGGER.debug('eys=%s', eys)

        xarr = np.array(xs)
        yarr = np.array(ys)
        eyarr = np.array(eys) if eys else None
        exarr = np.array(exs) if exs else None
        result = Result(edges=xarr, contents=yarr, errors=eyarr, xerrors=exarr)
        return result
