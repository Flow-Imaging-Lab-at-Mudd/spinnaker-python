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

import time
import sys
import os
import argparse
import PySpin
from multiprocess_logging import install_mp_handler
from llpyspin import primary, secondary
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../', 'lib/'))
import logger

if not __name__ == "__main__":
	import traceback

	filename = traceback.format_stack()[0]
	log = logger.getLogger(filename.split('"')[1])

NUM_IMAGES = 30  # number of images to grab
framerate = 40


def acquire_images(device_nums):
	"""
	This function acquires and saves n=NUM_IMAGES images from each device.

	:param num_cams: Number of cameras
	:type num_cams: int
	:return: True if successful, False otherwise.
	:rtype: bool
	"""

	log.VLOG(2, '*** IMAGE ACQUISITION ***\n')
	try:
		result = True

		# Prepare each camera to acquire images
		#
		# *** NOTES ***
		# For pseudo-simultaneous streaming, each camera is prepared as if it
		# were just one, but in a loop. Notice that cameras are selected with
		# an index. We demonstrate pseduo-simultaneous streaming because true
		# simultaneous streaming would require multiple process or threads,
		# which is too complex for an example.
		#

		device_nums.sort()

		num_cams = range(len(device_nums))

		primary_index = -1

		# cams = []
		# for i in num_cams:
		# 	if i != primary_index:
		# 		cams += [secondary.SecondaryCamera(device_nums[i])]
		# 	else:
		# 		cams += [primary.PrimaryCamera(device_nums[i])]

		os.makedirs('MultiCamAcqTest', exist_ok=True)
		video_files = ['MultiCamAcqTest/MCAT-%s.mp4' % (device_nums[i]) for i in num_cams]

		# if primary_index >= 0:
		# 	cams[primary_index].framerate = framerate

		# for i in num_cams:
		# 	if primary_index < 0:
		# 		cams[i].framerate = 'max'
		# 	if i != primary_index:
		# 		cams[i].prime(video_files[i], framerate)

		# if primary_index >= 0:
		# 	cams[primary_index].prime()
		# 	cams[primary_index].trigger()

		secondary_cameras = [secondary.SecondaryCamera(device) for device in device_nums]
		for camera, video_file in zip(secondary_cameras, video_files):
			camera.framerate = 'max' # not sure if this is totally necessary, but the secondary cameras have to have an acquisition framerate >= the trigger frequency or else the acquisition will fail
			camera.prime(video_file, framerate)
		# start the hardware trigger and record as long as you'd like
		curr_time = time.process_time()

		while time.process_time() < curr_time + 5:
			continue
		# stop the hardware trigger
		# timestamps = np.zeros((NUM_IMAGES, len(device_nums)))

		for camera, i in zip(secondary_cameras, num_cams):
			timestamps = camera.stop() # do whatever you want with the timestamps

		# if primary_index >= 0:
		# 	timestamps[:][primary_index] = cams[primary_index].stop()

		# for i in num_cams:
		# 	if i != primary_index:
		# 		timestamps[:][i] = cams[i].stop()

		np.savetxt('MCAT-timestamps.csv', timestamps, delimiter=',')

	except PySpin.SpinnakerException as ex:
		log.error('Error: %s' % ex)
		result = False

	return result


def print_device_info(nodemap, cam_num):
	"""
	This function prints the device information of the camera from the transport
	layer; please see NodeMapInfo example for more in-depth comments on printing
	device information from the nodemap.

	:param nodemap: Transport layer device nodemap.
	:param cam_num: Camera number.
	:type nodemap: INodeMap
	:type cam_num: int
	:returns: True if successful, False otherwise.
	:rtype: bool
	"""

	log.VLOG(3, 'Printing device information for camera %d... \n' % cam_num)

	try:
		result = True
		node_device_information = PySpin.CCategoryPtr(nodemap.GetNode('DeviceInformation'))

		if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
			features = node_device_information.GetFeatures()
			for feature in features:
				node_feature = PySpin.CValuePtr(feature)
				log.VLOG(3, '%s: %s' % (node_feature.GetName(),
				                        node_feature.ToString() if PySpin.IsReadable(
					                        node_feature) else 'Node not readable'))

		else:
			log.warning('Device control information not available.')
		log.VLOG(3, '%%%\n')

	except PySpin.SpinnakerException as ex:
		log.error('Error: %s' % ex)
		return False

	return result


def run_multiple_cameras(device_nums):
	"""
	This function acts as the body of the example; please see NodeMapInfo example
	for more in-depth comments on setting up cameras.

	:param cam_list: List of cameras
	:type cam_list: CameraList
	:return: True if successful, False otherwise.
	:rtype: bool
	"""
	try:
		result = True

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
		install_mp_handler(logger.getLogger(__file__))

		# Acquire images on all cameras
		result &= acquire_images(device_nums)


	except PySpin.SpinnakerException as ex:
		log.error('Error: %s' % ex)
		result = False

	return result


def main():
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
		log.VLOG(1, 'Done! Exiting...')
		return False

	# Run example on all cameras
	log.VLOG(1, 'Running acquisition for all cameras...')

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

		if log.getLevel() >= 3:
			for i, cam in enumerate(cam_list):
				# Retrieve TL device nodemap
				nodemap_tldevice = cam.GetTLDeviceNodeMap()
				# Print device information
				result &= log_device_info(nodemap_tldevice, i, None)

	except PySpin.SpinnakerException as ex:
		log.error('Error: %s' % ex)
		result = False

	device_nums = [0 for _ in cam_list]
	for i, cam in enumerate(cam_list):
		# Retrieve device serial number for filename
		node_device_serial_number = PySpin.CStringPtr(
			cam.GetTLDeviceNodeMap().GetNode('DeviceSerialNumber'))

		if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
			device_serial_number = node_device_serial_number.GetValue()
			log.VLOG(2, 'Camera %d serial number set to %s...' % (i, device_serial_number))

			device_nums[i] = device_serial_number

	del cam

	# Clear camera list before releasing system
	cam_list.Clear()

	# Release system instance
	system.ReleaseInstance()

	result &= run_multiple_cameras(device_nums)

	log.VLOG(1, 'Acquisition complete... \n')

	log.VLOG(1, 'Done! Exiting...')
	return result


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

	from SetSettings import log_device_info

	if main():
		sys.exit(0)
	else:
		sys.exit(1)
