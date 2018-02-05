from lxml import html
import requests
import sys
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime
import urllib
import time
import json
from utils import debug, info, warning, error, unescape
import re
# import utils
from models import Match, Goal, League, Media

class FootyRoomGrabber():

	def start(self):
		leagues = self.get_leagues()

		for league in leagues:
			debug("Processing league: " + league[0].name, False)
			urls = self.get_page_urls(league[0], league[1])

			print(" => Found {} url pages. Processing urls...".format(len(urls)))

			counter = 1
			for url in urls:
				debug("Processing page {}: ".format(counter), False)

				# Returns tuple (match_url, match_img)
				match_urls = self.process_page(url)
				print(" Found {}".format(len(match_urls)))

				for match in match_urls:
					debug("Processing match {} ".format(match[0]), False)
					media_urls = self.process_match(match[0], match[1])
					print (" Found {}".format(len(media_urls)))
					print (media_urls)
				counter += 1

	def get_leagues(self):
		url = "http://footyroom.com/"

		r = requests.get(url)
		soup = BeautifulSoup(r.content, "lxml")

		if r.status_code != 200:
			error("Failed to process url!")
			return False

		# Get main content hodlder
		main_section = soup.find("section", {"class": "all-leagues-content"})

		debug("main_section: {}".format(main_section != None))

		# Get children
		league_group = main_section.find_all("div", recursive=False)
		other_league_groups = main_section.find_all("section", recursive=False)

		# debug("main_children: {}".format(match_children != None))
		leagues_to_rtn = []

		for lg_group in league_group:
			# Get ul inside div
			lst = lg_group.find("ul")

			# Get country from first li of ul
			country_li = lst.find("li", {"class": "all-leagues-header"})
			country = country_li.text

			leagues = lst.find_all("li", { "class": "" })

			for league_li in leagues:
				league = League(country, league_li.text)

				url = league_li.find("a")["href"]

				# self.process_league(league, url)
				leagues_to_rtn.append((league, url))
			# Find leagues

		return leagues_to_rtn

	def get_page_urls(self, league, url):
		r = requests.get(url)
		soup = BeautifulSoup(r.content, "lxml")

		# Get stageTree value
		# This is basically the league identifier used to retrieved matches
		# associated with said league
		stageTree = self.get_stage_tree(soup)

		urls = []
		for i in range(1, 1000):
			urls.append(
				"http://footyroom.com/posts-pagelet?page={}&stageTree={}".format(i, stageTree))

		return urls

	def process_page(self, url):
		r = requests.get(url)
		soup = BeautifulSoup(r.content, "lxml")

		main_div = soup.find("div", {"class": "posts-page clearfix "})

		children_div = main_div.find_all(
			"div", {"class": "card col-xs-12 col-ms-6 col-md-4 "})

		matches = []
		for child in children_div:
			div = child.find("div", {"class": "card-image"})
			match_url = div.find("a")["href"]
			match_img = div.find("img")["src"]

			matches.append((match_url, match_img))

		return matches

	def process_match(self, url, img_url):
		r = requests.get(url)
		soup = BeautifulSoup(r.content, "lxml")

		script_tags = soup.find_all("script")

		urls = []
		for tag in script_tags:
			if "DataStore.media " in tag.text:
				urls = urls + self.extract_media_urls(tag.text)

		return urls

	def extract_media_urls(self, text):
		media_urls = []

		#\{(.*?)\}
		patt = re.compile('\{(.*?)\}')
		patt2 = re.compile('<source src=\"(.*?)\"')
		# print(text.encode('utf-8').decode('unicode_escape'))

		for m in re.finditer(patt, text):
			media = json.loads(m.group(0))

			if "attachment" in media and "iframe" in media["attachment"]:
				# Extract URL from attachment value
				# Split by src=" [it's known the element is an iframe, so we need to get the src prop]
				tks = media["attachment"].split('src=')

				# Might be quotation mark or '
				splitter = tks[1][0]

				# Get the second token, from the start+1 to the first occurence of "
				# STOP AT = tks[1][1:].find(tks[1][0])
				media_url = tks[1][1:tks[1][1:].find(tks[1][0])]

				if media_url[0:2] == "//":
					media_url = media_url[2:]

				media_urls.append(media_url)
				break
			elif "attachment" in media and "video" in media["attachment"]:
				# <video controls preload = "auto" width = "100%" height = "100%" >
				#  <source src = "http://twii.edgeboss.net/download/twii/manutd/video_mufc_20180115_stoke_goals.ogg" type = "video/ogg" > < / video >

				patt = re.compile('\"(.*?)\"')
				defined = False

				for m in re.finditer(patt, media["attachment"]):
					token = m.group(1)

					if 'http' in token.lower():
						defined = True
						media_urls.append(token)

				if defined == False:
					error("COULD NOT FIND VIDEO ATTACHMENT")
				break
			else:
				media_urls.append(re.sub(r'\\(.)', r'\1', media["source"]))
				break

		# for m in re.finditer(patt2, re.sub(r'\\(.)', r'\1', text)):
		# 	url = m.group(1)

		# 	if "http" in url:
		# 		media_urls.append(url)

		return media_urls

	def get_stage_tree(self, soup):
		script_tags = soup.find_all("script")

		stageTree = None
		show = False
		for tag in script_tags:
			if stageTree != None:
				break

			patt = re.compile('("([^"]|"")*")')

			for m in re.finditer(patt, tag.text):
				# print(m.group(0), '*', m.group(1))

				if show:
					stageTree = m.group(1)
					break

				if "stagetree" in m.group(1).lower():
					show = True

		return stageTree.replace('"', '')
