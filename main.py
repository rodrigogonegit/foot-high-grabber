import argparse
import configparser
from utils import debug, info, warning, error
from ngolos_grabber import NGolosGrabber
from footyroom_grabber import FootyRoomGrabber
import os

config = configparser.RawConfigParser()

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help='enables verbosity', action='count')
parser.add_argument('-l', '--stop', help='stops when the first match processed in the last execution is reached', action='store_true')
args = parser.parse_args()


# ngolos.process_match("https://www.ngolos.com/videos/2018-01-04-tottenham-westham")
# ngolos.process_page("https://www.ngolos.com/videos/list-560")
# ngolos.get_goals(
# 	"https://www.ngolos.com/videos/2018-01-19-vsetubal-sporting")
# footy.start()
# footy.process_match("http://footyroom.com/matches/79940708/crystal-palace-vs-manchester-city/review", "")

if __name__ == "__main__":
    # DEBUG ONLY!!!!!!!!
    os.chdir("/home/rodrigo/projs/foot-high/grabber/")
    debug("CWD: " + os.getcwd())

    try:
        if args.stop:
            info("Execution will stop once the previous first match is reached")

        ngolos = NGolosGrabber(args.stop)
        # footy = FootyRoomGrabber()
        # https: // www.ngolos.com / videos / 2018 - 01 - 06 - pontarlier - montpellier
        ngolos.grab_highlights()
        # ngolos.process_page("https://www.ngolos.com/videos/list-440")

    except KeyboardInterrupt as e:
        ngolos.handle_exit()
        info("User interruption detected. Exitting.")

    except SystemExit:
        ngolos.handle_exit()
        info("System quitted. Exitting.")

    # except Exception as e:
    # 	info("Unhandled exception!")
    # error(str(e))
