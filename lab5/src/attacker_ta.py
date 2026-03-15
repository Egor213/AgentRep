def create_attacker_ta():

    def search_ball(mgr, s):
        return ("turn", "40")

    def go_ball(mgr, s):

        if not mgr.getVisible("b"):
            return ("turn", "30")

        angle = mgr.getAngle("b")
        dist = mgr.getDistance("b")

        if abs(angle) > 7:
            return ("turn", str(int(angle)))

        if dist > 1.5:
            return ("dash", "80")

        return ("dash", "40")

    def kick(mgr, s):

        goal = mgr.enemy_goal_key()

        if mgr.getVisible(goal):
            return ("kick", f"100 {int(mgr.getAngle(goal))}")

        return ("kick", "40 20")


    ta = {
        '__start__': 'start',
        'start': [
            (
                lambda m, s: not m.getVisible("b"),
                search_ball,
                'start'
            ),

            (
                lambda m, s: m.getVisible("b") and m.getDistance("b") > 0.7,
                go_ball,
                'start'
            ),

            (
                lambda m, s: m.getVisible("b") and m.getDistance("b") <= 0.7,
                kick,
                'start'
            )
        ]
    }
    return ta