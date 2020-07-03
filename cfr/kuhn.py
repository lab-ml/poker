from typing import List, NewType, Dict, cast

import numpy as np
from labml import logger, experiment
from cfr import History as _History, InfoSet as _InfoSet, CFR

Player = NewType('Player', int)
Action = NewType('Action', str)

ACTIONS = cast(List[Action], ['p', 'b'])
CHANCES = cast(List[Action], ['A', 'K', 'Q'])
PLAYERS = cast(List[Player], [0, 1])


class InfoSet(_InfoSet):
    def __init__(self, key: str):
        super().__init__(key)

    def actions(self) -> List[Action]:
        return ACTIONS

    def __repr__(self):
        total = sum(r for r in self.average_strategy.values())
        total = max(total, 1e-6)
        bet = self.average_strategy['b'] / total
        return f'{bet * 100: .1f}%'


class History(_History):
    history: str

    def __init__(self, history: str = ''):
        self.history = history

    def is_terminal(self):
        if len(self.history) <= 2:
            return False
        if self.history[-1] == 'p':
            return True
        if self.history[-2:] == 'bb':
            return True

        return False

    def _terminal_utility(self) -> float:
        winner = -1 + 2 * (self.history[0] < self.history[1])

        if self.history[-2:] == 'bp':
            return 1
        if self.history[-2:] == 'bb':
            return winner * 2
        if self.history[-1] == 'p':
            return winner

    def terminal_utility(self, i: Player) -> float:
        if i == PLAYERS[0]:
            return self._terminal_utility()
        else:
            return -1 * self._terminal_utility()

    def is_chance(self) -> bool:
        return len(self.history) < 2

    def __add__(self, other: Action):
        return History(self.history + other)

    def player(self) -> Player:
        return cast(Player, len(self.history) % 2)

    def sample_chance(self) -> Action:
        while True:
            r = np.random.randint(len(CHANCES))
            chance = CHANCES[r]
            for c in self.history:
                if c == chance:
                    chance = None
                    break

            if chance is not None:
                return cast(Action, chance)

    def __repr__(self):
        return repr(self.history)

    def info_set_key(self) -> str:
        i = self.player()
        return self.history[i] + self.history[2:]

    def new_info_set(self) -> InfoSet:
        return InfoSet(self.info_set_key())


def create_new_history():
    return History()


if __name__ == '__main__':
    experiment.create(name='kuhn_poker', writers={'sqlite'})
    experiment.start()
    cfr = CFR(create_new_history=create_new_history,
              epochs=100_000,
              save_frequency=100)
    cfr.solve()
