#!/usr/bin/python
# -*- coding: utf8 -*-

import telebot
from telebot import types

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import json
import random
import datetime
from functools import cmp_to_key


ENV = {}

class User(object):
    def __init__(self, name):
        self.name = name
        self.rating = 1400
        self.wonGames = 0
        self.lostGames = 0
        self.historyRatings = []
        self.aliases = []
        self.telegramUsername = None
        self.telegramUserId = None

class Game(object):
    def __init__(self):
        self.START_RATING = 1400
        self.COEF_RATING_K = 16

        self.data = {}
        self.aliases = {
            "Калужин": [ "Я", "К" ],
            "Бурков": [ "Б" ],
            "Ногтев": [ "НГ", "Ног", "Серж", "Сер" ],
            "СашаАндрея": [ "СА", "СаняАндреевский" ],
            "Сильвестров": [ "АС", "А" ],
            "Новиков": [ "СН", "Нов" ],
            "Шавейников": [ "Д", "Ш" ],
            "Антонов": [ "Ж" ],
            "Наташа": [ "Н" ]
        }
        self.checkAliases()
        self.officialMembers = [ "Калужин", "Бурков", "Ногтев", "Сильвестров", "Новиков", "Шавейников", "Антонов", "Наташа" ]

    def checkAliases(self):
        uniqueNames = set()
        for arr in self.aliases.values():
            for alias in arr:
                if alias in uniqueNames:
                    raise "Дублирующиеся синононимы"
                uniqueNames.add(alias)

    def createUserIfNotExists(self, name):
        if name in self.data:
            return
        self.data[name] = {
            "name": name,
            "rating": self.START_RATING,
            "wonGames": 0,
            "lostGames": 0,
            "history_ratings": [],
            "payments": []
        }

    def calcElo(self, ra, rb):
        return 1.0 / (1.0 + pow(10.0, (rb - ra) / 400.0))

    def processRatings(self, untilString = None):
        self.data = {}
        self.paymentUsers = {}
        ratings = []
        i = 0
        rows = open("history.txt").read().split('\n')
        for row in rows:
            row = row.strip()
            if untilString and row == untilString:
                break
            if len(row) < 2:
                # print(currentDate)
                # print(currentPrice)
                # print(currentPlayers)
                if currentPrice:
                    for player in currentPlayers:
                        self.data[player]["payments"].append([currentDate, -currentPrice / len(currentPlayers), "Оплата за игру"])
                # print("\n")
                continue

            if row.lower().startswith("дата: "):
                currentDate = datetime.datetime.strptime(row.split(':')[1].strip(), '%d-%m-%Y').date()
                currentPlayers = set()
                currentPrice = None
                continue

            if row.lower().startswith("стоимость: "):
                currentPrice = int(row.split(':')[1].strip())
                continue

            winners, losers = None, None
            if "<" in row:
                losers, winners = row.split(" < ")[:2]
            else:
                winners, losers = row.split(" > ")[:2]

            winners = winners.split(" ")[:2]
            losers = losers.split(" ")[:2]

            winnerA = winners[0]
            winnerB = winners[1]

            loserA = losers[0]
            loserB = losers[1]

            currentPlayers.add(winnerA)
            currentPlayers.add(winnerB)
            currentPlayers.add(loserA)
            currentPlayers.add(loserB)

            self.createUserIfNotExists(winnerA)
            self.createUserIfNotExists(winnerB)
            self.createUserIfNotExists(loserA)
            self.createUserIfNotExists(loserB)

            winnersSum = (self.data[winnerA]["rating"] + self.data[winnerB]["rating"]) / 2.0
            losersSum = (self.data[loserA]["rating"] + self.data[loserB]["rating"]) / 2.0

            winnersEa = self.calcElo(winnersSum, losersSum)
            losersEa = self.calcElo(losersSum, winnersSum)

            self.data[winnerA]["wonGames"] += 1
            self.data[winnerB]["wonGames"] += 1

            self.data[loserA]["lostGames"] += 1
            self.data[loserB]["lostGames"] += 1

            self.data[winnerA]["rating"] += self.COEF_RATING_K * (1 - winnersEa)
            self.data[winnerB]["rating"] += self.COEF_RATING_K * (1 - winnersEa)

            self.data[loserA]["rating"] += self.COEF_RATING_K * (0 - losersEa)
            self.data[loserB]["rating"] += self.COEF_RATING_K * (0 - losersEa)

            self.data[winnerA]["history_ratings"].append(self.data[winnerA]["rating"])
            self.data[winnerB]["history_ratings"].append(self.data[winnerB]["rating"])
            self.data[loserA]["history_ratings"].append(self.data[loserA]["rating"])
            self.data[loserB]["history_ratings"].append(self.data[loserB]["rating"])
            
    def getPlot(self, name):
        ratings = []
        for i, rating in enumerate(self.data[name]["history_ratings"]):
            ratings.append((datetime.date.today() + datetime.timedelta(days=i), rating))
        plt.figure()
        plt.title(name)
        x, scores = zip(*ratings)
        plt.plot(x, scores)
        plt.savefig(name + ".png")
        return name + ".png"

    def getRatings(self):
        sortedMembers = sorted(self.data.values(), key=lambda item: item["rating"], reverse=True)
        result = []
        for member in sortedMembers:
            if member["name"] in self.officialMembers:
                result.append(" ".join([
                    member["name"],
                    str(int(member["rating"])),
                    str(member["wonGames"]) + "/" + str(member["wonGames"] + member["lostGames"]),
                    str(round(member["wonGames"] * 1.0 / (member["wonGames"] + member["lostGames"]), 4))
                ]))

        return "\n".join(result)


    def getElo(self):
        sortedMembers = sorted(self.data.values(), key=lambda item: item["rating"], reverse=True)
        result = []
        for member in sortedMembers:
            if member["name"] in self.officialMembers:
                result.append(" ".join([
                    member["name"],
                    str(int(member["rating"]))
                ]))

        return "\n".join(result)

    def getWinRate(self):
        sortedMembers = sorted(self.data.values(), key=lambda item: (item["wonGames"] * 1.0 / (item["wonGames"] + item["lostGames"])), reverse=True)
        result = []
        for member in sortedMembers:
            if member["name"] in self.officialMembers:
                result.append(" ".join([
                    member["name"],
                    str(member["wonGames"]) + "/" + str(member["wonGames"] + member["lostGames"]),
                    str(round(member["wonGames"] * 1.0 / (member["wonGames"] + member["lostGames"]), 4))
                ]))

        return "\n".join(result)

    def readPayments(self):
        # try:
        rows = open("history_payments.txt").read().split('\n')
        people = {}
        for row in rows:
            paymentDate, user, amount, description = row.split(' ')[:4]
            amount = float(amount)
            self.data[user.strip()]["payments"].append([datetime.datetime.strptime(paymentDate.strip(), '%d-%m-%Y').date(), amount, description])
            # print(paymentDate)
            # print(user)
            # print(amount)
        # except Exception as e:
        #     print(e)

    def all_balance(self):
        result = ""
        for user in self.data.keys():
            user_balance = 0
            for date, amount in self.data[user]["payments"]:
                user_balance += amount
            if user in self.officialMembers:
                result += user + " " + str(round(user_balance)) + "\n"

        return result

    def history_balance(self, user):
        payments = self.data[user]["payments"]
        payments.sort()
        result = ""
        total = 0
        for payment in payments:
            result += str(payment[0]) + ": " + str(round(payment[1])) + " " + payment[2] + "\n"
            total += payment[1]

        result += "Итого баланс: " + str(round(total))
        return result

class Tournament(object):
    def __init__(self, players):
        self.battles = []
        self.players = players
        self.games = {}
        self.missedRound = {}
        self.lastLoosers = []
        self.battleSets = {}
        self.team_sets = {}
        self.teams_last_round = {}
        self.current_round = 0

    def add_battle(self, battle_team):
        self.current_round += 1
        self.battles.append(battle_team)


        self.battleSets[battle_team] = self.battleSets.get(battle_team, 0) + 1
        self.teams_last_round[battle_team[0]] = self.current_round
        self.teams_last_round[battle_team[1]] = self.current_round
        
        for player in self.players[:4]:
            self.games[player] = self.games.get(player, 0) + 1
        
        for player in self.players[4:]:
            self.missedRound[player] = self.current_round
        print("loose: " + battle_team[0][0] + " " + battle_team[0][1])
        print("\n")
        self.lastLoosers = [battle_team[0][0], battle_team[0][1]]


    def get_battle(self):
        def cmp_by_order_playing(p1, p2):
            if self.games.get(p1, 0) != self.games.get(p2, 0):
                return self.games.get(p1, 0) - self.games.get(p2, 0)

            if self.missedRound.get(p1, 100) != self.missedRound.get(p2, 100):
                return self.missedRound.get(p2, 100) - self.missedRound.get(p1, 100)

            if p1 in self.lastLoosers and p2 not in self.lastLoosers:
                return 1

            if p2 in self.lastLoosers and p1 not in self.lastLoosers:
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


class BeachBot(object):
    def __init__(self, bot):
        self.bot = bot
        self.beachBot = Game()
        self.beachBot.processRatings()
        self.beachBot.readPayments()
        # self.beachBot.print_balance()

        self.states = {}
        self.players = []


    def processCreatingGame(self, message):
        if message.from_user.username != "AlexBurkov":
            return
        msg = message.text.lower().strip()

        if msg in [ "создать игру", "создай игру", "c", "с" ]:
            self.states[message.chat.id] = "creating_game_wait_for_balance"
            bot.send_message(message.chat.id, "Введите оплату площадки")
            return

        if message.chat.id not in self.states or not self.states[message.chat.id].startswith("creating_game_"):
            return

        if self.states[message.chat.id] == "creating_game_wait_for_balance":
            payment = int(msg)
            print(payment)
            # TODO: update balance

            self.states[message.chat.id] = "creating_game_wait_for_players"
            markup = types.ReplyKeyboardMarkup(row_width=2)
            markup.add(types.KeyboardButton("Играть"))
            for player in self.beachBot.officialMembers:
                if player not in self.players:
                    markup.add(types.KeyboardButton(player))
            bot.send_message(message.chat.id, "Введите имена игроков в порядке очереди игры", reply_markup=markup)
            return

        if self.states[message.chat.id] == "creating_game_wait_for_players":
            if msg == "играть":
                print("Game is started")
                bot.send_message(message.chat.id, "Список игроков: " + ", ".join(self.players))
                self.tournament = Tournament(self.players)
                battle = self.tournament.get_battle()
                markup = types.ReplyKeyboardMarkup(row_width=2)
                markup.add(battle[0][0] + "+" + battle[0][1] + " vs " + battle[1][0] + "+" + battle[1][1])
                markup.add("Завершить день")
                bot.send_message(message.chat.id, str(battle), reply_markup=markup)
                self.states[message.chat.id] = "creating_game_wait_for_battle"
                return

            if message.text.strip() not in self.beachBot.aliases.keys():
                bot.reply_to(message, "Игрок не найден")
                return

            self.players.append(message.text.strip())
            markup = types.ReplyKeyboardMarkup(row_width=2)
            markup.add(types.KeyboardButton("Играть"))
            for player in self.beachBot.officialMembers:
                if player not in self.players:
                    markup.add(types.KeyboardButton(player))
            bot.send_message(message.chat.id, "Игрок добавлен", reply_markup=markup)

        if self.states[message.chat.id] == "creating_game_wait_for_battle":
            team1, team2 = message.text.split(" vs ")
            player1, player2 = team1.split("+")
            player3, player4 = team2.split("+")
            self.tournament.add_battle(((player1, player2), (player3, player4)))
            markup = types.ReplyKeyboardMarkup(row_width=2)
            markup.add(types.KeyboardButton(player1 + "+" + player2))
            markup.add(types.KeyboardButton(player3 + "+" + player4))
            bot.send_message(message.chat.id, "Кто победил?", reply_markup=markup)
            self.states[message.chat.id] = "creating_game_wait_for_battle_result"
            return
            
        if self.states[message.chat.id] == "creating_game_wait_for_battle_result":
            player1, player2 = message.text.split("+")

            battle = self.tournament.get_battle()
            markup = types.ReplyKeyboardMarkup(row_width=2)
            markup.add(battle[0][0] + "+" + battle[0][1] + " vs " + battle[1][0] + "+" + battle[1][1])
            markup.add("Завершить день")
            bot.send_message(message.chat.id, str(battle), reply_markup=markup)
            self.states[message.chat.id] = "creating_game_wait_for_battle"

            

        # if self.states[message.chat.id] == "creating_game_wait_for_players":
        #     players = msg.split(" ")
        #     self.Tournament = Tournament(players)
        #     return

    def processMessage(self, message):
        try:
            self.processCreatingGame(message)
            
            if message.text.lower().strip() == "бот опрос":
                bot.send_poll(message.chat.id, "Когда играем на следующей неделе?", [ "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Не играю на этой неделе" ], is_anonymous=False, allows_multiple_answers=True, reply_to_message_id=message.id)

            if message.text.lower().strip() in [ "бот баланс" ]:
                bot.send_message(message.chat.id, self.beachBot.history_balance("Антонов"))

            if message.text.lower().strip() in [ "бот", "bot" ]:
                if message.from_user.username != "AlexBurkov":
                    return

                bot.send_message(message.from_user.id, datetime.date.today().strftime("%d-%m-%Y"))
                return

                markup = types.ReplyKeyboardMarkup(row_width=2)
                itembtn1 = types.KeyboardButton('Команда 1')
                itembtn2 = types.KeyboardButton('Команда 2')
                itembtn3 = types.KeyboardButton('Отмена')
                markup.add(itembtn1, itembtn2, itembtn3)
                # bot.send_message(message.from_user.id, "Кто победил?", reply_markup=markup)
                bot.send_message(message.from_user.id, message.from_user.username)
                
                # bot.reply_to(message, message.chat.id)
                # bot.send_message(message.chat.id, message.chat.id)
                # bot.send_message(message.chat.id, message.user.id)
            if message.text.lower() in [ "бот привет", "бот, привет", "бот,привет", "привет бот", "привет, бот", "привет,бот" ]:
                markup = types.ReplyKeyboardRemove(selective=False)
                if not message.from_user.username:
                    bot.reply_to(message, "Здравствуйте, судя по всему у Вас нет никнейма", reply_markup=markup)
                    print(str(message.from_user.id) + " -> anonym")
                else:
                    bot.reply_to(message, "Привет, " + message.from_user.username, reply_markup=markup)
                    print(str(message.from_user.id) + " -> " + message.from_user.username)
            if message.text.lower() == "бот общий баланс":
                bot.reply_to(message, self.beachBot.all_balance())
            if message.text.lower() == "обнови":
                self.beachBot.processRatings()
                bot.reply_to(message, self.beachBot.getRatings())
            elif message.text.lower() in ["эло", "рейтинг эло"]:
                bot.reply_to(message, self.beachBot.getElo())
            elif message.text.lower() in ["рейтинг"]:
                bot.reply_to(message, self.beachBot.getRatings())
            elif message.text.lower() in ["винрейт"]:
                bot.reply_to(message, self.beachBot.getWinRate())
            elif message.text.lower().startswith("график"):
                name = message.text.split(" ")[1]
                bot.send_photo(message.chat.id, photo=open(self.beachBot.getPlot(name), 'rb'), reply_to_message_id=message.id)
        except Exception as e:
            # bot.send_message(message.chat.id, "Что-то пошло не так, если вы хотели вызвать бота, проверьте команду")
            print(e)

if __name__ == "__main__":
    # T = Tournament(["Бурков", "Наташа", "Калужин", "Шавейников", "Антонов"])
    # for z in range(10):
    #     battle = T.get_battle()
    #     T.add_battle(battle)


    ENV = json.load(open(".env"))
    bot = telebot.TeleBot(ENV["telegramToken"])
    myBot = BeachBot(bot)

    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        myBot.processMessage(message)
        
    print("bot is started")
    bot.polling()
