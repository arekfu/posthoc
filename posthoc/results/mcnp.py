# coding: utf-8

import logging
import re

import numpy as np

from .result import Result, DTYPE

# set up logging
logger = logging.getLogger(__name__)


class MCTALResult(object):
    SEARCH_TALLY = 0
    SEARCH_F = 1
    READ_F = 2
    SEARCH_X = 3
    READ_X = 4
    SEARCH_ZONE = 5
    SEARCH_VALS = 6
    READ_VALS = 7

    def __init__(self, file_name):
        self.file_name = file_name
        self.start_dict = {}
        self.result_dict = {}
        self.parse()

    def parse(self):
        with open(self.file_name) as f:
            line = f.readline()
            while line:
                match = re.match('tally +([0-9]+)', line, re.I)
                if match:
                    tally_number = int(match.group(1))
                    logger.debug('Found tally %d', tally_number)
                    self.start_dict[tally_number] = f.tell()
                line = f.readline()

    def result(self, tally_number, zone_number):
        res = self.result_dict.get((tally_number, zone_number), None)
        if res is None:
            res = self.extract_result(tally_number, zone_number)
            self.result_dict[(tally_number, zone_number)] = res
        return res

    def extract_result(self, tally_number, zone_number):
        xs = []
        ys = []
        eys = []
        exs = []
        state = self.SEARCH_F

        last_pos = self.start_dict.get(tally_number, None)
        if last_pos is None:
            raise Exception('Could not find tally ' + str(tally_number))

        with open(self.file_name) as f:
            f.seek(last_pos)
            line = f.readline()
            while line:
                if state == self.SEARCH_F:
                    match = re.match('f +([0-9]+)', line, re.I)
                    if match:
                        n_zones = int(match.group(1))
                        if n_zones > 0:
                            logger.debug('Found %d zones', n_zones)
                            state = self.READ_F
                            zones = []
                elif state == self.READ_F:
                    # split the string
                    splitted = re.split(' +', line.strip())
                    ints = map(int, splitted)
                    logger.debug('Parsed %d ints: %s', len(ints), str(ints))
                    zones += ints
                    if len(zones) >= n_zones:
                        zone_index = zones.index(zone_number)
                        state = self.SEARCH_X
                elif state == self.SEARCH_X:
                    match = re.match('([usmcet][tc]?) +([0-9]+)', line, re.I)
                    if match:
                        n_vals = int(match.group(2)) - 1
                        if n_vals > 0:
                            logger.debug('Found independent variable: %s, %d '
                                         'values', match.group(1), n_vals)
                            state = self.READ_X
                elif state == self.READ_X:
                    # split the string
                    splitted = re.split(' +', line.strip())
                    floats = map(float, splitted)
                    logger.debug('Parsed %d floats: %s', len(floats),
                                 str(floats))
                    xs += floats
                    if len(xs) >= n_vals:
                        state = self.SEARCH_VALS
                        xs = xs[:n_vals]
                elif state == self.SEARCH_VALS:
                    if re.match('vals', line, re.I):
                        logger.debug('Found values')
                        must_skip = 2*zone_index*(n_vals+1)
                        logger.debug('Will skip %d items', must_skip)
                        state = self.SEARCH_ZONE
                elif state == self.SEARCH_ZONE:
                    # split the string
                    splitted = re.split(' +', line.strip())
                    must_skip -= len(splitted)
                    logger.debug('Read %d values, %d to go: starts with %s',
                                 len(splitted), must_skip, splitted[0])
                    if must_skip < 0:
                        logger.debug('Moving to READ_VALS state')
                        line = ' '.join(splitted[must_skip:])
                        logger.debug('Handing over %s to parser', line)
                        state = self.READ_VALS

                if state == self.READ_VALS:
                    stripped = line.strip()
                    if stripped:
                        # split the string
                        splitted = re.split(' +', stripped)
                        floats = map(float, splitted)
                        logger.debug('Parsed %d floats: %s', len(floats),
                                     str(floats))
                        ys += floats[::2]
                        eys += floats[1::2]
                        if len(ys) >= n_vals + 1:
                            ys = ys[1:n_vals]
                            eys = eys[1:n_vals]
                            break

                line = f.readline()

        # fill exs here
        ys.append(0)
        eys.append(0)

        if len(xs) != len(ys) or \
                (eys and len(ys) != len(eys)) or \
                (exs and len(exs) != len(xs)):
            raise Exception('Inconsistent lengths of x ({})/y ({})/'
                            'ey ({})/ex ({}) arrays'.format(len(xs), len(ys),
                                                            len(eys), len(exs))
                            )

        logger.debug('Parsing succeeded')
        logger.debug('xs=%s', xs)
        logger.debug('ys=%s', ys)
        logger.debug('exs=%s', exs)
        logger.debug('eys=%s', eys)

        xarr = np.array(xs, dtype=DTYPE)
        yarr = np.array(ys, dtype=DTYPE)
        eyarr = np.array(eys, dtype=DTYPE)
        exarr = np.ediff1d(xs)

        # MCNP yields relative errors: normalize
        eyarr *= yarr

        result = Result(edges=xarr, contents=yarr, errors=eyarr, xerrors=exarr)
        return result

    def labels(self, tally_number):
        return ('', '')

    def label(self, tally_number):
        return ''
