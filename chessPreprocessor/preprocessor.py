import chess.pgn
import io
import pandas as pd

from stockfish import Stockfish


class Preprocessor:
    def __init__(self, path_to_stockfish="/usr/games/stockfish"):
        """
        Initializes the Preprocessor object
        :param path_to_stockfish: path to the stockfish binary
        """
        self._stockfish = Stockfish(path_to_stockfish)
        self._game = None
        self._wdl_stat = None
        self._evaluation_stat = None
        self._best_lines = None

    def read_pgn_from_string(self, pgn):
        """
        Load game from string moves (like "1. e4 e5 2. Bc4 d6 3. Qh5 Nf6 4. Qxf7#")
        :param pgn: string with moves in PGN
        :return: None
        """
        self._game = chess.pgn.read_game(io.StringIO(pgn))
        self._wdl_stat = None
        self._evaluation_stat = None
        self._best_lines = None

    def calculate_wdl(self):
        """
        Calculate wdl statistic for loaded game
        :return: None
        """
        if self._game is None:
            raise Exception("No game loaded")
        self._wdl_stat = []
        self._stockfish.set_position()
        for move in self._game.mainline_moves():
            self._stockfish.make_moves_from_current_position([move])
            self._wdl_stat.append(self._stockfish.get_wdl_stats())

    def calculate_evaluation_stat(self):
        """
        Calculate evaluation statistic for loaded game
        :return: None
        """
        if self._game is None:
            raise Exception("No game loaded")
        self._evaluation_stat = []
        self._stockfish.set_position()
        for move in self._game.mainline_moves():
            self._stockfish.make_moves_from_current_position([move])
            self._evaluation_stat.append(self._stockfish.get_evaluation())

    def calculate_n_best_lines(self, n=0):
        """
        Calculate n best lines for loaded game per move
        :param n: count of best lines to calculate
        :return: None
        """
        if self._game is None:
            raise Exception("No game loaded")
        self._best_lines = {}
        for i in range(n):
            self._best_lines[i] = []
        self._stockfish.set_position()
        for move in self._game.mainline_moves():
            top_moves = self._stockfish.get_top_moves(n)
            for i in range(n):
                self._best_lines[i].append(top_moves[i])
            self._stockfish.make_moves_from_current_position([move])

    def get_stats_per_move(self, add_wdl_stats=False, add_evaluation_stats=False, n_best_lines=0):
        """
        Get stats per move for one game
        :param add_wdl_stats: bool flag for adding wdl stats
        :param add_evaluation_stats: bool flag for adding evaluation stats
        :param n_best_lines: count of best lines for adding to stats
        :return: dataframe with stats per move
        """
        columns = ["move"]
        moves = list(map(str, self._game.mainline_moves()))
        data = [moves]
        if add_wdl_stats:
            if self._wdl_stat is None:
                raise Exception("No wdl stat")
            columns.extend(["win", "draw", "lose"])
            win, draw, lose = [], [], []
            for item in self._wdl_stat:
                if item:
                    win.append(item[0] / 1000)
                    draw.append(item[1] / 1000)
                    lose.append(item[2] / 1000)
                else:
                    win.append(None)
                    draw.append(None)
                    lose.append(None)
            data.extend([win, draw, lose])
        if add_evaluation_stats:
            if self._evaluation_stat is None:
                raise Exception("No evaluation stat")
            columns.extend(["centipawns", "moves_to_force_mate"])
            centipawns, moves_to_mate = [], []
            for item in self._evaluation_stat:
                if item["type"] == "cp":
                    centipawns.append(item["value"])
                    moves_to_mate.append(None)
                if item["type"] == "mate":
                    centipawns.append(None)
                    moves_to_mate.append(item["value"])
            data.extend([centipawns, moves_to_mate])
        if n_best_lines:
            if self._best_lines is None:
                raise Exception("No best lines")
            if len(self._best_lines) < n_best_lines:
                raise Exception("Not enough best lines")
            for i in range(n_best_lines):
                columns.extend([
                    f"best_line_{i + 1}_move",
                    f"best_line_{i + 1}_centipawns",
                    f"best_line_{i + 1}_moves_to_force_mate",
                ])
            for i in range(n_best_lines):
                moves, centipawns, moves_to_mate = [], [], []
                for item in self._best_lines[i]:
                    moves.append(item["Move"])
                    centipawns.append(item["Centipawn"])
                    moves_to_mate.append(item["Mate"])
                data.extend([moves, centipawns, moves_to_mate])
        return pd.DataFrame(columns=columns, data=zip(*data))

    def get_stats_for_game(self):
        """
        Calculate common stats for loaded game
        :return: dataframe with common stats
        """
        pass
