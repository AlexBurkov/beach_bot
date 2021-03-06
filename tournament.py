from functools import cmp_to_key
import random

class Tournament(object):
    def __init__(self, players):
        self.battles = []
        self.players = players
        self.games = {}
        self.missedRound = {}
        self.lastLosers = []
        self.battleSets = {}
        self.team_sets = {}
        self.teams_last_round = {}
        self.current_round = 0

    def get_team_hash(self, team):
        return ( min(team[0], team[1]), max(team[0], team[1]) )

    def get_battle_hash(self, team1, team2):
        team1_hash = self.get_team_hash(team1)
        team2_hash = self.get_team_hash(team2)
        return ( min(team1_hash, team2_hash), max(team1_hash, team2_hash) )

    def add_battle(self, winners, losers):
        self.current_round += 1
        self.battles.append((winners, losers))

        battle_hash = self.get_battle_hash(winners, losers)
        self.battleSets[battle_hash] = self.battleSets.get(battle_hash, 0) + 1

        self.teams_last_round[self.get_team_hash(winners)] = self.current_round
        self.teams_last_round[self.get_team_hash(losers)] = self.current_round
        
        for player in self.players[:4]:
            self.games[player] = self.games.get(player, 0) + 1
        
        for player in self.players[4:]:
            self.missedRound[player] = self.current_round

        self.lastLosers = losers

    def get_battles_history(self):
        return self.battles

    def get_battle(self):
        def cmp_by_order_playing(p1, p2):
            if self.games.get(p1, 0) != self.games.get(p2, 0):
                return self.games.get(p1, 0) - self.games.get(p2, 0)

            if self.missedRound.get(p1, 100) != self.missedRound.get(p2, 100):
                return self.missedRound.get(p2, 100) - self.missedRound.get(p1, 100)

            if p1 in self.lastLosers and p2 not in self.lastLosers:
                return 1

            if p2 in self.lastLosers and p1 not in self.lastLosers:
                return -1

            return 0

        def priority_splitting(team1, team2):
            return sum([
                self.battleSets.get((min(team1, team2), max(team1, team2)), 0) * 100000,
                (self.team_sets.get(team1, 0) + self.team_sets.get(team2, 0)) * 1000,
                (self.teams_last_round.get(team1, -1) + self.teams_last_round.get(team2, -1)) * 10
            ])
            
        def cmp_by_priority(option1, option2):
            return priority_splitting(option1[0], option1[1]) - priority_splitting(option2[0], option2[1])

        if self.current_round != 0:
            random.shuffle(self.players)
        self.players = sorted(self.players, key=cmp_to_key(cmp_by_order_playing))
        firstPlayers = self.players[:4]

        print("round {0}:".format(self.current_round))
        firstPlayers.sort()
        battle_teams = [
            ((firstPlayers[0], firstPlayers[1]), (firstPlayers[2], firstPlayers[3])),
            ((firstPlayers[0], firstPlayers[2]), (firstPlayers[1], firstPlayers[3])),
            ((firstPlayers[0], firstPlayers[3]), (firstPlayers[1], firstPlayers[2]))
        ]
        
        random.shuffle(battle_teams)
        battle_team = sorted(battle_teams, key=cmp_to_key(cmp_by_priority))[0]
        print("play: " + battle_team[0][0] + " " + battle_team[0][1] + " <-> " + battle_team[1][0] + " " + battle_team[1][1])
        print("sit: " + " ".join(self.players[4:]))

        return battle_team
