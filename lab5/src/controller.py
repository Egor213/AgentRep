from ta import TA
from attacker_ta import create_attacker_ta
from goalie_ta import create_goalie_ta
from defender_ta import create_defender_ta
from ta_manager import TAManager


class Controller:

    def __init__(self, role, team, side, player_number):

        self.manager = TAManager()

        if role == "goalie":
            ta = create_goalie_ta()
        elif role == "attacker":
            ta = create_attacker_ta()
        else:
            ta = create_defender_ta()

        self.ta = TA(ta)

        self.team = team
        self.side = side
        self.player_number = player_number


    def reset(self):
        self.ta.reset()


    def decide(
        self,
        visible_objects,
        game_on,
        time_cycle
    ):

        if not game_on:
            return None

        self.manager.update(
            visible_objects,
            self.team,
            self.side,
            self.player_number,
            time_cycle
        )

        return self.ta.step(self.manager)
