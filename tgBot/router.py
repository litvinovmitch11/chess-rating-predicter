import pandas as pd

from aiogram import Router

from config import PATH_TO_MODEL
from model import MyModel


class MyRouter(Router):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = App()
        self.app.load_model(PATH_TO_MODEL)


class App:
    def __init__(self):
        self.loaded_model = None

    def load_model(self, path_to_model):
        self.loaded_model = MyModel(path_to_model)

    def get_prediction(self, game):
        if self.loaded_model is None:
            raise Exception('Model was not loaded')

        df = pd.DataFrame({"game": [game]})
        return self.loaded_model.predict(df).rating
