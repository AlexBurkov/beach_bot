class User(object):
    def __init__(self, json_data):
        self.name = json_data["name"]
        self.aliases = json_data.get("aliases", [])
        self.is_official = json_data.get("official", False)
        self.telegramUsername = json_data.get("username", None)
        self.telegramUserId = json_data.get("username", None)

        self.rating = 1400
        self.wonGames = 0
        self.lostGames = 0
        self.history_ratings = []
        self.payments = []

    def add_set_result(self, rating_diff):
        if rating_diff > 0:
            self.wonGames += 1
        else:
            self.lostGames += 1

        self.rating += rating_diff
        self.history_ratings.append(self.rating)
