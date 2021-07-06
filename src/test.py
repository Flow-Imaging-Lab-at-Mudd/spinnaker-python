import sys
import os

from multiprocess_logging import install_mp_handler
from multiprocessing import Pool
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../', 'lib/'))
import logger
import glob
import os

if not __name__ == "__main__":
	import traceback

	filename = traceback.format_stack()[0]
	log = logger.getLogger(filename.split('"')[1])


def square(num):
	"""
    function to print square of given num
    """
	log.debug("debug")
	log.info("info")
	log.warning("warning")
	log.error("error")
	log.exception("exception")
	log.fatal("fatal")
	log.log(5, "log")
	log.VLOG(2, "Square: {}".format(num * num))
	return True


def main():
	result = True
	log.VLOG(1, "Logs starting")

	install_mp_handler(log)

	log.VLOG(1, "Handler installed")

	p = Pool(3)
	results = p.map(square, range(3))
	result &= min(results)

	return result


def interpret_file():
	lines = sorted(glob.glob(os.path.join('MultiCamAcqTest', '*')))
	lines = [line.split("-") for line in lines]
	lines = [[int(entry[5:-4]) if '.jpg' in entry else int(entry) for entry in line[1:]] for line in lines]
	frames = max(lines, key=lambda x: x[1])[1] + 1
	prev_time = 0
	for i in range(frames):
		frame_nums = [lines[i + (j * frames)][1] for j in range(len(lines) // frames)]
		if len(set(frame_nums)) > 1:
			print("Uh oh, our frames are: {}".format(frame_nums))
		times = [lines[i + (j * frames)][2] for j in range(len(lines) // frames)]
		avgTime = sum(times) / len(times)
		next_time = avgTime
		fps = 1e9 / (next_time - prev_time)
		distances = [time - min(times) for time in times]
		print("----------- FRAME {0} -----------".format(i))
		print("average capture time (ns): {0}".format(avgTime))
		print("                distances: {0}".format(distances))
		print("                      fps: {0}".format(fps))
		prev_time = next_time



if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-c', '--config_file', help='relative path to config file', type=str)
	parser.add_argument('-v', '--verbosity', help='verbosity level for file prints (1 through 4 or DEBUG, INFO, etc.)',
	                    type=str, default="1")
	parser.add_argument('-l', '--logType', help='style of log print messages (cpp (default), pretty)', type=str,
	                    default="cpp")
	args = parser.parse_args()
	config_path = args.config_file
	log = logger.getLogger(__file__, args.verbosity, args.logType)

	interpret_file()

	# if main():
	# 	sys.exit(0)
	# else:
	# 	sys.exit(1)
