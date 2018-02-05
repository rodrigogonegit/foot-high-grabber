from configobj import ConfigObj

config = ConfigObj("set.ini")

val = -1

try:
	val = int(config["first_match_url"])
except KeyError:
	val = 0

val += 1

print(val)
config["first_match_url"] = str(val)

config.write()
