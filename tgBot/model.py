import dill
import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator


class RandomClassifier(BaseEstimator):
    def __init__(self):
        pass

    def fit(self, X, y):
        return self

    def predict(self, X):
        return pd.DataFrame({"rating": np.random.randint(low=0, high=3, size=X.shape[0])})


class MyModel:
    def __init__(self, path=None):
        if path is None:
            self.model = RandomClassifier()
        else:
            self.model = dill.load(open(path, "rb"))

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def dump(self, path):
        dill.dump(self.model, open(path, 'wb'))
