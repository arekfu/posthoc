# coding: utf-8

import copy
import warnings
import logging

import numpy as np

# set up logging
LOGGER = logging.getLogger(__name__)

TOLERANCE = None
DTYPE = float


class Result:
    def __init__(self, edges=None, contents=None, errors=None, xerrors=None):
        self.edges = edges
        self.contents = contents
        self.errors = errors
        self.xerrors = xerrors

    def __str__(self):
        return ('(' +
                str(self.edges) + ', ' +
                str(self.contents) + ', ' +
                str(self.errors) + ', ' +
                str(self.xerrors) + ')')

    def __repr__(self):
        return str(self)

    def _check_consistency_edges(self, other):
        if TOLERANCE:
            tol = TOLERANCE
        else:
            tol = 100. * np.maximum(
                np.finfo(self.edges.dtype).eps,
                np.finfo(other.edges.dtype).eps
                )

        try:
            diff = np.allclose(self.edges, other.edges, atol=tol)
        except ValueError:
            raise Exception('ResultTuple edges have different sizes: {}!={}'.format(len(self.edges), len(other.edges)))
        if not diff:
            raise Exception('ResultTuples have incompatible edges:\n'
                            'TOLERANCE = ' + str(tol) + '\n'
                            'differences = ' + str(diff))

        if self.xerrors is None or other.xerrors is None:
            return

        try:
            diff = np.allclose(self.xerrors, other.xerrors, atol=tol)
        except ValueError:
            raise Exception('ResultTuple xerrors have different sizes.')
        if not diff:
            raise Exception('ResultTuple have incompatible xerrors.')

    def __add__(self, other):
        edges = copy.deepcopy(self.edges)
        xerrors = copy.deepcopy(self.xerrors)
        if np.isscalar(other):
            contents = self.contents + other
            errors = copy.deepcopy(self.errors)
        else:
            self._check_consistency_edges(other)
            contents = self.contents + other.contents
            if self.errors is not None and other.errors is not None:
                errors = np.sqrt(self.errors**2 + other.errors**2)
            elif other.errors is not None:
                errors = copy.deepcopy(other.errors)
            else:
                errors = copy.deepcopy(self.errors)
        return Result(edges, contents, errors, xerrors)

    def __sub__(self, other):
        edges = copy.deepcopy(self.edges)
        xerrors = copy.deepcopy(self.xerrors)
        if np.isscalar(other):
            contents = self.contents - other
            errors = copy.deepcopy(self.errors)
        else:
            self._check_consistency_edges(other)
            contents = self.contents - other.contents
            if self.errors is not None and other.errors is not None:
                errors = np.sqrt(self.errors**2 + other.errors**2)
            elif other.errors is not None:
                errors = copy.deepcopy(other.errors)
            else:
                errors = copy.deepcopy(self.errors)
        return Result(edges, contents, errors, xerrors)

    def __mul__(self, other):
        edges = copy.deepcopy(self.edges)
        xerrors = copy.deepcopy(self.xerrors)
        if np.isscalar(other):
            contents = self.contents * other
            errors = self.errors * other
        else:
            self._check_consistency_edges(other)
            contents = self.contents * other.contents
            if self.errors is not None and other.errors is not None:
                errors = np.sqrt((self.contents*other.errors)**2 +
                                 (self.errors*other.contents)**2)
            elif other.errors is not None:
                errors = self.contents*other.errors
            elif self.errors is not None:
                errors = self.errors*other.contents
            else:
                errors = None
        return Result(edges, contents, errors, xerrors)

    def __div__(self, other):
        with warnings.catch_warnings():
            # we ignore warnings from div-by-zero
            warnings.filterwarnings('ignore', 'invalid value', RuntimeWarning)

            edges = copy.deepcopy(self.edges)
            xerrors = copy.deepcopy(self.xerrors)
            if np.isscalar(other):
                contents = self.contents / other
                errors = self.errors / other
            else:
                self._check_consistency_edges(other)
                contents = self.contents/other.contents
                if self.errors is not None and other.errors is not None:
                    errors = np.nan_to_num(
                        contents * np.sqrt((self.errors/self.contents)**2 +
                                           (other.errors/other.contents)**2)
                        )
                elif other.errors is not None:
                    errors = np.nan_to_num(contents * other.errors /
                                           other.contents)
                elif self.errors is not None:
                    errors = np.nan_to_num(self.errors / other.contents)
                else:
                    errors = None
            return Result(edges, contents, errors, xerrors)

    def __getitem__(self, key):
        edges = self.edges[key]
        contents = self.contents[key]
        errors = self.errors[key] if self.errors is not None else None
        xerrors = self.xerrors[key] if self.xerrors is not None else None
        return Result(edges=edges, contents=contents,
                      errors=errors, xerrors=xerrors)

    def rebin(self, nbins, mean=True):
        n = len(self.edges)
        n1 = n-1
        self.edges = self.edges[::nbins]
        if mean:
            reshaped = self.contents[:-1].reshape(n1 // nbins, nbins)
            self.contents = reshaped.mean(axis=1)
        else:
            reshaped = self.contents[:-1].reshape(n1 // nbins, nbins)
            self.contents = reshaped.sum(axis=1)
        self.contents = np.append(self.contents, [DTYPE(0)])

        if self.xerrors is not None:
            if mean:
                reshaped = self.xerrors[:-1].reshape(n1//nbins, nbins)**2
                self.xerrors = np.sqrt(reshaped.mean(axis=1))
            else:
                reshaped = self.xerrors[:-1].reshape(n1//nbins, nbins)**2
                self.xerrors = np.sqrt(reshaped.sum(axis=1))
            self.xerrors = np.append(self.xerrors, [DTYPE(0)])

        if self.errors is not None:
            if mean:
                reshaped = self.errors[:-1].reshape(n1//nbins, nbins)**2
                self.errors = np.sqrt(reshaped.mean(axis=1))
            else:
                reshaped = self.errors[:-1].reshape(n1//nbins, nbins)**2
                self.errors = np.sqrt(reshaped.sum(axis=1))
            self.errors = np.append(self.errors, [DTYPE(0)])

        LOGGER.debug('rebin: new result is %s', self)

    def rescale_edges(self, factor, rescale_contents=True):
        """Apply a scale factor to the bin edges (and xerrors, if present).

        Arguments:
        factor -- the factor

        Keyword arguments:
        rescale_contents: if True, apply 1/factor to contents and errors.
        """

        self.edges *= factor
        if self.xerrors is not None:
            self.xerrors *= factor
        if rescale_contents:
            self.contents /= factor
            if self.errors is not None:
                self.errors /= factor
        LOGGER.debug('rescale_edges: new result is %s', self)

    def rescale_errors(self, factor):
        """Apply a scale factor to the bin errors."""

        self.errors = self.errors * factor if self.errors is not None else None
        LOGGER.debug('rescale_errors: new result is %s', self)

    def append_bin(self, edge=None, content=0., error=0., xerror=0.):
        new_bin_edge = edge if edge else 2.*self.edges[-1] - self.edges[-2]
        self.edges = np.append(self.edges, new_bin_edge)
        self.contents = np.append(self.contents, content)
        if self.errors is not None:
            self.errors = np.append(self.errors, error)
        if self.xerrors is not None:
            self.xerrors = np.append(self.xerrors, error)

    def chop(self, threshold=1e-30):
        chop_indices = self.contents < threshold
        self.contents[chop_indices] = 0.
        self.errors[chop_indices] = 0.

    def divide_by_bin_size(self, pad='last'):
        bin_sizes = np.ediff1d(self.edges)
        if pad == 'first':
            bin_sizes = np.insert(bin_sizes, 0, 1.)
        elif pad == 'last':
            bin_sizes = np.insert(bin_sizes, len(bin_sizes), 1.)
        else:
            raise Exception("unrecognized 'pad' option value in "
                            "divide_by_bin; must be 'first' or 'last'")
        self.contents /= bin_sizes
        self.errors /= bin_sizes

    def multiply_by_bin_size(self, pad='last'):
        bin_sizes = np.ediff1d(self.edges)
        if pad == 'first':
            bin_sizes = np.insert(bin_sizes, 0, 1.)
        elif pad == 'last':
            bin_sizes = np.insert(bin_sizes, len(bin_sizes), 1.)
        else:
            raise Exception("unrecognized 'pad' option value in "
                            "divide_by_bin; must be 'first' or 'last'")
        self.contents *= bin_sizes
        self.errors *= bin_sizes

    def integrate(self, multiply_by_bin=True):
        if multiply_by_bin:
            bins = np.ediff1d(self.edges)
            return np.sum(self.contents[:-1] * bins)
        else:
            return np.sum(self.contents[:-1])

    def bin_centers(self):
        centers = 0.5*(self.edges[:-1] + self.edges[1:])
        last_bin_center = 2.*centers[-1] - centers[-2]
        new_edges = copy.deepcopy(self.edges)
        centers = np.append(centers, last_bin_center)
        return Result(new_edges, centers, None, None)

