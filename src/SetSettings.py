# ============================================================================
# Copyright (c) 2001-2021 FLIR Systems, Inc. All Rights Reserved.

# This software is the confidential and proprietary information of FLIR
# Integrated Imaging Solutions, Inc. ("Confidential Information"). You
# shall not disclose such Confidential Information and shall use it only in
# accordance with the terms of the license agreement you entered into
# with FLIR Integrated Imaging Solutions, Inc. (FLIR).
#
# FLIR MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF THE
# SOFTWARE, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE, OR NON-INFRINGEMENT. FLIR SHALL NOT BE LIABLE FOR ANY DAMAGES
# SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR DISTRIBUTING
# THIS SOFTWARE OR ITS DERIVATIVES.
# ============================================================================
#
# AcquisitionMultipleCamera.py shows how to capture images from
# multiple cameras simultaneously. It relies on information provided in the
# Enumeration, Acquisition, and NodeMapInfo examples.
#
# This example reads similarly to the Acquisition example,
# except that loops are used to allow for simultaneous acquisitions.

import os
import PySpin
import sys
from enum import Enum
import configparser
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../', 'lib/'))
import logger

if not __name__ == "__main__":
	import traceback

	filename = traceback.format_stack()[0]
	log = logger.getLogger(filename.split('"')[1], False, False)


class Types(Enum):
	ENUM = Enum
	FLOAT = float
	BOOLEAN = bool
	INTEGER = int


full_settings = {'AcquisitionMode': Types.ENUM.value,
                 'AcquisitionFrameCount': Types.INTEGER.value,
                 'AcquisitionFrameRateEnable': Types.BOOLEAN.value,
                 'AcquisitionFrameRate': Types.FLOAT.value,
                 'ExposureMode': Types.ENUM.value,
                 'ExposureAuto': Types.ENUM.value,
                 'ExposureTime': Types.FLOAT.value,
                 'AutoExposureExposureTimeLowerLimit': Types.FLOAT.value,
                 'AutoExposureExposureTimeUpperLimit': Types.FLOAT.value,
                 'GainAuto': Types.ENUM.value,
                 'Gain': Types.FLOAT.value,
                 'GammaEnable': Types.BOOLEAN.value,
                 'Gamma': Types.FLOAT.value,
                 'BlackLevelSelector': Types.ENUM.value,
                 'BlackLevel': Types.FLOAT.value,
                 'DeviceLinkThroughputLimit': Types.INTEGER.value,
                 'TriggerMode': Types.ENUM.value,
                 'LineSelector': Types.ENUM.value,
				 'LineMode': Types.ENUM.value,
                 'V3_3Enable': Types.BOOLEAN.value,
                 'TriggerSource': Types.ENUM.value,
                 'TriggerOverlap': Types.ENUM.value}


def check_value(value_type):
	if value_type == Types.ENUM.value:
		node_func = PySpin.CEnumerationPtr
	elif value_type == Types.FLOAT.value:
		node_func = PySpin.CFloatPtr
	elif value_type == Types.BOOLEAN.value:
		node_func = PySpin.CBooleanPtr
	elif value_type == Types.INTEGER.value:
		node_func = PySpin.CIntegerPtr
	else:
		return False
	return node_func


def change_setting(i, cam, value, title, value_type):
	# Choose correct CPtr function
	node_func = check_value(value_type)
	if not node_func:
		log.error('Given value type not valid. Please use the ValueTypes enumeration class! \
					Aborting... \n')
		return False

	# Find node
	node_setting = node_func(cam.GetNodeMap().GetNode(title))
	if not PySpin.IsAvailable(node_setting) or not PySpin.IsWritable(node_setting):
		log.error('Unable to set {0} to {2} (node retrieval; camera {1}). Aborting... \n'.format(title, i, value))
		return False

	# Set node to given value
	if value_type == Types.ENUM.value:
		node_setting_value = node_setting.GetEntryByName(value)
		if not PySpin.IsAvailable(node_setting_value) or not PySpin.IsReadable(
				node_setting_value):
			log.error('Unable to set {2} to {0} (entry {0!r} retrieval {1}). \
							Aborting... \n'.format(value.lower(), i, title))
			return False

		setting_value = node_setting_value.GetValue()
		node_setting.SetIntValue(setting_value)
		value = value.lower()
	else:
		node_setting.SetValue(value)

	log.VLOG(2, '%%% Camera {0} {1} set to {2}...'.format(i, title, value))

	return True


def retrieve_settings(i, cam, title, value_type):
	node_func = check_value(value_type)
	if not node_func:
		log.error('Given value type not valid. Please use the ValueTypes enumeration class! \
						Aborting... \n')
		return False

	node_setting = node_func(cam.GetNodeMap().GetNode(title))

	if PySpin.IsAvailable(node_setting) and PySpin.IsReadable(node_setting):
		if value_type == Types.ENUM.value:
			value = node_setting.GetIntValue()
			value = node_setting.GetEntry(value).GetName()
			value = value[value.rfind('_') + 1:]
		else:
			value = node_setting.GetValue()
		log.VLOG(4, '%%% Camera {0} {1:13}: {2}'.format(i, title, value))

	return True


def set_settings(cam_list, config_dict, config_dict_primary, primary_id):
	log.VLOG(2, '*** CHANGING SETTINGS ***\n')
	try:
		result = True

		if log.getLevel() >= 2:
			# Change settings of each camera
			for i, cam in enumerate(cam_list):
				try:
					# Change settings for minimum processing
					log.VLOG(2, 'Changing settings for camera %d...\n' % i)
					
					temp_config_dict = config_dict_primary if i == primary_id else config_dict 
					
					for setting in temp_config_dict:
						result &= change_setting(i, cam, temp_config_dict[setting], setting, full_settings[setting])

					# Retrieve acquisition frame rate
					node_acquisition_frame_rate = PySpin.CFloatPtr(cam.GetNodeMap().GetNode('AcquisitionFrameRate'))
					if not PySpin.IsAvailable(node_acquisition_frame_rate) or not PySpin.IsReadable(
							node_acquisition_frame_rate):
						log.warning('Unable to read acquisition fps (node retrieval; camera {0}). Aborting... \n'.format(i))
						return False
					acq_frame_rate = node_acquisition_frame_rate.GetValue()

					# Retrieve resulting frame rate
					node_resulting_frame_rate = PySpin.CFloatPtr(cam.GetNodeMap().GetNode('AcquisitionResultingFrameRate'))
					if not PySpin.IsAvailable(node_resulting_frame_rate) or not PySpin.IsReadable(
							node_resulting_frame_rate):
						log.warning('Unable to read acquisition fps (node retrieval; camera {0}). Aborting... \n'.format(i))
						return False
					res_frame_rate = node_resulting_frame_rate.GetValue()

					# Retrieve resulting frame rate
					log.VLOG(2, '%%%Camera {0} settings changed with acquisition frame rate {1:.2f} '
					      'and resulting frame rate {2:.2f}...'.format(i, acq_frame_rate, res_frame_rate))
					if 2 < abs(acq_frame_rate - res_frame_rate):
						log.VLOG(2, '%%% \tThey are not equal because the Exposure Time is greater than the frame time.')

					log.VLOG(2, '%%%\n')

				except PySpin.SpinnakerException as ex:
					log.error('Error: %s' % ex)
					result = False

		log.VLOG(4, '*** VERIFYING SETTINGS ***\n')
		# Print new changed camera settings
		if log.getLevel() >= 3:
			for i, cam in enumerate(cam_list):
				log.VLOG(4, 'Retrieving settings for camera %d...\n' % i)
				try:
					# Retrieve device serial number for filename
					node_device_serial_number = PySpin.CStringPtr(
						cam.GetTLDeviceNodeMap().GetNode('DeviceSerialNumber'))

					if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
						device_serial_number = node_device_serial_number.GetValue()
						log.VLOG(4, 'Camera %d serial number: %s' % (i, device_serial_number))

					temp_config_dict = config_dict_primary if i == primary_id else config_dict
					for setting in temp_config_dict:
						result &= retrieve_settings(i, cam, setting, full_settings[setting])

					log.VLOG(4, '%%%\n')

				except PySpin.SpinnakerException as ex:
					log.error('Error: %s' % ex)
					result = False
	except PySpin.SpinnakerException as ex:
		log.error('Error: %s' % ex)
		result = False

	return result


def log_device_info(nodemap, cam_num, primary_id):
	"""
	This function prints the device information of the camera from the transport
	layer; please see NodeMapInfo example for more in-depth comments on printing
	device information from the nodemap.

	:param nodemap: Transport layer device nodemap.
	:param cam_num: Camera number.
	:param primary_id: the ID of the primary camera (if there is one)
	:type nodemap: INodeMap
	:type cam_num: int
	:type primary_id: str
	:returns: True if successful, False otherwise.
	:rtype: bool
	"""

	log.VLOG(3, 'Printing device information for camera %d...\n' % cam_num)

	primary_camera = False
	try:
		result = True
		node_device_information = PySpin.CCategoryPtr(nodemap.GetNode('DeviceInformation'))

		if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
			features = node_device_information.GetFeatures()
			for feature in features:
				node_feature = PySpin.CValuePtr(feature)
				if primary_id is not None:
					primary_camera |= (node_feature.ToString() == primary_id)
				log.VLOG(3, '%%% {0}: {1}'.format(node_feature.GetName(),
				                                 node_feature.ToString() if PySpin.IsReadable(node_feature)
				                                 else 'Node not readable'))
		else:
			log.warning('Device control information not available.\n')

		if primary_camera:
			log.VLOG(3, '%%% Camera {0} is the primary camera.'.format(cam_num))

		log.VLOG(3, '%%%\n')

	except PySpin.SpinnakerException as ex:
		log.error('Error: %s' % ex)
		return False

	return (result, cam_num) if primary_camera else result


def run_multiple_cameras(cam_list, config_dict, config_dict_primary, primary_id):
	"""
	This function acts as the body of the example; please see NodeMapInfo example
	for more in-depth comments on setting up cameras.

	:param cam_list: List of cameras
	:param config_dict: Dictionary with config file settings and values
	:param primary_id: ID of primary camera
	:type cam_list: CameraList
	:type config_dict: dict
	:type primary_id: str
	:return: True if successful, False otherwise.
	:rtype: bool
	"""
	try:
		result = True

		# Retrieve transport layer nodemaps and print device information for
		# each camera
		# *** NOTES ***
		# This example retrieves information from the transport layer nodemap
		# twice: once to print device information and once to grab the device
		# serial number. Rather than caching the nodem#ap, each nodemap is
		# retrieved both times as needed.
		log.VLOG(3, '*** DEVICE INFORMATION ***\n')

		for i, cam in enumerate(cam_list):
			# Retrieve TL device nodemap
			nodemap_tldevice = cam.GetTLDeviceNodeMap()

			# Print device information
			if log.getLevel() >= 3 or primary_id is not None:
				temp_result = log_device_info(nodemap_tldevice, i, primary_id)
				if type(temp_result) != bool:
					result &= temp_result[0]
					primary_id = temp_result[1]
				else:
					result &= temp_result

		# Initialize each camera
		#
		# *** NOTES ***
		# You may notice that the steps in this function have more loops with
		# less steps per loop; this contrasts the AcquireImages() function
		# which has less loops but more steps per loop. This is done for
		# demonstrative purposes as both work equally well.
		#
		# *** LATER ***
		# Each camera needs to be deinitialized once all images have been
		# acquired.
		for i, cam in enumerate(cam_list):
			# Initialize camera
			cam.Init()

		# Acquire images on all cameras
		result &= set_settings(cam_list, config_dict, config_dict_primary, primary_id)

		# Deinitialize each camera
		#
		# *** NOTES ***
		# Again, each camera must be deinitialized separately by first
		# selecting the camera and then deinitializing it.
		for cam in cam_list:
			# Deinitialize camera
			cam.DeInit()

		# Release reference to camera
		# NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
		# cleaned up when going out of scope.
		# The usage of del is preferred to assigning the variable to None.
		del cam

	except PySpin.SpinnakerException as ex:
		log.error('Error: %s' % ex)
		result = False

	return result


def main(config_dict, config_dict_primary=None, primary_id=None):
	"""
	Example entry point; please see Enumeration example for more in-depth
	comments on preparing and cleaning up the system.

	:return: True if successful, False otherwise.
	:rtype: bool
	"""

	# Since this application saves images in the current folder
	# we must ensure that we have permission to write to this folder.
	# If we do not have permission, fail right away.
	try:
		test_file = open('test.txt', 'w+')
	except IOError:
		log.error('Unable to write to current directory. Please check permissions.')
		input('Press Enter to exit...')
		return False

	test_file.close()
	os.remove(test_file.name)

	# Retrieve singleton reference to system object
	system = PySpin.System.GetInstance()

	# Get current library version
	version = system.GetLibraryVersion()
	log.VLOG(3, 'Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))

	# Retrieve list of cameras from the system
	cam_list = system.GetCameras()

	num_cameras = cam_list.GetSize()

	log.VLOG(1, 'Number of cameras detected: %d' % num_cameras)

	# Finish if there are no cameras
	if num_cameras == 0:
		# Clear camera list before releasing system
		cam_list.Clear()

		# Release system instance
		system.ReleaseInstance()

		log.warning('Not enough cameras!')
		log.info('Done!')
		return False

	# Run example on all cameras
	log.VLOG(1, 'Changing settings for all cameras...')

	result = run_multiple_cameras(cam_list, config_dict, config_dict_primary, primary_id)

	log.VLOG(1, 'Setting change completed... \n')

	# Clear camera list before releasing system
	cam_list.Clear()

	# Release system instance
	system.ReleaseInstance()

	log.info('Done!')
	return result


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

	# format settings
	for setting in full_settings:
		if setting in p_config:
			if full_settings[setting] == Types.FLOAT.value:
				get_func = p_config.getfloat
			elif full_settings[setting] == Types.INTEGER.value:
				get_func = p_config.getint
			elif full_settings[setting] == Types.BOOLEAN.value:
				get_func = p_config.getboolean
			else:
				get_func = p_config.get

			p[setting] = get_func(setting)

	if section == 'primary':
		p = p, p_config.get('PrimaryID')

	return p


if __name__ == '__main__':
	# read config file flag passed from terminal
	parser = argparse.ArgumentParser()
	parser.add_argument('-c', '--config_file', help='relative path to config file', type=str)
	parser.add_argument('-v', '--verbosity', help='verbosity level for file prints (1 through 4 or DEBUG, INFO, etc.)',
	                    type=str, default="1")
	parser.add_argument('-l', '--logType', help='style of log print messages (cpp (default), pretty)', type=str,
	                    default="cpp")
	args = parser.parse_args()
	config_path = args.config_file
	log = logger.getLogger(__file__, args.verbosity, args.logType)

	config = configparser.ConfigParser(interpolation=configparser.BasicInterpolation())
	config.read(config_path)
	if dict(config['default'].items()) == {}:
		config_dict_primary, primary_id = parseConfigFile(config_path, 'primary')
		config_dict_secondary = parseConfigFile(config_path, 'secondary')
		if main(config_dict_secondary, config_dict_primary, primary_id):
			sys.exit(0)
		else:
			sys.exit(1)
	else:
		config_dict = parseConfigFile(config_path, 'default')
		if main(config_dict):
			sys.exit(0)
		else:
			sys.exit(1)
