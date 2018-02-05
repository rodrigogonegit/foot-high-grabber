from json import JSONEncoder

# Represents a match
class Match(JSONEncoder):
	def __init__(self, team1, team2, match_date, score, country, competition, url, is_live, penalty_score="", competition_phase=""):
		self.team1 = team1
		self.team2 = team2
		self.match_date = match_date.strftime('%Y-%m-%d %H:%M:%S')
		self.score = score
		self.penalty_score = penalty_score
		self.country = country
		self.goals = []
		self.competition = competition
		self.competition_phase = competition_phase
		self.url = url
		self.is_live = is_live

	def __str__(self):
		return str(self.__dict__)

	def __eq__(self, other):
		if other == None:
			return False

		return self.__dict__ == other.__dict__

	def serialize(self):
		return {
                    'team1': self.team1,
                    'team2': self.team2,
                    'match_date': self.match_date,
                    'score': self.score,
                    'competition': self.competition,
                    'country': self.country,
                    'goals': self.goals,
                    'url': self.url,
                    'is_live': self.is_live,
                    'penalty_score': self.penalty_score,
                    'competition_phase': self.competition_phase,
                }


class Goal(JSONEncoder):
	def __init__(self, author, minute, url):
		self.author = author
		self.minute = minute
		self.url = url

class League(JSONEncoder):
	def __init__(self, name, country):
		self.name = name
		self.country = country


class Media(JSONEncoder):
	def __init__(self, url, title):
		self.url = url
		self.title = title
