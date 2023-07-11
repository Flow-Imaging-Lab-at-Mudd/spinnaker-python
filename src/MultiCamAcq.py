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

import datetime as dt
import sys
import os
import argparse
import PySpin
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../', 'lib/'))
import logger

if not __name__ == "__main__":
	import traceback
	filename = traceback.format_stack()[0]
	log = logger.getLogger(filename.split('"')[1], False, False)

NUM_IMAGES = 1  # number of images to grab

def prepare_camera(i, cam):
	# Set acquisition mode to continuous
	node_acquisition_mode = PySpin.CEnumerationPtr(cam.GetNodeMap().GetNode('AcquisitionMode'))
	if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
		log.error('Unable to set acquisition mode to continuous (node retrieval; camera %d). Aborting... \n' % i)
		return False

	node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
	if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
			node_acquisition_mode_continuous):
		log.error('Unable to set acquisition mode to continuous (entry \'continuous\' retrieval %d). \
					Aborting... \n' % i)
		return False

	acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()

	node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

	log.VLOG(2, 'Camera %d acquisition mode set to continuous...' % i)

	# Begin acquiring images
	cam.BeginAcquisition()

	log.VLOG(2, '%%% Camera {} started acquiring images...\n'.format(i))

	return True


def acquire_images(cam_list, num_frames, folder):
	"""
	This function acquires and saves n=num_frames images from each device.

	:param cam_list: List of cameras
	:param num_frames: Number of frames to capture
	:param folder: Folder name
	:type cam_list: CameraList
	:type num_frames: int
	:type folder: str
	:return: True if successful, False otherwise.
	:rtype: bool
	"""

	if num_frames is None:
		num_frames = NUM_IMAGES
	digits = np.floor(np.log10(num_frames) + 1)

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

		for i, cam in enumerate(cam_list):
			result &= prepare_camera(i, cam)

		# Retrieve, convert, and save images for each camera
		#
		# *** NOTES ***
		# In order to work with simultaneous camera streams, nested loops are
		# needed. It is important that the inner loop be the one iterating
		# through the cameras; otherwise, all images will be grabbed from a
		# single camera before grabbing any images from another.

		device_nums = [0 for _ in cam_list]
		for i, cam in enumerate(cam_list):
			# Retrieve device serial number for filename
			node_device_serial_number = PySpin.CStringPtr(
				cam.GetTLDeviceNodeMap().GetNode('DeviceSerialNumber'))

			if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
				device_serial_number = node_device_serial_number.GetValue()
				log.VLOG(2, 'Camera %d serial number set to %s...' % (i, device_serial_number))

			device_nums[i] = device_serial_number

		os.makedirs('MultiCamAcqTest', exist_ok=True)
		if folder is not None and num_frames > 1:
			os.makedirs('MultiCamAcqTest/{}'.format(folder), exist_ok=True)

		start_time = dt.datetime.now()
		cam_digits = np.floor(np.log10(len(cam_list)) + 1)
		for n in range(num_frames):
			image_results = [PySpin.Image for _ in cam_list]
			new_frame_times = [0 for _ in cam_list]
			for i, cam in enumerate(cam_list):
				try:
					# Retrieve next received image and ensure image completion
					image_results[i] = cam.GetNextImage(1000)
					new_frame_times[i] = (dt.datetime.now() - start_time).total_seconds()
				except PySpin.SpinnakerException as ex:
					log.error('Error: %s' % ex)
					result = False
			
			for i, cam in enumerate(cam_list):
				try:
					if image_results[i].IsIncomplete():
						log.warning('Image incomplete with image status %d ... \n' % image_results[i].GetImageStatus())
					else:
						# Print image information
						width = image_results[i].GetWidth()
						height = image_results[i].GetHeight()
						log.VLOG(2, '%%% Camera {0} grabbed image {1}, width = {2}, height = {3}'.format(
							i, n, width, height))

						# Convert image to mono 8
						image_converted = image_results[i].Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)

						# Create a unique filename
						if folder is None or num_frames > 1:
							img_folder = 'MultiCamAcqTest' if folder is None else 'MultiCamAcqTest/{}'.format(folder)
							image_file = '{}/MCAT-{}-{:0{}f}-{}.jpg'.format(
								img_folder, device_nums[i] if device_nums[i] else i, n, digits, new_frame_times[i])
						else:
							cam_folder = 'cam{:0{}f}'.format(i + 1, cam_digits)
							os.makedirs('MultiCamAcqTest/{}'.format(cam_folder), exist_ok=True)
							image_file = 'MultiCamAcqTest/{}/{}.jpg'.format(
								cam_folder, folder)
						# Save image
						image_converted.Save(image_file)
						log.VLOG(2, '%%% Image saved at {}'.format(image_file))
				except PySpin.SpinnakerException as ex:
					log.error('Error: %s' % ex)
					result = False

			for i, _ in enumerate(cam_list):
				try:
					# Release image
					image_results[i].Release()
				except PySpin.SpinnakerException as ex:
					log.error('Error: %s' % ex)
					result = False

			log.VLOG(2, '%%%\n')

		# End acquisition for each camera
		#
		# *** NOTES ***
		# Notice that what is usually a one-step process is now two steps
		# because of the additional step of selecting the camera. It is worth
		# repeating that camera selection needs to be done once per loop.
		#
		# It is possible to interact with cameras through the camera list with
		# GetByIndex(); this is an alternative to retrieving cameras as
		# CameraPtr objects that can be quick and easy for small tasks.
		for cam in cam_list:
			# End acquisition
			cam.EndAcquisition()

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
				                  node_feature.ToString() if PySpin.IsReadable(node_feature) else 'Node not readable'))

		else:
			log.warning('Device control information not available.')
		print()

	except PySpin.SpinnakerException as ex:
		log.error('Error: %s' % ex)
		return False

	return result


def run_multiple_cameras(cam_list, num_frames, folder):
	"""
	This function acts as the body of the example; please see NodeMapInfo example
	for more in-depth comments on setting up cameras.

	:param cam_list: List of cameras
	:param num_frames: Number of frames to capture
	:param folder: Folder name
	:type cam_list: CameraList
	:type num_frames: int
	:type folder: str
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

		if log.getLevel() >= 3:
			for i, cam in enumerate(cam_list):
				# Retrieve TL device nodemap
				nodemap_tldevice = cam.GetTLDeviceNodeMap()

				# Print device information
				result &= log_device_info(nodemap_tldevice, i, None)

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
		result &= acquire_images(cam_list, num_frames, folder)

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


def main(num_frames=None, folder=None):
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
	log.VLOG(1, 'Running acquisition for all cameras...')

	result = run_multiple_cameras(cam_list, num_frames, folder)

	log.VLOG(1, 'Acquisition complete... \n')

	# Clear camera list before releasing system
	cam_list.Clear()

	# Release system instance
	system.ReleaseInstance()

	log.info('Done!')
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

	if main(folder="0"):
		sys.exit(0)
	else:
		sys.exit(1)
