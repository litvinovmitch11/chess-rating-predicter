from aiogram import Router

from config import PATH_TO_MODEL
from tgBot.model.rating_predictor_model import RatingPredictorModel


class MyRouter(Router):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = RatingPredictorModel(PATH_TO_MODEL)
