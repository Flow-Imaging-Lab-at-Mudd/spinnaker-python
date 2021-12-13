import argparse
import configparser
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../', 'lib/'))
import logger
import numpy as np

if not __name__ == "__main__":
	import traceback

	filename = traceback.format_stack()[0]
	log = logger.getLogger(filename.split('"')[1])


def parseConfigFile(config_path):
	# read settings parameters from a configuration file
	# Input:
	# config_path - string with relative path to configuration file
	#
	# Outputs:
	# config_dict - dictionary with new configurations

	# create config parser and read config file
	config = configparser.ConfigParser(interpolation=configparser.BasicInterpolation())
	config.read(config_path)
	p_config = config['calib-images']

	range_min = p_config.getint('RangeMin')
	zC = p_config.getint('zC')
	step_dist = p_config.getint('StepDist')
	range_max = zC + range_min
	total_steps = int(np.abs(zC / step_dist)) + 1

	return range_min, range_max, total_steps, np.abs(zC), np.abs(step_dist)


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

	import MultiCamAcq

	config = configparser.ConfigParser(interpolation=configparser.BasicInterpolation())
	config.read(config_path)
	range_min, range_max, total_steps, zC, step_dist = parseConfigFile(config_path)

	digits = np.floor(np.log10(zC) + 1)
	for position, image_num in zip(np.linspace(range_min, range_max, total_steps), range(0, zC + step_dist, step_dist)):
		position /= 10
		print('-------------------------------------------')
		print('Ready to capture image {:0{}f} at {}cm.'.format(image_num, digits, position))
		input('Please position your target at {}cm. Then, press Enter to acquire frames.'.format(position))
		result = MultiCamAcq.main(num_frames=1, folder='{:0{}f}'.format(image_num, digits))
		print('Captured!' if result else "Couldn't capture images for position {}cm.".format(position))
	print('-------------------------------------------')
	print('Finished!')

# if main():
# 	sys.exit(0)
# else:
# 	sys.exit(1)
