from colorama import init, Fore, Back, Style
import re
from random import uniform
import time

# Print Aux


def info(msg, new_line=True):
	print(Fore.GREEN + "[INFO]" + Fore.RESET + msg,
	      end=("\n" if new_line else ""), flush=(not new_line))
	# pass


def warning(msg, new_line=True):
	print(Fore.YELLOW + "[WARN]" + Fore.RESET + msg,
	      end=("\n" if new_line else ""), flush=(not new_line))


def error(msg, new_line=True):
	print(Fore.RED + "[ERROR]" + Fore.RESET + msg,
	      end=("\n" if new_line else ""), flush=(not new_line))


def debug(msg, new_line=True):
	print(Fore.BLUE + "[DEBUG]" + Fore.RESET + msg,
	      end=("\n" if new_line else ""), flush=(not new_line))


def log(msg, new_line):
	print(msg, end=("\n" if new_line else ""), flush=(not new_line))


def unescape(text):
	regex = re.compile(b'\\\\(\\\\|[0-7]{1,3}|x.[0-9a-f]?|[\'"abfnrt]|.|$)')

	def replace(m):
		b = m.group(1)
		if len(b) == 0:
			raise ValueError("Invalid character escape: '\\'.")
		i = b[0]
		if i == 120:
			v = int(b[1:], 16)
		elif 48 <= i <= 55:
			v = int(b, 8)
		elif i == 34:
			return b'"'
		elif i == 39:
			return b"'"
		elif i == 92:
			return b'\\'
		elif i == 97:
			return b'\a'
		elif i == 98:
			return b'\b'
		elif i == 102:
			return b'\f'
		elif i == 110:
			return b'\n'
		elif i == 114:
			return b'\r'
		elif i == 116:
			return b'\t'
		else:
				s = b.decode('ascii')
				raise UnicodeDecodeError(
					 'stringescape', text, m.start(), m.end(), "Invalid escape: %r" % s
				)
		return bytes((v, ))
	result = regex.sub(replace, text)

def wait_random():
	v = uniform(200.0, 600.0)

	# Sleep 200ms to avoid overwhelming the server
	time.sleep(v / 1000.0)
