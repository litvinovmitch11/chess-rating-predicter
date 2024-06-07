import dill
import numpy as np
import pandas as pd
import pickle

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from modules.chessPreprocessor.preprocessor import Preprocessor
from modules.utils.rating_to_category import rating_to_number


# Обёртка для модели
class TextModelWrapper:
    def __init__(self, model):
        self.model = model
        self.proc = Preprocessor()

    def get_stat(self, moves: str):
        self.proc.read_pgn_from_string("1. e4 e5 2. Bc4 d6 3. Qh5 Nf6 4. Qxf7#")
        self.proc.calculate_wdl()
        self.proc.calculate_evaluation_stat()
        self.proc.calculate_n_best_lines(n=3)
        return self.proc.get_stats_per_move(add_wdl_stats=True, add_evaluation_stats=True, n_best_lines=3)

    def predict(self, text):
        df_stat = self.get_stat(text)

        features = self._extract_features(df_stat)

        return self.model.predict(features)

    def percent_best3_move(self, df_stat):
        matches = df_stat[
            (df_stat['move'] == df_stat['best_line_1_move']) |
            (df_stat['move'] == df_stat['best_line_2_move']) |
            (df_stat['move'] == df_stat['best_line_3_move'])
            ]
        return matches.shape[0] / df_stat.shape[0]

    def min_max_delta_centipawns(self, df_stat, ost=0, want=0):
        # ost = 0, если смотрим на ходы белых
        # want = 0, если интересуемся минимумом, want = 1, если нужен максимум и want = 2, если медиана
        last = 0
        _id = 0
        min_max_median_delta = (1000, -1000, 0)
        for centipawns in df_stat['centipawns']:
            if _id % 2 == ost and not np.isnan(centipawns):
                min_max_median_delta = (
                    min(min_max_median_delta[0], centipawns - last), max(min_max_median_delta[1], centipawns - last),
                    min_max_median_delta[2] + centipawns)
            last = centipawns
            _id += 1
        min_max_median_delta = (
            min_max_median_delta[0] / 1000, min_max_median_delta[1] / 1000, (min_max_median_delta[2] / _id) / 1000)
        if want == 0:
            return min_max_median_delta[0]
        elif want == 1:
            return min_max_median_delta[1]
        return min_max_median_delta[2]

    def _extract_features(self, df_stat):
        return pd.DataFrame({
            "white_percent_best_move": [self.percent_best3_move(df_stat)],
            "min_delta_centipawns_white": [self.min_max_delta_centipawns(df_stat, 0, 0)],
            "max_delta_centipawns_white": [self.min_max_delta_centipawns(df_stat, 0, 1)],
            "median_centipawns_white": [self.min_max_delta_centipawns(df_stat, 0, 2)]
        })

    # Вот это вообще интересно) Без этих строчек падаем с ошибкой TypeError: cannot pickle '_thread.lock' object
    # Потому что self.proc содержит в себе _thread.lock, который не перемещаемый
    # Ну короче полное веселье)
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['proc']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.proc = Preprocessor()


def percent_best_move(game_id, ost=0):
    # ost = 0 если смотрим ходы белых, иначе ost = 1
    move_in_game = df_moves[(df_moves['game_id'] == game_id) & (df_moves['move_number'] % 2 == ost)]
    matches = move_in_game[
        (move_in_game['move'] == move_in_game['best_line_1_move']) |
        (move_in_game['move'] == move_in_game['best_line_2_move']) |
        (move_in_game['move'] == move_in_game['best_line_3_move'])
        ]
    return matches.shape[0] / move_in_game.shape[0]


def min_max_delta_centipawns(game_id, ost=0, want=0):
    # ost = 0, если смотрим на ходы белых
    # want = 0, если интересуемся минимумом, want = 1, если нужен максимум и want = 2, если медиана
    last = 0
    _id = 0
    min_max_median_delta = (1000, -1000, 0)
    for centipawns in df_moves[df_moves['game_id'] == game_id].sort_values(by='move_number')['centipawns']:
        if _id % 2 == ost and not np.isnan(centipawns):
            min_max_median_delta = (
                min(min_max_median_delta[0], centipawns - last), max(min_max_median_delta[1], centipawns - last),
                min_max_median_delta[2] + centipawns)
        last = centipawns
        _id += 1
    min_max_median_delta = (
        min_max_median_delta[0] / 1000, min_max_median_delta[1] / 1000, (min_max_median_delta[2] / _id) / 1000)
    if want == 0:
        return min_max_median_delta[0]
    elif want == 1:
        return min_max_median_delta[1]
    return min_max_median_delta[2]


def min_centipawns_white(game_id):
    return min_max_delta_centipawns(game_id, ost=0, want=0)


def max_centipawns_white(game_id):
    return min_max_delta_centipawns(game_id, ost=0, want=1)


def median_centipawns_white(game_id):
    return min_max_delta_centipawns(game_id, ost=0, want=2)


def min_centipawns_black(game_id):
    return min_max_delta_centipawns(game_id, ost=1, want=0)


def max_centipawns_black(game_id):
    return min_max_delta_centipawns(game_id, ost=1, want=1)


def median_centipawns_black(game_id):
    return min_max_delta_centipawns(game_id, ost=1, want=2)


class RatingPredictorModel:
    def __init__(self, path=None):
        if path is None:
            self.model = LogisticRegression()
            self.wrapper = TextModelWrapper(self.model)
        else:
            self.wrapper = dill.load(open(path, "rb"))

    def fit(self):
        df_first240 = pd.read_csv("../../data/first_240.csv")
        df_from_240_to_360 = pd.read_csv("../../data/from_240_to_360.csv")
        df_from_360_to_480 = pd.read_csv("../../data/from_360_480.csv")
        df_moves = pd.concat([df_first240, df_from_240_to_360, df_from_360_to_480])

        GAME_COUNT = 480
        df_games = pd.read_csv("../../data/clear_data.csv")
        df_games = df_games.head(GAME_COUNT)

        df_games['white_percent_best_move'] = df_games['game_id'].apply(percent_best_move)
        df_games['white_rating_num'] = df_games['white_elo'].apply(rating_to_number)
        df_games['min_delta_centipawns_white'] = df_games['game_id'].apply(min_centipawns_white)
        df_games['max_delta_centipawns_white'] = df_games['game_id'].apply(max_centipawns_white)
        df_games['median_centipawns_white'] = df_games['game_id'].apply(median_centipawns_white)

        df_train = df_games[['white_percent_best_move', 'min_delta_centipawns_white', 'max_delta_centipawns_white',
                             'median_centipawns_white']]
        x_train_white, x_test_white, y_train_white, y_test_white = train_test_split(
            df_train, df_games['white_rating_num'],
            train_size=0.8,
            random_state=42)
        self.model.fit(x_train_white, y_train_white)
        self.wrapper = TextModelWrapper(self.model)

    def predict(self, game):
        return self.wrapper.predict(game)[0]

    def dump(self, path):
        dill.dump(self.wrapper, open(path, 'wb'))


# if __name__ == "__main__":
#     model = LogisticRegression()
#
#     df_first240 = pd.read_csv("../../data/first_240.csv")
#     df_from_240_to_360 = pd.read_csv("../../data/from_240_to_360.csv")
#     df_from_360_to_480 = pd.read_csv("../../data/from_360_480.csv")
#     df_moves = pd.concat([df_first240, df_from_240_to_360, df_from_360_to_480])
#
#     GAME_COUNT = 480
#     df_games = pd.read_csv("../../data/clear_data.csv")
#     df_games = df_games.head(GAME_COUNT)
#
#     df_games['white_percent_best_move'] = df_games['game_id'].apply(percent_best_move)
#     df_games['white_rating_num'] = df_games['white_elo'].apply(rating_to_number)
#     df_games['min_delta_centipawns_white'] = df_games['game_id'].apply(min_centipawns_white)
#     df_games['max_delta_centipawns_white'] = df_games['game_id'].apply(max_centipawns_white)
#     df_games['median_centipawns_white'] = df_games['game_id'].apply(median_centipawns_white)
#
#     df_train = df_games[['white_percent_best_move', 'min_delta_centipawns_white', 'max_delta_centipawns_white',
#                          'median_centipawns_white']]
#     x_train_white, x_test_white, y_train_white, y_test_white = train_test_split(
#         df_train, df_games['white_rating_num'],
#         train_size=0.8,
#         random_state=42)
#     model.fit(x_train_white, y_train_white)
#
#     # Создание обёртки
#     wrapped_model = TextModelWrapper(model)
#
#     with open('../content/model.pkl', 'wb') as f:
#         pickle.dump(wrapped_model, f)
#
#     print("Модель успешно создана!")
