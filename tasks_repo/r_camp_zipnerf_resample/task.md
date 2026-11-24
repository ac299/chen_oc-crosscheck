In this repository, the function `stepfun.resample` in `internal/stepfun.py` has lost its implementation: its body is `raise NotImplementedError`. Implement it.

Signature (line 212 of `internal/stepfun.py`):
```python
def resample(t, tp, vp, use_avg=False):
```

Requirement:
- Functionality: Resamples a step function defined by pairs of time points (tp) and their corresponding values (vp) into new intervals specified by t. It supports both summation and averaging methods for resampling.
- Arguments: :param t: Tensor. The endpoints into which the step function is resampled. It is used as the new time points for resampling.
:param tp: Tensor. The original time points of the step function being resampled. It defines the intervals of the original step function.
:param vp: Tensor. The values of the step function at the original time points (tp). These values are resampled according to the new intervals defined by t.
:param use_avg: Bool, optional. Determines the resampling method. If False, the function sums the values of the step function for each interval in `t`. If True, it returns the average value, weighted by the width of each interval in `t`.
:return: Tensor. The values of the resampled step function at the new intervals defined by t.

Keep the signature and the rest of the repository unchanged except where the implementation
needs it. Tests for this function are not provided; the repository's other code and tests show
how it is used. Run Python and tests with `python` from the repository root.
