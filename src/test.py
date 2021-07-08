import sys
import os

from multiprocess_logging import install_mp_handler
from multiprocessing import Pool
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../', 'lib/'))
import logger
import glob
import os
import numpy as np

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


def interpret_file(sync):
	if sync:
		all_times = np.loadtxt('MCAT-timestamps.csv', delimiter=',')
		all_times = all_times.tolist()
		frames = len(all_times)
	else:
		lines = sorted(glob.glob(os.path.join('MultiCamAcqTest', '*')))
		lines = [line.split("-") for line in lines]
		lines = [[float(entry[:-4]) if '.jpg' in entry else int(entry) for entry in line[1:]] for line in lines]
		frames = max(lines, key=lambda x: x[1])[1] + 1
		all_times = []
		for i in range(frames):
			frame_nums = [lines[i + (j * frames)][1] for j in range(len(lines) // frames)]
			if len(set(frame_nums)) > 1 or sum(frame_nums) / len(frame_nums) != i:
				print("Uh oh, our frames are: {}".format(frame_nums))
			all_times += [[lines[i + (j * frames)][2] for j in range(len(lines) // frames)]]
	prev_time = 0
	fps_list = []
	distance_list = []
	for i in range(frames):
		times = all_times[i]
		avgTime = sum(times) / len(times)
		next_time = avgTime
		fps = 0 if next_time - prev_time == 0 else (1 / (next_time - prev_time))
		distances = [round(time - min(times), 5) for time in times]
		print("----------- FRAME {0} -----------".format(i))
		print("average capture time (s): {0}".format(avgTime))
		print("               distances: {0}".format(distances))
		print("                     fps: {0}".format(fps))
		fps_list += [fps]
		distance_list += [sum(distances) / len(distances)]
		prev_time = next_time
	
	avgFPS = sum(fps_list) / len(fps_list)
	print()
	print('---------------------------------')
	print('                 AVERAGE FPS: {}'.format(avgFPS))
	print('            AVERAGE DISTANCE: {}'.format(sum(distance_list) / len(distance_list)))
	print("FRAMES NOT WITHIN 5% AVG FPS: {}".format(list(filter(lambda x: np.abs(x[1] - fps_list) / fps_list > 0.05, enumerate(fps_list)))))



if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--sync', help='true if multiprocessing acquisition was used', type=bool)
	parser.add_argument('-v', '--verbosity', help='verbosity level for file prints (1 through 4 or DEBUG, INFO, etc.)',
	                    type=str, default="1")
	parser.add_argument('-l', '--logType', help='style of log print messages (cpp (default), pretty)', type=str,
	                    default="cpp")
	args = parser.parse_args()
	log = logger.getLogger(__file__, args.verbosity, args.logType)

	interpret_file(args.sync)

	# if main():
	# 	sys.exit(0)
	# else:
	# 	sys.exit(1)
