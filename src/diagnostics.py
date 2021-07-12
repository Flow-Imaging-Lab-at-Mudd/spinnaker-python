import sys
import os

from multiprocess_logging import install_mp_handler
from multiprocessing import Pool
import argparse
import configparser
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../', 'lib/'))
import logger
import glob
import os
import numpy as np
from scipy import stats

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


def interpret_file(sync, summary=False, framerate = -1, frame_total=0):
	if sync:
		if summary:
			all_times = np.loadtxt('Timestamps/MCAT-timestamps-{}.csv'.format(frame_total), delimiter=',')
		else:
			all_times = np.loadtxt('MCAT-timestamps.csv', delimiter=',')
		frames = all_times.shape[0]
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
		all_times = np.array(all_times)

	prev_time = [0]
	mult = int(10 ** (np.log10(frames) - 1))
	fps_list = np.zeros((int(frames / mult), mult))
	distance_list = np.zeros((int(frames / mult), all_times.shape[1], mult))
	for i in range(int(frames / mult)):
		times = all_times[mult*i:,:] if mult * (i + 1) > frames else all_times[mult * i  : mult * (i + 1),:]
		avgTime = [np.sum(time) / time.size for time in times]

		fps = [0 if avgTime[0] == prev_time[-1] else (1 / (avgTime[0] - prev_time[-1]))]
		fps += [0 if avgTime[i] == avgTime[i+1] else (1 / (avgTime[i+1] - avgTime[i])) for i in range(mult - 1)]
		fps = np.array(fps)

		distances = np.transpose(np.array([[item - np.min(time) for item in time] for time in times]))
		display_distances = [np.round(stats.trim_mean(distance, 0.1), decimals=5) for distance in distances]

		if not summary:
			message = 'FRAMES {}-{}'.format(i * mult, (i+1) * mult - 1) if mult > 1 else 'FRAME {}'.format(i)
			print("----------- {} -----------".format(message))
			if mult == 1:
				print("average capture time (s): {0}".format(avgTime))
			print("               distances: {0}".format(display_distances))
			print("                     fps: {0}".format(np.mean(fps)))

		fps_list[i,:] = fps
		distance_list[i, :, :] = distances
		prev_time = avgTime

	fps_list = np.reshape(fps_list, -1)
	distance_list = np.reshape(distance_list, -1)
	
	avgFPS = stats.trim_mean(fps_list, 0.1)
	print()
	if not summary:
		print('-------------------------------------------')
	print('                 AVERAGE FPS: {}'.format(np.round(avgFPS, decimals=5)))
	print('            AVERAGE DISTANCE: {}'.format(np.round(stats.trim_mean(distance_list, 0.1), decimals=7)))
	print('             FRAMES CAPTURED: {}'.format(frames))
	if not summary:
		print("FRAMES NOT WITHIN 5% AVG FPS: {}".format(list(filter(lambda x: np.abs(x[1] - avgFPS) / avgFPS > 0.05, enumerate(fps_list)))))
	
	if framerate >= 0:
		lagged_frames = list(filter(lambda x: x[1] < framerate * 0.9, list(enumerate(fps_list))[min(int(frame_total/2), 50):]))
		lag_check = lagged_frames[:min(5, len(lagged_frames))]
		i = 1
		while len(lagged_frames) > 0 and lag_check[-1][0] - lag_check[0][0] > len(lag_check) - 1:
			lag_check = lagged_frames[i:min(5+1, len(lagged_frames))]
			i += 1
		return frames, () if len(lagged_frames) == 0 else lag_check[0]


def parseConfigFile(config_path, section):
	# read settings parameters from a configuration file
	# Input:
	# config_path - string with relative path to configuration file
	#
	# Outputs:
	# config_dict - dictionary with new configurations

	# create config parser and read config file
	config = configparser.ConfigParser(interpolation=configparser.BasicInterpolation())
	config.read(config_path)
	p = {}
	p_config = config[section]
	result = []

	if section != 'secondary':
		test_config = config['aggregation']
		result += [test_config.getint('RangeMin')]
		result += [test_config.getint('RangeMax')]
		result += [test_config.getint('NumReps')]

	result += [p_config.getint('AcquisitionFrameRate')]
	if section == 'primary':
		if p_config.getboolean('V3_3Enable') is not None:
			result += [p_config.get('PrimaryID')]
		else:
			result += [-1]

	return result


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--sync', help='true if multiprocessing acquisition was used', type=bool, default=False)
	parser.add_argument('-a', '--aggregate', help='true if multiple runs over a range of values', type=bool, default=False)
	parser.add_argument('-c', '--config_file', help='relative path to config file', type=str)
	parser.add_argument('-v', '--verbosity', help='verbosity level for file prints (1 through 4 or DEBUG, INFO, etc.)',
	                    type=str, default="1")
	parser.add_argument('-l', '--logType', help='style of log print messages (cpp (default), pretty)', type=str,
	                    default="cpp")
	args = parser.parse_args()
	config_path = args.config_file
	log = logger.getLogger(__file__, args.verbosity, args.logType)

	import MultiCamAcqSync

	if args.aggregate:
		config = configparser.ConfigParser(interpolation=configparser.BasicInterpolation())
		config.read(config_path)
		if dict(config['default'].items()) == {}:
			try:
				range_min, range_max, num_reps, framerate1, primary_id = parseConfigFile(config_path, 'primary')
				framerate2 = parseConfigFile(config_path, 'secondary')[0]
				assert framerate1 == framerate2, "Primary and secondary camera frame rates are unequal! P: {}, S: {}".format(framerate1, framerate2)
				for stop_frame in np.linspace(range_min, range_max, num=num_reps):
					stop_frame = int(stop_frame)
					print('-------------------------------------------')
					print('                  Num Frames: {}'.format(stop_frame))
					MultiCamAcqSync.main(framerate1, primary_id, capture_num=stop_frame)
					stopDict = {}
					stopDict[stop_frame] = interpret_file(args.sync, summary=True, framerate=framerate1, frame_total=stop_frame)
					print('           Frame Stop w/ FPS: {}'.format(stopDict[stop_frame]))
					print()
				print('-------------------------------------------')
				print('RESULTS:')
				print(stopDict)
			except:
				print('Reached an error. Probably because one camera captured 0 frames.\n')
				print('-------------------------------------------')
				print('RESULTS:')
				print(stopDict)
		else:
			range_min, range_max, num_reps, framerate = parseConfigFile(config_path, 'default')
			for stop_frame in np.linspace(range_min, range_max, num=num_reps):
				MultiCamAcqSync.main(framerate, -1)
				interpret_file(args.sync, summary=True, framerate=framerate, frame_total=stop_frame)
	else:
		interpret_file(args.sync)

	# if main():
	# 	sys.exit(0)
	# else:
	# 	sys.exit(1)
