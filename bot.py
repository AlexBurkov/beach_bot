#!/usr/bin/python
# -*- coding: utf8 -*-

import telebot
from telebot import types

import json

from user import User
from game import Game
from tournament import Tournament

ENV = {}

class BeachBot(object):
    def __init__(self, bot):
        self.bot = bot
        self.aliases = {}
        self.read_users()

        self.beachBot = Game(self.users)
        self.beachBot.process_ratings()
        self.beachBot.read_payments()

        self.states = {}
        self.players = []
        self.current_battle = None

    def read_users(self):
        self.users = {}
        users = json.load(open("members.json"))
        for name in users:
            data = users[name]
            data["name"] = name
            self.users[name] = User(data)
            self.aliases[name] = self.users[name]
            for alias in data["aliases"]:
                self.aliases[alias] = self.users[name]

    def get_markup(self, buttons):
        markup = types.ReplyKeyboardMarkup(row_width=2)
        for button in buttons:
            markup.add(button)

        return markup

    def show_battles_history(self, message):
        battles_history = self.tournament.get_battles_history()
        result = [ "Протокол игры:" ]
        for battle in battles_history:
            result.append("{0} {1} > {2} {3}".format(battle[0][0], battle[0][1], battle[1][0], battle[1][1]))

        if len(result) > 1:
            bot.send_message(message.chat.id, "\n".join(result))

    def show_day_results(self, message):
        self.process_ratings()
        self.show_battles_history(message)

        battles_history = self.tournament.get_battles_history()
        day_result = {}
        for player in self.players:
            day_result[player] = {
                "name": player,
                "win": 0,
                "lose": 0,
                "old_rating": self.users.rating
            }
        for battle in battles_history:
            day_result[battle[0][0]]["win"] += 1
            day_result[battle[0][1]]["win"] += 1
            day_result[battle[1][0]]["lose"] += 1
            day_result[battle[1][1]]["lose"] += 1

        players = list(day_result.values())
        players = sorted(players, key=lambda player: (player["win"] * 1.0 / (player["win"] + player["lose"])), reverse=True)

        result = []
        for place, player in enumerate(players):
            result.append("{0}. {1} {2}/{3}".format(place + 1, player["name"], player["win"], player["win"] + player["lose"]))

        bot.send_message(message.chat.id, "\n".join(result))

    def process_getting_battle(self, message):
        self.show_battles_history(message)
        battle = self.tournament.get_battle()
        markup = types.ReplyKeyboardMarkup(row_width=2)
        buttons = [
            battle[0][0] + "+" + battle[0][1] + " vs " + battle[1][0] + "+" + battle[1][1],
            "Завершить день"
        ]
        bot.send_message(message.chat.id, "Кто играет?", reply_markup=self.get_markup(buttons))
        self.states[message.chat.id] = "creating_game_wait_for_battle"

    def process_waiting_players(self, message, text):
        buttons = [ "Играть" ]
        for user in self.users.values():
            if user.is_official and user.name not in self.players:
                buttons.append(user.name)
        bot.send_message(message.chat.id, text, reply_markup=self.get_markup(buttons))

    def process_creating_game(self, message):
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
            # TODO: update balance

            self.states[message.chat.id] = "creating_game_wait_for_players"
            self.process_waiting_players(message, "Введите имена игроков в порядке очереди игры")
            return

        if self.states[message.chat.id] == "creating_game_wait_for_players":
            if msg == "играть":
                if len(self.players) < 4:
                    bot.reply_to(message.chat.id, "Должно быть не менее четверых игроков")
                    return
                bot.send_message(message.chat.id, "Список игроков: " + ", ".join(self.players))
                self.tournament = Tournament(self.players)
                self.process_getting_battle(message)
                return

            if message.text.strip() not in self.aliases:
                bot.reply_to(message, "Игрок не найден")
                return

            self.players.append(message.text.strip())
            self.process_waiting_players(message, self.aliases[message.text.strip()].name + " добавлен")
            return

        if self.states[message.chat.id] == "creating_game_wait_for_battle":
            if message.text.lower().strip() == "завершить день":
                self.show_day_results(message)
                self.states[message.chat.id] = "creating_game_wait_for_saving"
                bot.send_message(message.chat.id, "Сохранить игру?", reply_markup=self.get_markup(["Да", "Нет, сохраню вручную"]))
                return

            team1, team2 = message.text.split(" vs ")
            player1, player2 = team1.split("+")
            player3, player4 = team2.split("+")
            self.current_players = [ player1, player2, player3, player4 ]
            markup = types.ReplyKeyboardMarkup(row_width=2)
            markup.add(types.KeyboardButton(player1 + "+" + player2))
            markup.add(types.KeyboardButton(player3 + "+" + player4))
            bot.send_message(message.chat.id, "Кто победил?", reply_markup=markup)
            self.states[message.chat.id] = "creating_game_wait_for_battle_result"
            return

        if self.states[message.chat.id] == "creating_game_wait_for_battle_result":
            winners = message.text.split("+")
            losers = []
            for player in self.current_players:
                if player not in winners:
                    losers.append(player)

            self.tournament.add_battle(winners, losers)
            self.process_getting_battle(message)
            return

        # if self.states[message.chat.id] == "creating_game_wait_for_saving":


    def processMessage(self, message):
        try:
            self.process_creating_game(message)

            if message.text.lower().strip() == "бот опрос":
                bot.send_poll(message.chat.id, "Когда играем на следующей неделе?", [ "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Не играю на этой неделе" ], is_anonymous=False, allows_multiple_answers=True, reply_to_message_id=message.id)

            if message.text.lower().strip() in [ "бот платежи" ]:
                bot.send_message(message.chat.id, self.beachBot.history_balance("Антонов"))

            if message.text.lower() in [ "бот привет", "бот, привет", "бот,привет", "привет бот", "привет, бот", "привет,бот" ]:
                markup = types.ReplyKeyboardRemove(selective=False)
                if not message.from_user.username:
                    bot.reply_to(message, "Здравствуйте, судя по всему у Вас нет никнейма", reply_markup=markup)
                    print(str(message.from_user.id) + " -> anonym")
                else:
                    bot.reply_to(message, "Привет, " + message.from_user.username, reply_markup=markup)
                    print(str(message.from_user.id) + " -> " + message.from_user.username)
            if message.text.lower() in ["бот общий баланс", "боб", "bob"]:
                bot.reply_to(message, self.beachBot.all_balance())
            if message.text.lower() == "обнови":
                self.beachBot.process_ratings()
                bot.reply_to(message, self.beachBot.getRatings())
            elif message.text.lower() in ["эло", "рейтинг эло"]:
                bot.reply_to(message, self.beachBot.getElo())
            elif message.text.lower() in ["рейтинг"]:
                bot.reply_to(message, self.beachBot.getRatings())
            elif message.text.lower() in ["винрейт"]:
                bot.reply_to(message, self.beachBot.getWinRate())
            elif message.text.lower().startswith("график"):
                name = message.text.split(" ")[1]
                bot.send_photo(message.chat.id, photo=open(self.beachBot.getPlot(name.title()), 'rb'), reply_to_message_id=message.id)
        except Exception as e:
            # bot.send_message(message.chat.id, "Что-то пошло не так, если вы хотели вызвать бота, проверьте команду")
            print(e)

if __name__ == "__main__":
    ENV = json.load(open(".env"))
    bot = telebot.TeleBot(ENV["telegramToken"])
    myBot = BeachBot(bot)

    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        myBot.processMessage(message)
        
    print("bot is started")
    while True:
        try:
            bot.polling()
        except Exception as e:
            print(e)
