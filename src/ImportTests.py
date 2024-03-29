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
import configparser
import PySpin
from multiprocess_logging import install_mp_handler
from llpyspin import primary, secondary
# import numpy as np
# import datetime as dt

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../', 'lib/'))
# import logger

# if not __name__ == "__main__":
#     import traceback

#     filename = traceback.format_stack()[0]
#     log = logger.getLogger(filename.split('"')[1])

# NUM_IMAGES = 30  # number of images to grab


# def print_device_info(nodemap, cam_num):
#     """
#     This function prints the device information of the camera from the transport
#     layer; please see NodeMapInfo example for more in-depth comments on printing
#     device information from the nodemap.

#     :param nodemap: Transport layer device nodemap.
#     :param cam_num: Camera number.
#     :type nodemap: INodeMap
#     :type cam_num: int
#     :returns: True if successful, False otherwise.
#     :rtype: bool
#     """

#     log.VLOG(3, 'Printing device information for camera %d... \n' % cam_num)

#     try:
#         result = True
#         node_device_information = PySpin.CCategoryPtr(nodemap.GetNode('DeviceInformation'))

#         if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
#             features = node_device_information.GetFeatures()
#             for feature in features:
#                 node_feature = PySpin.CValuePtr(feature)
#                 log.VLOG(3, '%s: %s' % (node_feature.GetName(),
#                                         node_feature.ToString() if PySpin.IsReadable(
#                                             node_feature) else 'Node not readable'))

#         else:
#             log.warning('Device control information not available.')
#         log.VLOG(3, '%%%\n')

#     except PySpin.SpinnakerException as ex:
#         log.error('Error: %s' % ex)
#         return False

#     return result


# def run_multiple_cameras(device_nums, framerate, exposure, binsize, primary_index, capture_num):
#     """

#     :param cam_list: List of cameras
#     :type cam_list: CameraList
#     :return: True if successful, False otherwise.
#     :rtype: bool
#     """
#     result = True

#     install_mp_handler(logger.getLogger(__file__))

#     # Acquire images on all cameras
#     log.VLOG(2, '*** IMAGE ACQUISITION ***\n')

#     try:
#         device_nums.sort()

#         num_cams = range(len(device_nums))

#         if primary_index != -1:
#             primary_index = device_nums.index(primary_index)
#             log.VLOG(3, 'Primary camera found')

#         cams = []
#         for i in num_cams:
#             if i != primary_index:
#                 cams += [secondary.SecondaryCamera(device_nums[i])]
#             else:
#                 cams += [primary.PrimaryCamera(device_nums[i])]
                
#         os.makedirs('MultiCamAcqTest', exist_ok=True)
#         if capture_num > 0:
#             os.makedirs('MultiCamAcqTest/{}'.format(capture_num), exist_ok=True)
#             video_files = ['MultiCamAcqTest/{}/MCAT-{}.avi'.format(capture_num, device_nums[i]) for i in num_cams]
#         else:
#             video_files = ['MultiCamAcqTest/MCAT-%s.avi' % (device_nums[i]) for i in num_cams]

#         if primary_index >= 0:
#             cams[primary_index].framerate = framerate
#             cams[primary_index].exposure = exposure
#             cams[primary_index].binsize = binsize
#             # override binsize for now, need to add to config parser

#         for i in num_cams:
#             if primary_index < 0:
#                 cams[i].framerate = 'max'
#                 log.VLOG(4, 'Setting camera frame rate to maximum')
#             if i != primary_index:
#                 #cams[i].binsize = binsize
#                 #cams[i].exposure = exposure
#                 cams[i].prime(video_files[i], framerate, backend='opencv')

#         if primary_index >= 0:
#             cams[primary_index].prime(video_files[primary_index], backend='opencv')
#             cams[primary_index].trigger()

#         # start the hardware trigger and record as long as you'd like
#         if primary_index >= 0:
#             if capture_num > 0:
#                 time.sleep(capture_num / framerate)
#                 print(dt.datetime.now())
#             else:
#                 input('Starting acquisition. Press Enter to stop.')
#         else:
#             input('To start acquisition, turn on your trigger.\nTo stop acquisition, turn off your trigger. Then press Enter.')
#         # stop the hardware trigger

#         if primary_index < 0:
#             primary_index = 0

#         timestamps = [cams[primary_index].stop()]

#         for i in num_cams:
#             if i != primary_index:
#                 timestamps += [cams[i].stop()]
        
#         try:
#             lengths = [len(x) for x in timestamps]
#         except:
#             log.error('ERROR: Could not acquire video. Exiting...')
#             return False

#         if max(lengths) != min(lengths):
#             if len(timestamps) > 5:
#                 message = "Min: {}, Max: {}".format(min(lengths), max(lengths))
#             else:
#                 message = lengths
#             log.warning("Timestamp lengths are not equal! {}".format(message))
#             log.info("Resulting timestamps will be cropped.")
#             # line up frames
#             timestamps = [times[:min(lengths)] for times in timestamps]

#         timestamp_list = np.transpose(np.array(timestamps))
#         timestamp_list[[0, primary_index]] = timestamp_list[[primary_index, 0]]
        
#         if capture_num > 0:
#             os.makedirs('Timestamps', exist_ok=True)
#             np.savetxt('Timestamps/MCAT-timestamps-{}.csv'.format(capture_num), timestamp_list / 1e3, delimiter=',')
#         else:
#             np.savetxt('MCAT-timestamps.csv', timestamp_list / 1e3, delimiter=',')
#             log.VLOG(2, 'Saving timestamps as MCAT-timestamps.csv')

#     except PySpin.SpinnakerException as ex:
#         log.error('Error: %s' % ex)
#         result = False

#     return result


# def main(framerate, exposure, binsize, primary_index, capture_num=-1):
#     """
#     :return: True if successful, False otherwise.
#     :rtype: bool
#     """

#     # Since this application saves images in the current folder
#     # we must ensure that we have permission to write to this folder.
#     # If we do not have permission, fail right away.
#     try:
#         test_file = open('test.txt', 'w+')
#     except IOError:
#         log.error('Unable to write to current directory. Please check permissions.')
#         input('Press Enter to exit...')
#         return False

#     test_file.close()
#     os.remove(test_file.name)

#     # Retrieve singleton reference to system object
#     system = PySpin.System.GetInstance()

#     # Get current library version
#     version = system.GetLibraryVersion()
#     log.VLOG(3, 'Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))

#     # Retrieve list of cameras from the system
#     cam_list = system.GetCameras()

#     num_cameras = cam_list.GetSize()

#     log.VLOG(1, 'Number of cameras detected: %d' % num_cameras)

#     # Finish if there are no cameras
#     if num_cameras == 0:
#         # Clear camera list before releasing system
#         cam_list.Clear()

#         # Release system instance
#         system.ReleaseInstance()

#         log.warning('Not enough cameras!')
#         log.VLOG(1, 'Done! Exiting...')
#         return False

#     # Run example on all cameras
#     log.VLOG(1, 'Running acquisition for all cameras...')

#     try:
#         result = True

#         # Retrieve transport layer nodemaps and print device information for
#         # each camera
#         # *** NOTES ***
#         # This example retrieves information from the transport layer nodemap
#         # twice: once to print device information and once to grab the device
#         # serial number. Rather than caching the nodem#ap, each nodemap is
#         # retrieved both times as needed.
#         log.VLOG(3, '*** DEVICE INFORMATION ***\n')

#         if log.getLevel() >= 3:
#             for i, cam in enumerate(cam_list):
#                 # Retrieve TL device nodemap
#                 nodemap_tldevice = cam.GetTLDeviceNodeMap()
#                 # Print device information
#                 result &= log_device_info(nodemap_tldevice, i, None)

#     except PySpin.SpinnakerException as ex:
#         log.error('Error: %s' % ex)
#         result = False

#     device_nums = [0 for _ in cam_list]
#     for i, cam in enumerate(cam_list):
#         # Retrieve device serial number for filename
#         node_device_serial_number = PySpin.CStringPtr(
#             cam.GetTLDeviceNodeMap().GetNode('DeviceSerialNumber'))

#         if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
#             device_serial_number = node_device_serial_number.GetValue()
#             log.VLOG(2, 'Camera %d serial number set to %s...' % (i, device_serial_number))

#             device_nums[i] = device_serial_number

#     del cam

#     # Clear camera list before releasing system
#     cam_list.Clear()

#     # Release system instance
#     system.ReleaseInstance()

#     result &= run_multiple_cameras(device_nums, framerate, exposure, binsize, primary_index, capture_num)

#     log.VLOG(1, 'Acquisition complete... \n')

#     log.VLOG(1, 'Done! Exiting...')
#     return result


# def parseConfigFile(config_path, section):
#     # read settings parameters from a configuration file
#     # Input:
#     # config_path - string with relative path to configuration file
#     #
#     # Outputs:
#     # config_dict - dictionary with new configurations

#     # create config parser and read config file
#     config = configparser.ConfigParser(interpolation=configparser.BasicInterpolation())
#     config.read(config_path)
#     #p = {}
#     p_config = config[section]

#     framerate = p_config.getint('AcquisitionFrameRate')
#     exposure = p_config.getint('ExposureTime')
    
#     # check that exposure time is compatible with framerate
#     exposurecheck = int(1/framerate*1000000);
#     if exposurecheck < exposure:
#         log.warning('Maximum exposure time incompatible with frame rate. Reducing exposure time.')
#         exposure = exposurecheck - 5; # exposure margin of 5us below maximum - check actual camera spec here    
    
#     binh = p_config.getint('BinningHorizontal')
#     binv = p_config.getint('BinningVertical')
#     binsize = (binh,binv)

#     if section == 'primary':
#         if p_config.getboolean('V3_3Enable') is not None:
#             primary_id = p_config.get('PrimaryID')
#             log.VLOG(3, 'Primary camera assigned to %s' % primary_id)
#         else:
#             primary_id = -1
#             log.VLOG(3, 'Primary camera not assigned')
            
#         return framerate, exposure, binsize, primary_id

#     return framerate, exposure, binsize


# if __name__ == '__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-c', '--config_file', help='relative path to config file', type=str)
#     parser.add_argument('-v', '--verbosity', help='verbosity level for file prints (1 through 4 or DEBUG, INFO, etc.)',
#                         type=str, default="1")
#     parser.add_argument('-l', '--logType', help='style of log print messages (cpp (default), pretty)', type=str,
#                         default="cpp")
#     args = parser.parse_args()
#     config_path = args.config_file
#     log = logger.getLogger(__file__, args.verbosity, args.logType)

#     from SetSettings import log_device_info

#     config = configparser.ConfigParser(interpolation=configparser.BasicInterpolation())
#     config.read(config_path)
#     if dict(config['default'].items()) == {}:
#         framerate1, exposure1, binsize1, primary_id = parseConfigFile(config_path, 'primary')
#         framerate2, exposure2, binsize2 = parseConfigFile(config_path, 'secondary')

#         log.VLOG(4, 'Frame rate for primary camera is %d' % framerate1)
#         log.VLOG(4, 'Frame rate for secondary cameras is %d' % framerate2)

#         assert framerate1 == framerate2, "Primary and secondary camera frame rates are unequal!"
#         if main(framerate1, exposure1, binsize1, primary_id):
#             sys.exit(0)
#         else:
#             sys.exit(1)
#     else:
#         framerate, exposure, binsize = parseConfigFile(config_path, 'default')
#         log.VLOG(3, 'Frame rate set for default camera to %d' % framerate)

#         if main(framerate, exposure, binsize -1):
#             sys.exit(0)
#         else:
#             sys.exit(1)