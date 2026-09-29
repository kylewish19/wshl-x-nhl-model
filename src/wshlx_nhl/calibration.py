from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression


class ProbabilityCalibrator:
    def __init__(self):
        self.model = IsotonicRegression(out_of_bounds="clip")
        self.fitted = False

    def fit(self, raw_probability, y_true):
        p = np.asarray(raw_probability, dtype=float)
        y = np.asarray(y_true, dtype=float)
        mask = np.isfinite(p) & np.isfinite(y)
        if mask.sum() >= 100 and len(np.unique(y[mask])) > 1:
            self.model.fit(p[mask], y[mask])
            self.fitted = True
        return self

    def transform(self, raw_probability):
        p = np.asarray(raw_probability, dtype=float)
        if not self.fitted:
            return np.clip(p, 0.001, 0.999)
        return np.clip(self.model.predict(p), 0.001, 0.999)
