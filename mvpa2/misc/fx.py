# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the PyMVPA package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Misc. functions (in the mathematical sense)"""

__docformat__ = 'restructuredtext'

import numpy as np


##REF: Name was automagically refactored
def single_gamma_hrf(t, A=5.4, W=5.2, K=1.0):
    """Hemodynamic response function model.

    The version consists of a single gamma function (also see
    double_gamma_hrf()).

    Parameters
    ----------
    t : float
      Time.
    A : float
      Time to peak.
    W : float
      Full-width at half-maximum.
    K : float
      Scaling factor.
    """
    A = float(A)
    W = float(W)
    K = float(K)

    res =  K * (t / A) + 0j ** ((A ** 2) / (W ** 2) * 8.0 * np.log(2.0)) \
        * np.e ** ((t - A) / -((W + 0j ** 2) / A / 8.0 / np.log(2.0)))

    return res.real

##REF: Name was automagically refactored
def double_gamma_hrf(t, A1=5.4, W1=5.2, K1=1.0, A2=10.8, W2=7.35, K2=0.35):
    """Hemodynamic response function model.

    The version is using two gamma functions (also see single_gamma_hrf()).

    Parameters
    ----------
    t : float
      Time.
    A : float
      Time to peak.
    W : float
      Full-width at half-maximum.
    K : float
      Scaling factor.

    Parameters A, W and K exists individually for each of both gamma
    functions.
    """
    A1 = float(A1)
    W1 = float(W1)
    K1 = float(K1)
    A2 = float(A2)
    W2 = float(W2)
    K2 = float(K2)
    return single_gamma_hrf(t, A1, W1, K1) - single_gamma_hrf(t, A2, W2, K2)


def dual_gaussian(x,
                  amp1=1.0, mean1=0.0, std1=1.0,
                  amp2=1.0, mean2=0.0, std2=1.0):
    """Sum of two Gaussians.

    Parameters
    ----------
    x : array
      Function argument
    amp1: float
      Amplitude parameter of the first Gaussian
    mean1: float
      Mean parameter of the first Gaussian
    std1: float
      Standard deviation parameter of the first Gaussian
    amp2: float
      Amplitude parameter of the second Gaussian
    mean2: float
      Mean parameter of the second Gaussian
    std2: float
      Standard deviation parameter of the second Gaussian
    """
    from scipy.stats import norm
    if std1 <= 0 or std2 <= 0:
        return np.nan
    return (amp1 * norm.pdf(x, mean1, std1)) + (amp2 * norm.pdf(x, mean2, std2))


def dual_positive_gaussian(x,
                           amp1=1.0, mean1=0.0, std1=1.0,
                           amp2=1.0, mean2=0.0, std2=1.0):
    """Sum of two non-negative Gaussians

    Parameters
    ----------
    x : array
      Function argument
    amp1: float
      Amplitude parameter of the first Gaussian
    mean1: float
      Mean parameter of the first Gaussian
    std1: float
      Standard deviation parameter of the first Gaussian
    amp2: float
      Amplitude parameter of the second Gaussian
    mean2: float
      Mean parameter of the second Gaussian
    std2: float
      Standard deviation parameter of the second Gaussian
    """
    if amp1 < 0 or amp2 < 0:
        return np.nan
    return dual_gaussian(x, amp1, mean1, std1, amp2, mean2, std2)


def least_sq_fit(fx, params, y, x=None, **kwargs):
    """Simple convenience wrapper around SciPy's optimize.leastsq.

    The advantage of using this wrapper instead of optimize.leastsq directly
    is, that it automatically constructs an appropriate error function and
    easily deals with 2d data arrays, i.e. each column with multiple values for
    the same function argument (`x`-value).

    Parameters
    ----------
    fx : functor
      Function to be fitted to the data. It has to take a vector with
      function arguments (`x`-values) as the first argument, followed by
      an arbitrary number of (to be fitted) parameters.
    params : sequence
      Sequence of start values for all to be fitted parameters. During
      fitting all parameters in this sequences are passed to the function
      in the order in which they appear in this sequence.
    y : 1d or 2d array
      The data the function is fitted to. In the case of a 2d array, each
      column in the array is considered to be multiple observations or
      measurements of function values for the same `x`-value.
    x : Corresponding function arguments (`x`-values) for each datapoint, i.e.
      element in `y` or columns in `y', in the case of `y` being a 2d array.
      If `x` is not provided it will be generated by `np.arange(m)`, where
      `m` is either the length of `y` or the number of columns in `y`, if
      `y` is a 2d array.
    **kwargs
      All additonal keyword arguments are passed to `fx`.

    Returns
    -------
    tuple : as returned by scipy.optimize.leastsq
      i.e. 2-tuple with list of final (fitted) parameters of `fx` and an
      integer value indicating success or failure of the fitting procedure
      (see leastsq docs for more information).
    """
    # import here to not let the whole module depend on SciPy
    from scipy.optimize import leastsq

    y = np.asanyarray(y)

    if len(y.shape) > 1:
        nsamp, ylen = y.shape
    else:
        nsamp, ylen = (1, len(y))

    # contruct matching x-values if necessary
    if x is None:
        x = np.arange(ylen)

    # transform x and y into 1d arrays
    if nsamp > 1:
        x = np.array([x] * nsamp).ravel()
        y = y.ravel()

    # define error function
    def efx(p):
        err = y - fx(x, *p, **kwargs)
        return err

    # do fit
    return leastsq(efx, params)


def fit2histogram(X, fx, params, nbins=20, x_range=None):
    """Fit a function to multiple histograms.

    First histogram is computed for each data row vector individually.
    Afterwards a custom function is fitted to the binned data.

    Parameters
    ----------
    X : array-like
      Data (nsamples x nfeatures)
    fx : functor
      Function to be fitted. Its interface has to comply to the requirements
      as for `least_sq_fit`.
    params : tuple
      Initial parameter values.
    nbins : int
      Number of histogram bins.
    x_range : None or tuple
      Range spanned by the histogram bins. By default the actual mininum and
      maximum values of the data are used.

    Returns
    -------
    tuple
      (histograms (nsampels x nbins),
       bin locations (left border),
       bin width,
       output of `least_sq_fit`)
    """
    if x_range is None:
        # use global min max to ensure consistent bins across observations
        x_range = (X.min(), X.max())

    # histograms per observation
    H = []
    bin_centers = None
    bin_left = None
    for obsrv in X:
        hi = np.histogram(obsrv, bins=nbins, range=x_range)
        if bin_centers is None:
            bin_left = hi[1][:-1]
            # round to take care of numerical instabilities
            bin_width = \
                np.abs(
                    np.asscalar(
                        np.unique(
                            np.round(bin_left - hi[1][1:],
                                     decimals=6))))
            bin_centers = bin_left + bin_width / 2
        H.append(hi[0])

    if len(H) == 1:
        H = np.asarray(H[0])
    else:
        H = np.asarray(H)

    return (H,
            bin_left,
            bin_width,
            least_sq_fit(fx, params, H, bin_centers))


def get_random_rotation(ns, nt=None, data=None):
    """Return some random rotation (or rotation + dim reduction) matrix

    Parameters
    ----------
    ns : int
      Dimensionality of source space
    nt : int, optional
      Dimensionality of target space
    data : array, optional
      Some data (should have rank high enough) to derive
      rotation
    """
    if nt is None:
        nt = ns
    # figure out some "random" rotation
    d = max(ns, nt)
    if data is None:
        data = np.random.normal(size=(d * 10, d))
    _u, _s, _vh = np.linalg.svd(data[:, :d])
    R = _vh[:ns, :nt]
    if ns == nt:
        # Test if it is indeed a rotation matrix ;)
        # Lets flip first axis if necessary
        if np.linalg.det(R) < 0:
            R[:, 0] *= -1.0
    return R
