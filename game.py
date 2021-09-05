import datetime
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from user import User

matplotlib.use('Agg')

class Game(object):
    def __init__(self, users):
        self.START_RATING = 1400
        self.COEF_RATING_K = 16

        self.users = users
        self.checkAliases()

    def checkAliases(self):
        uniqueNames = set()
        for user in self.users.values():
            for alias in user.aliases:
                if alias in uniqueNames:
                    raise "Дублирующиеся синононимы"
                uniqueNames.add(alias)

    def createUserIfNotExists(self, name):
        if name in self.users:
            return
        self.users[name] = User({"name": name})
        
    def calcElo(self, ra, rb):
        return 1.0 / (1.0 + pow(10.0, (rb - ra) / 400.0))

    def process_ratings(self):
        for name in self.users:
            user = self.users[name]
            user.rating = self.START_RATING
            user.wonGames = 0
            user.lostGames = 0
            user.history_ratings = []
            user.payments = []

        self.paymentUsers = {}
        ratings = []
        i = 0
        rows = open("history.txt").read().split('\n')
        for row in rows:
            row = row.strip()
            if len(row) < 2:
                if currentPrice:
                    for player in currentPlayers:
                        self.users[player].payments.append([currentDate, -currentPrice / len(currentPlayers), "Оплата за игру"])
                currentPrice = None
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
            for name in row.split(' '):
                if len(name) > 1:
                    self.createUserIfNotExists(name)
                    currentPlayers.add(name)

            if "<" in row:
                losers, winners = row.split(" < ")[:2]
            else:
                winners, losers = row.split(" > ")[:2]

            winners = winners.split(" ")[:2]
            losers = losers.split(" ")[:2]

            winnerA, winnerB = self.users[winners[0]], self.users[winners[1]]
            loserA, loserB = self.users[losers[0]], self.users[losers[1]]

            winnersSum = (winnerA.rating + winnerB.rating) / 2.0
            losersSum = (loserA.rating + loserB.rating) / 2.0

            winnersEa = self.calcElo(winnersSum, losersSum)
            rating_diff = self.COEF_RATING_K * (1 - winnersEa)

            winnerA.add_set_result(rating_diff)
            winnerB.add_set_result(rating_diff)

            loserA.add_set_result(-rating_diff)
            loserB.add_set_result(-rating_diff)


    def getPlot(self, name):
        ratings = []
        for i, rating in enumerate(self.users[name].history_ratings):
            # ratings.append((datetime.date.today() + datetime.timedelta(days=i), rating))
            ratings.append((i, rating))
        plt.figure()
        plt.title(name)
        x, scores = zip(*ratings)
        plt.plot(x, scores)
        filename = "files/images/" + name + ".png"
        plt.savefig(filename)
        return filename

    def getRatings(self):
        sortedMembers = sorted(self.users.values(), key=lambda item: item.rating, reverse=True)
        result = []
        for member in sortedMembers:
            if member.is_official:
                result.append(" ".join([
                    member.name,
                    str(int(member.rating)),
                    str(member.wonGames) + "/" + str(member.wonGames + member.lostGames),
                    str(round(member.wonGames * 1.0 / (member.wonGames + member.lostGames), 4))
                ]))

        return "\n".join(result)


    def getElo(self):
        sortedMembers = sorted(self.users.values(), key=lambda item: item.rating, reverse=True)
        result = []
        for member in sortedMembers:
            if member.is_official:
                result.append(" ".join([
                    member.name,
                    str(int(member.rating))
                ]))

        return "\n".join(result)

    def getWinRate(self):
        sortedMembers = sorted(self.users.values(), key=lambda item: (item.wonGames * 1.0 / (item.wonGames + item.lostGames)), reverse=True)
        result = []
        for member in sortedMembers:
            if member.is_official:
                result.append(" ".join([
                    member.name,
                    str(member.wonGames) + "/" + str(member.wonGames + member.lostGames),
                    str(round(member.wonGames * 1.0 / (member.wonGames + member.lostGames), 4))
                ]))

        return "\n".join(result)

    def read_payments(self):
        rows = open("history_payments.txt").read().split('\n')
        people = {}
        for row in rows:
            if len(row.strip()) < 2:
                continue
            arr = row.split('\t')
            if len(arr) != 4:
                raise "Payment doesn't have 4 fields"
            paymentDate, user, amount, description = arr[:4]
            amount = float(amount)
            self.users[user.strip()].payments.append([datetime.datetime.strptime(paymentDate.strip(), '%d-%m-%Y').date(), amount, description])

    def all_balance(self):
        result = ""
        for user in self.users.values():
            user_balance = 0
            for payment_data in user.payments:
                paymentDate, amount, description = payment_data
                user_balance += amount
            if user.is_official:
                result += user.name + " " + str(round(user_balance)) + "\n"

        return result

    def history_balance(self, name):
        user = self.users[name]
        payments = user.payments
        payments.sort()
        result = ""
        total = 0
        for payment in payments:
            result += str(payment[0]) + ": " + str(round(payment[1])) + " " + payment[2] + "\n"
            total += payment[1]

        result += "Итого баланс: " + str(round(total))
        return result