from modules.chessPreprocessor.preprocessor import Preprocessor
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import chess.pgn
from modules.utils.rating_to_category import rating_to_number
import time

THREAD_COUNT = 8
STEP = 65
START = 480


# Т.е. каждый поток будет выполнять отрезки вида:
# [START, STEP + START), [STEP + START, 2*STEP + START), ... , [STEP*(THREAD_COUNT-1) + START, STEP*THREAD_COUNT + START)

def get_preprocessed_df(l, r, moves, _game_ids):
    print(f"Начал обработку отрезка [{l}, {r})\n")
    # count in [l, r)
    _all_stats = []
    for ind in range(l, r, 1):
        _proc = Preprocessor()
        _proc.read_pgn_from_string(moves[ind])
        _proc.calculate_wdl()
        _proc.calculate_evaluation_stat()
        _proc.calculate_n_best_lines(n=3)
        df_stat = _proc.get_stats_per_move(add_wdl_stats=True, add_evaluation_stats=True, n_best_lines=3)
        df_stat['game_id'] = _game_ids[ind]
        df_stat['move_number'] = np.arange(df_stat['game_id'].shape[0])
        _all_stats.append(df_stat)
    print(f"Отрезок [{l}, {r}) обработан за {time.time() - start_time_proc}\n")

    return _all_stats


proc = Preprocessor()
rating_num_count = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
GAME_COUNT = 4702  # столько всего подходящих игр в нашем датасете (выявлено в файле second.ipynb)
MAX_USER_NUM = 1000  # хотим ограничить количество юзеров по каждой категории

i = 0
game_id = 0
required_headers = ['Event', 'Result', 'WhiteElo', 'BlackElo', 'WhiteRatingDiff', 'BlackRatingDiff', 'ECO', 'Opening',
                    'TimeControl', 'Termination']

events = np.empty(GAME_COUNT, dtype=object)
results = np.empty(GAME_COUNT, dtype=object)

white_elo = np.empty(GAME_COUNT, dtype=int)
black_elo = np.empty(GAME_COUNT, dtype=int)
white_rating_diff = np.empty(GAME_COUNT, dtype=int)
black_rating_diff = np.empty(GAME_COUNT, dtype=int)

ecos = np.empty(GAME_COUNT, dtype=object)
openings = np.empty(GAME_COUNT, dtype=object)

time_control = np.empty(GAME_COUNT, dtype=object)
termination = np.empty(GAME_COUNT, dtype=object)

game_ids = np.empty(GAME_COUNT, dtype=int)

all_moves = []
with open("../data/lichess_db_standard_rated_2013-01.pgn") as pgn:
    start_time = time.time()
    print("Начал читать из файла pgn")
    while True:
        game = chess.pgn.read_game(pgn)
        if game is None or i >= GAME_COUNT:
            break

        if not all(header in game.headers for header in required_headers) or '?' in game.headers['Event'] + \
                game.headers['Result'] + game.headers['WhiteElo'] + game.headers['BlackElo'] + game.headers[
            'WhiteRatingDiff'] + game.headers['BlackRatingDiff'] + game.headers['ECO'] + game.headers[
            'Opening'] + game.headers['TimeControl'] + game.headers['Termination']:
            continue
        game_white_elo = int(game.headers['WhiteElo'])
        white_num = rating_to_number(game_white_elo)

        game_black_elo = int(game.headers['BlackElo'])
        black_num = rating_to_number(game_black_elo)
        if rating_num_count[white_num] < MAX_USER_NUM or rating_num_count[black_num] < MAX_USER_NUM:
            rating_num_count[white_num] += 1
            rating_num_count[black_num] += 1

            events[i] = game.headers['Event']
            results[i] = game.headers['Result']
            white_elo[i] = game_white_elo
            black_elo[i] = game_black_elo
            white_rating_diff[i] = game.headers['WhiteRatingDiff']
            black_rating_diff[i] = game.headers['BlackRatingDiff']
            ecos[i] = game.headers['ECO']
            openings[i] = game.headers['Opening']
            time_control[i] = game.headers['TimeControl']
            termination[i] = game.headers['Termination']
            game_ids[i] = game_id

            all_moves.append(str(game.mainline_moves()))
            i += 1
        game_id += 1

df = pd.DataFrame({'Events': events, 'results': results, 'white_elo': white_elo, 'black_elo': black_elo,
                   'white_rating_diff': white_rating_diff, 'black_rating_diff': black_rating_diff, 'ecos': ecos,
                   'openings': openings, 'time_control': time_control, 'termination': termination,
                   'game_id': game_ids})

all_res = []
print(f"Прочитал из файла. Время, которое на это ушло: {time.time() - start_time}.\n"
      f"Количество прочитанных игр: {i}.\n"
      f"Запускаю потоки\n")
start_time_proc = time.time()
with ThreadPoolExecutor() as executor:
    all_future = [executor.submit(get_preprocessed_df, i * STEP + START, (i + 1) * STEP + START, all_moves, game_ids)
                  for i in range(THREAD_COUNT)]
    for future in all_future:
        all_res += future.result()
print(
    f"Потоки завершились успешно. Общее время выполнения потоков: {time.time() - start_time_proc}.\n"
    f"Общее время выполнения программы: {time.time() - start_time}")
res = pd.concat([i for i in all_res])
res.to_csv(f"from_{START}_to_{START + THREAD_COUNT * STEP}.csv", encoding='utf-8', index=False)
