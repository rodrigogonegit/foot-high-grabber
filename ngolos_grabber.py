from lxml import html
import requests
import sys
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime
import urllib
import json
from utils import debug, info, warning, error, wait_random
# import utils
from models import Match, Goal
from configobj import ConfigObj
import json
import time

class NGolosGrabber:

	 # READ_FIRST_MATCH = None
	 # READ_LAST_MATCH = None
	 # READ_LAST_PAGE = None
	 # READ_FIRST_PAGE = None

	 # NEW_FIRST_MATCH = None
	 # NEW_LAST_MATCH = None
	 # NEW_LAST_PAGE = None
	 # NEW_FIRST_PAGE = None

	 # CHANGE_PAGE_OFFSET = False
	 # PAGE_OFFSET = -1

	 # SKIP_MATCH = False

	 # # Used to push matches to DB when an interrupt is detected mid page processing
	 # CURRENT_MATCHES_BEING_PROCESSED = []

	def __init__(self, stop_at_first_match=False):
		self.READ_FIRST_MATCH = None
		self.READ_LAST_MATCH = None
		self.READ_LAST_PAGE = None

		self.NEW_FIRST_MATCH = None
		self.NEW_LAST_MATCH = None
		self.NEW_LAST_PAGE = None

		self.SKIP_MATCH = False

		# Used to push matches to DB when an interrupt is detected mid page processing
		self.CURRENT_MATCHES_BEING_PROCESSED = []

		self.SKIPPED_MATCHES_COUNTER = 0

		self.CHANGE_TO_LAST_PAGE = False

		self.STOP_ON_FIRST_MATCH = stop_at_first_match

		self.COUNTRY_TO_COMPETITION = {
		"spain": "La Liga",
		"portugal": "Primeira Liga",
		"germany": "Bundesliga",
		"england": "Premier League",
		"italy": "Serie A",
		"russia": "Russian Premier League",
		"france": "Ligue 1",
		"albania": "Kategorie Superiore",
		"turkey": "Turkcell Superlig",
		"netherlands": "Eredivisie",
		"belgium": "Belgian Pro League"
		}


		self.config = ConfigObj("settings.ini", raise_errors=True)
		self.read_settings()

		self.push_backup()

	def push_backup(self):
		info("Pushing backups to database...")

		if not os.path.exists('backup_matches'):
			info("No backup matches. Nothing to be done.")
			return

		  # [name for name in os.listdir(
		  # 	'backup_matches') if os.path.isfile(name)])

		for file in os.listdir("backup_matches"):
			try:
				content = None
				file_name = "backup_matches/" + file
				info("Pushing backup: " + file_name)

				with open(file_name, "r") as f:
					content = f.read()

					if content.strip() == "":
						return

					content = json.loads(content)

				if self.push_matches(content, False):
					os.remove("backup_matches/" + file)

			except Exception as e:
					error("Error handling backup file.")
					error (str(e))

	def backup_matches(self, matches):
		if not os.path.exists('backup_matches'):
			os.makedirs('backup_matches')

		if matches == None or matches == []:
			debug("backup_matches: null or empty matches list")
			return

		# file_list = [name for name in os.listdir('backup_matches') if os.path.isfile("backup_matches/" + name)]
		  # file_list.sort()

		  # file_number = "0"
		  # if len(file_list) != 0:
		  # 	file_number = re.search("[0-9]*", file_list[-1])
		  # 	file_number = file_number.group(0)

		  # file_name = "backup_matches/{}.bak".format(int(file_number) + 1)

		file_name = time.strftime("backup_matches/%d-%m-%Y__%H-%M.bak")

		try:
			with open(file_name, "w+") as file:
					file.write(json.dumps(matches))

		except Exception as e:
			error("Error creating backup file: " + file_name)
			error(str(e))

	def push_matches(self, matches, backup_on_fail=True):
		if matches == None or len(matches) == 0:
			warning("Empty matches list. Nothing to push!")
			return

		info("Pushing {} matches to database...".format(len(matches)))

		to_be_backedup_matches = None

		try:
			if matches:
					r = requests.post("http://127.0.0.1:5000/match",
											json=matches)

			# status == 200, some matches failed (probably due to being duplicates)
			if r.status_code == 200:
					duplicate_matches = r.json()
					urls = [d["url"] for d in duplicate_matches]

					to_be_backedup_matches = [d for d in matches if not d["url"] in urls]

					warning("{} matches could not be pushed because they were duplicates".format(len(duplicate_matches)))

			# No duplicates found
			elif r.status_code == 201:
					pass

			# Something went wrong
			else:
					error("Database server responded with {}. Saving processed matches for later commit.".format(
					r.status_code))

					if backup_on_fail:
						self.backup_matches(to_be_backedup_matches)

					return False

		except Exception as e:
			if backup_on_fail:
					error("Error occured committing data to database! Saving processed matches for later commit.")
					self.backup_matches(matches)

			else:
					 error("Error occured pushing data to database! Backup file will not be deleted and will be reprocessed!")
					 debug(str(e))

			return False

		return True

	def handle_exit(self):
		warning("Handling safe exit...")
		self.push_matches([d.serialize() for d in self.CURRENT_MATCHES_BEING_PROCESSED])
		self.write_last_game()

	# Entry point
	def grab_highlights(self):
		# Process pages

		index = 0
		while True:
			# Page offset defines a new start, when for instance an interval of matches
			# # has been processed
			# if self.CHANGE_PAGE_OFFSET and self.PAGE_OFFSET > -1:

			# 	# Equal first and last page means it stopped on the same page
			# 	# So we need to go to the next one since it will finish processing
			# 	# that same page
			# 	if self.READ_LAST_PAGE == self.READ_FIRST_PAGE:
			# 		i = self.PAGE_OFFSET + 40
			# 	else:
			# 		i = self.PAGE_OFFSET

			# 	self.CHANGE_PAGE_OFFSET = False


			# if self.CHANGE_TO_LAST_PAGE:

			# 	if index < self.READ_LAST_PAGE:
			# 		index = self.READ_LAST_PAGE

			# self.NEW_LAST_PAGE = index

			new = self.process_page("https://www.ngolos.com/videos/list-{}".format(index))

			if not new == [] and not new == None:
					# Save matches to db
					self.push_matches([d.serialize() for d in new])

			if self.STOP_ON_FIRST_MATCH:
					break

			# if self.CHANGE_TO_LAST_PAGE and self.SKIP_MATCH:
			# This only happens when the LAST PAGE doesn't contain the last processed match
			# It shouldn't happen
			# Assume it was an error, and reprocess page
			# this time, CHANGE_TO_LAST_PAGE and SKIP_MATCH will be false
			# self.CHANGE_TO_LAST_PAGE = False
			# self.SKIP_MATCH = False
			# continue

			# self.CHANGE_TO_LAST_PAGE = False
			index += 40

	# Processes a url
	def process_page(self, url):
		info("Processing {}...".format(url))

		  # Empty CURRENT
		self.CURRENT_MATCHES_BEING_PROCESSED = []

		matches = []

		r = requests.get(url)
		soup = BeautifulSoup(r.content, "lxml")

		if r.status_code != 200:
			error("Failed to process url!")
			return False

		# Get main content hodlder
		main_div = soup.find("section", {"id": "mainContent"})

		# Get children
		match_children = main_div.find_all("div", {"class": "match"}, recursive=False)

		self.MATCH_PROCESS_COUNTER = 0

		for match in match_children:
			try:
					curr_match = self.process_match(match)
			except Exception as e:
					print("Failed on URL obj: " + str(match))
					print(e)

			self.MATCH_PROCESS_COUNTER += 1

			# if self.CHANGE_TO_LAST_PAGE:
			# 	break

			# Skip match
			if curr_match == None:
					if self.SKIP_MATCH and self.STOP_ON_FIRST_MATCH:
						break

					continue

			curr_match.goals += self.get_goals(curr_match.url)

			info("[{}/40]{} {} {} at {} [{}] => {} videos found".format(
				self.MATCH_PROCESS_COUNTER,
				curr_match.team1,
				curr_match.score,
				curr_match.team2,
				curr_match.match_date,
				curr_match.country,
				len(curr_match.goals)))
			matches.append(curr_match)

			self.CURRENT_MATCHES_BEING_PROCESSED = matches

			# Update last match
			self.NEW_LAST_MATCH = curr_match.url

		return matches

	def process_match(self, match):
		# Get match URL
		url = match.find("a")["href"]
		url = "https://www.ngolos.com" + url

		# if (url != "https://www.ngolos.com/videos/2018-01-28-indianapacers-orlandomagic"):
		# 	return

		if self.READ_FIRST_MATCH == url:
			info("Hit first match of last session. Halting processing! [{}]".format(self.READ_FIRST_MATCH))
			self.NEW_FIRST_MATCH = self.READ_FIRST_MATCH
			self.SKIP_MATCH = True

			# Stop right now if flag is set
			if self.STOP_ON_FIRST_MATCH:
					return

			# self.CHANGE_TO_LAST_PAGE = True

		# STOP SKIPPING once last processed match is reached and CONTINUE processsing
		if self.READ_LAST_MATCH == url:

			# Sanity check
			if not self.SKIP_MATCH:
					error("FOUND LAST MATCH BEFORE FINDING THE FIRST ONE. SOMETHiNG'S WRONG. CHECK SETTINGS.INI")
					raise SystemExit()

			info("Hit LAST match of last session. Resuming processing! [{}]".format(self.READ_LAST_MATCH))
			info("Skipped {} matches.".format(self.SKIPPED_MATCHES_COUNTER))

			self.SKIPPED_MATCHES_COUNTER = 0
			self.SKIP_MATCH = False
			# self.CHANGE_TO_LAST_PAGE = False
			return

		if self.SKIP_MATCH:
			self.SKIPPED_MATCHES_COUNTER += 1
			return

		# Wait only if match is not to be skipped
		# debug("Random delay")

		# Random wait to avoid overloading the server
		wait_random()

		# Get img src, split it by / and get the last occurence
		country = match.find("img")["src"].split("/")[-1].split(".")[0]

		# Split datetime and teams
		tokens = match.text.split(" - ", 1)

		country = country.strip()

		if country.lower() == "basketball":
			return

		# Check wether it's a live match
		is_live = country.lower() == "live"

		# Holds both teams
		teams = []

		# Penalty score to be set
		penalty_score = ""

		# Get teams
		if is_live or "Abandoned" in tokens[1]:
			# split by vs
			teams = tokens[1].split(" vs ")
			team1 = teams[0]
			team2 = teams[1]

		else:
			# Split by, for example, 2-2
			teams = re.split("\d+-\d+", tokens[1])

			if len(teams) == 3:
					team1 = teams[0]
					team2 = teams[2].replace("(", "")
					penalty_score = teams[1]

			elif len(teams) == 2:
				team1 = teams[0]
				team2 = teams[1]

			else:
				error("[INTERNAL ERROR] Teams token length not expected.")

		# Check for penalty score
		# penaly = re.search("([0-9]*-[0-9]*)", team1):
		re_penalty_team1 = re.search("(\d+)", team1)

		if re_penalty_team1 != None:
			re_penalty_team2 = re.search("(\d+)", team2)

			if re_penalty_team2 == None:
					error("Error processing url {}. Found what seems to be penalty score for team1 but not for team2. Ignoring.".format(url))
					return

			# Remove penalty score from team
			team1 = team1.replace("({})".format(re_penalty_team1.group(0)), "")
			team2 = team2.replace("({})".format(re_penalty_team2.group(0)), "")

			penalty_score = "{}-{}".format(re_penalty_team1.group(0), re_penalty_team2.group(0))

	#   else:
	#       # Check if penalty score wasn't defined in the second team with format (NUMBER-NUMBER)
	#       re_penalty_teams = re.search("(\d+-\d+)", team2)

	#       if re_penalty_teams != None:
	#           penalty_score = re_penalty_teams.group(0)

	#           team2 = team2.replace("({})".format(re_penalty_score, ""))


		# Check if league or sport os specified
		# If it is, it should be present on team2 string enclosed between ()
		competition = team2.rsplit("(", 1)
		competition_phase = ""

		if len(competition) != 1:
			team2 = competition[0].strip()
			competition = competition[1][0:competition[1].index(")")]

			# Check if competition has phase
			tks = competition.split("-")

			if len(tks) > 1:
					competition_phase = tks[1]
					competition = competition.replace("- {}".format(competition_phase), "")

		else:
			if country.lower() in self.COUNTRY_TO_COMPETITION:
					competition = self.COUNTRY_TO_COMPETITION[country.lower()]
			else:
					competition = "LEAGUE_TBD"

		result = re.search("\d+-\d+", tokens[1])

		if result == None:
			result = "vs"
		else:
			result = result.group(0)

		# Get datetime
		dtime = datetime.strptime(tokens[0].strip(), "%Y.%m.%d (%Hh%M)")

		# info("{} {} {} at {} [{}]".format(team1, result, team2, dtime, country))

		curr_match = Match(team1.strip(),
				team2.strip(),
				dtime,
				result.strip(),
				country.strip(),
				competition,
				url,
				is_live,
				penalty_score,
				competition_phase.strip())

		# print (json.dumps(curr_match.serialize()))
		if self.NEW_FIRST_MATCH == None:
			self.NEW_FIRST_MATCH = url
			info("SAVED FIRST MATCH")

		return curr_match

	def get_goals(self, url):
		# Process url
		r = requests.get(url)
		soup = BeautifulSoup(r.content, "lxml")

		# Find main section
		sec = soup.find("section", id="mainContent")

		# Find <script type=text/javascript>
		# script_tags = sec.find_all("script")
		# script = [d for d in script_tags if ("unquote") in d.text]

		# print (script)
		# Decode URL encoded information
		un = re.search("\'(.+)\'", sec.contents[8].text).group(0)

		un = urllib.parse.unquote(un)

		# print (un)
		soup = BeautifulSoup(un, "lxml")

		div = soup.find("div", id="tab-1")

		strong = div.find("strong")

		strong_text = strong.text.strip()

		# ccc = strong.children
		# videos = strong.find_all("div", {"class": "embed-container"})

		# index = 0
		# goal_objs = []

		# for child in ccc:
		# 	if child != None and child.name != "div" and child.strip() != "":
		# 		pass

		videos = []

		# Full highlights
		if strong_text == "No Goals Yet":
			pass
		else:
			v1 = strong.find_all("iframe")
			v2 = strong.find_all("source")

			if v1 != None:
					for v in v1:
						# print (v["src"])
						videos.append(v["src"].replace("//www", "www"))

			if v2 != None:
					for v in v2:
						# print (v["src"])
						videos.append(v["src"].replace("//www", "www"))

			# # embeds = strong.find_all("div", {"class": "embed-container"})
			# # print (embeds)
			# lst = strong.contents

			# # tup = [tuple(lst[i:i+1]) for i, v in enumerate(lst)]

			# # for i, v in enumerate(lst[0:-2]):
			# # 	print (str(lst[i]) +  " - "  + str(lst[i+1]))

			# # print (tup)
			# # is_goal_child = False
			# # for c in strong.contents:
			# # 	if is_goal_child:

		return videos

		# print (div)
		# sys.exit(0)
		# for e in embeds:
		# 	# match.goals.append(e.contents[0]["src"])
		# 	pass

		# TODO: READ AUTHOR AND MINUTE AND ADD DATA TO LIST OF GOALS

	def write_last_game(self):
		# If this happens, it means no new data was found in target website
		# It hasn't had the chance to set the FIRST_CHANCE because the
		# the first match was the last
		# if self.NEW_FIRST_MATCH == None \
		# 	or self.NEW_LAST_MATCH == None \
		# 	or self.NEW_FIRST_PAGE == None \
		# 	or self.NEW_LAST_PAGE == None:
		# 	debug("Some or all values were null! Not saving to settings.ini!")
		# 	return

		if self.NEW_FIRST_MATCH == None:
			self.NEW_FIRST_MATCH = self.READ_FIRST_MATCH

		if self.NEW_LAST_MATCH == None:
			self.NEW_LAST_MATCH = self.READ_LAST_MATCH

		if self.NEW_LAST_PAGE == None:
			self.NEW_LAST_PAGE = self.READ_LAST_PAGE

		try:
			self.config["main"] = {}
			self.config["main"]["first_match_url"] = self.NEW_FIRST_MATCH
			self.config["main"]["last_match_url"] = self.NEW_LAST_MATCH
			self.config["main"]["last_page_url"] = self.NEW_LAST_PAGE

			self.config.write()

			debug("First and last matches saved:\nFirst match:{}\nLast match: {}".format(
				self.NEW_FIRST_MATCH,
				self.NEW_LAST_MATCH))

		except Exception as e:
			print(e)

	def read_settings(self):
		try:
			self.READ_FIRST_MATCH = self.config["main"]["first_match_url"]
			self.READ_LAST_MATCH = self.config["main"]["last_match_url"]
			self.READ_LAST_PAGE = int(self.config["main"]["last_page_url"])

			debug("First and last matches read from settings.ini:\n\tFirst match:{}\n\tLast match: {}".format(
				self.READ_FIRST_MATCH,
				self.READ_LAST_MATCH))

		except Exception as e:
			warning(str(e))
