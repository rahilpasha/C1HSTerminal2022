import gamelib
import random
# import math
# import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips:

  - You can analyze action frames by modifying on_action_frame function
  - The GameState.map object can be manually manipulated to create hypothetical
  board states. Though, we recommended making a copy of the map to preserve
  the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.

        self.da_strat(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def da_strat(self, game_state):
        """
        At the start of the game we will have a defensive approach and potentially send in a couple interceptors to defend and score some quick points
        Then we will transition to a funnel strategy to bring all enemy units to a centralized area where we will also deploy scouts
        When the oppoenents have a large amount of stationary units near the front the demolisher strategy will be put in place
        """

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            self.starter_defense(game_state)
        else:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 20 and game_state.get_resource(1, 0) >= 12 and game_state.get_resource(0, 0) >= 19:
                self.demolisher_strategy(game_state)
            else:

                self.funnel(game_state)

        self.mud_defenses(game_state)

    def starter_defense(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets and walls that attack and stop enemy units
        wall_locations = [[0, 13], [1, 13], [2, 13], [3, 13], [24, 13], [25, 13], [26, 13], [27, 13]]
        turret_locations = [[3, 12], [24, 12], [5, 11], [9, 11], [13, 11], [17, 11], [21, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(WALL, wall_locations)
        game_state.attempt_spawn(TURRET, turret_locations)

        # upgrade sattic walls and turrets so they deal/take more damage
        game_state.attempt_upgrade([[3, 12], [24, 12]])
        game_state.attempt_upgrade([[2, 13], [3, 13], [24, 13], [25, 13]])

        # upgrade non-static turrets if we have remaining points
        game_state.attempt_upgrade([[5, 11], [21, 11], [9, 11], [17, 11], [13, 11]])

        # remove non-static turrets so they can be more flexable in future turns
        game_state.attempt_remove([[5, 11], [9, 11], [13, 11], [17, 11], [21, 11]])

        # remove non-static walls so they can be more flexable in future turns
        game_state.attempt_remove([[0, 13], [1, 13], [26, 13], [27, 13]])

    def mud_defenses(self, game_state):

        busts = [[2, 13], [3, 13], [24, 13], [25, 13], [10, 7], [11, 7], [12, 7], [13, 7], [14, 7], [15, 7], [16, 7], [17, 7], [3, 12], [24, 12]]
        for i in busts:
            unit = game_state.contains_stationary_unit(i)
            if unit and unit.health / unit.max_health <= .6:
                game_state.attempt_remove(i)

    def funnel(self, game_state):

        # place the constat walls and turrets
        stationary_walls = [[2, 13], [3, 13], [24, 13], [25, 13], [10, 7], [11, 7], [12, 7], [13, 7], [14, 7], [15, 7], [16, 7], [17, 7]]
        stationary_turrets = [[3, 12], [24, 12]]
        game_state.attempt_spawn(WALL, stationary_walls)
        game_state.attempt_spawn(TURRET, stationary_turrets)

        if [13, 0] == self.least_damage_spawn_location(game_state, [[13, 0], [14, 0]]):
            # right funnel

            # place the minimum required walls and turrets for a funnel
            right_walls = [[0, 13], [1, 13], [22, 13], [23, 13], [3, 10], [19, 10], [20, 10], [21, 10], [22, 10], [4, 9], [5, 8], [18, 8], [19, 8], [6, 7], [7, 7], [8, 7], [9, 7]]
            right_turrets = [[1, 12], [2, 12], [22, 12], [23, 12], [2, 11], [23, 11], [19, 9], [20, 9], [7, 6], [16, 6], [17, 6]]
            game_state.attempt_spawn(WALL, right_walls)
            game_state.attempt_spawn(TURRET, right_turrets)

            if game_state.get_resource(1, 0) < 11 or game_state.turn_number % 2 != 1:
                # if we aren't attacking on the right then patch the wall_locations
                game_state.attempt_spawn(WALL, [[27, 13], [26, 13]])
                game_state.attempt_remove([[27, 13], [26, 13]])

            # place starter supports
            game_state.attempt_spawn(SUPPORT, [[12, 3], [11, 4]])

            # upgrade important walls and turrets
            game_state.attempt_upgrade(stationary_turrets)
            game_state.attempt_upgrade([[25, 13], [0, 13], [1, 13], [24, 13]])
            game_state.attempt_upgrade([[23, 12], [3, 12], [22, 12]])
            game_state.attempt_upgrade([[12, 3], [11, 4]])

            # place more supports
            support_locations = [[13, 2], [10, 5], [16, 4], [15, 3], [14, 5], [15, 5], [16, 5], [17, 5], [13, 4], [14, 4], [15, 4]]
            game_state.attempt_spawn(SUPPORT, support_locations)

            # remove the non-static walls and turrets
            game_state.attempt_remove(right_walls)
            game_state.attempt_remove(right_turrets)

            if game_state.get_resource(1, 0) >= 11 and game_state.turn_number % 2 == 1:
                # attack strat

                # check if we have at least  17 mobility points
                if game_state.get_resource(1, 0) >= 17:

                    # split into three squads: interceptors at the front and two squads of scouts at the back
                    squad = int(game_state.get_resource(1, 0) // 3)
                    game_state.attempt_spawn(INTERCEPTOR, [26, 12], (squad * 2) // 3)
                    game_state.attempt_spawn(SCOUT, [13, 0], squad)
                    game_state.attempt_spawn(SCOUT, [11, 2], 100)

                else:

                    # split into two squads of scouts that are staggered at the back
                    squad = int(game_state.get_resource(1, 0) // 2)
                    game_state.attempt_spawn(SCOUT, [13, 0], (squad * 3) // 4)
                    game_state.attempt_spawn(SCOUT, [11, 2], 100)

        else:
            # left funnel

            # place the minimum required walls and turrets for a funnel
            left_walls = [[4, 13], [5, 13], [26, 13], [27, 13], [5, 10], [6, 10], [7, 10], [8, 10], [24, 10], [23, 9], [8, 8], [9, 8], [22, 8], [18, 7], [19, 7], [20, 7], [21, 7]]
            left_turrets = [[4, 12], [5, 12], [25, 12], [26, 12], [4, 11], [25, 11], [8, 9], [9, 9], [10, 6], [11, 6], [20, 6]]
            game_state.attempt_spawn(WALL, left_walls)
            game_state.attempt_spawn(TURRET, left_turrets)

            if game_state.get_resource(1, 0) < 11 or game_state.turn_number % 2 != 1:
                # if we aren't attacking on the right then patch the wall_locations
                game_state.attempt_spawn(WALL, [[0, 13], [1, 13]])
                game_state.attempt_remove([[0, 13], [1, 13]])

            # place starter supports
            game_state.attempt_spawn(SUPPORT, [[15, 3], [16, 4]])

            # upgrade important walls and turrets
            game_state.attempt_upgrade(stationary_turrets)
            game_state.attempt_upgrade([[2, 13], [27, 13], [26, 13], [3, 13]])
            game_state.attempt_upgrade([[4, 12], [25, 12], [5, 12]])
            game_state.attempt_upgrade([[15, 3], [16, 4]])

            # place more supports
            support_locations = [[14, 2], [17, 5], [11, 4], [12, 3], [10, 5], [11, 5], [12, 5], [13, 5], [13, 4], [12, 4], [11, 4]]
            game_state.attempt_spawn(SUPPORT, support_locations)
            game_state.attempt_upgrade(support_locations)

            # remove the non-static walls and turrets
            game_state.attempt_remove(left_walls)
            game_state.attempt_remove(left_turrets)

            if game_state.get_resource(1, 0) >= 11 and game_state.turn_number % 2 == 1:
                # attack strat

                # check if we have at least  17 mobility points
                if game_state.get_resource(1, 0) >= 17:

                    # split into three squads: interceptors at the front and two squads of scouts at the back
                    squad = int(game_state.get_resource(1, 0) // 3)
                    game_state.attempt_spawn(INTERCEPTOR, [1, 12], (squad * 2) // 3)
                    game_state.attempt_spawn(SCOUT, [14, 0], squad)
                    game_state.attempt_spawn(SCOUT, [16, 2], 100)

                else:

                    # split into two squads of scouts that are staggered at the back
                    squad = int(game_state.get_resource(1, 0) // 2)
                    game_state.attempt_spawn(SCOUT, [14, 0], (squad * 3) // 4)
                    game_state.attempt_spawn(SCOUT, [16, 2], 100)

    def demolisher_strategy(self, game_state):
        """
        Build a line of walls so our demolisher can attack from long range.
        """

        # Now let's build out a line of walls. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(1, 25):
            game_state.attempt_spawn(WALL, [x, 12])
            game_state.attempt_remove([x, 12])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 6 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [2, 11], 6)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1] + 1]
            game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)

        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]

            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile
            units can occupy the same space.
            """

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
