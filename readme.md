# 3D Flir Camera Configuration
A collection of files meant to help setup and take synchronized photos using PySpin for Flir cameras.

It is recommended that before using this package, to explore the available settings on SpinView first in order to understand how they might affect your camera's output.

## Available Settings
All available settings that can be configured are those that appear in the "Settings" panel on the windows version of SpinView. To add new settings, make sure to add the corresponding setting to the dictionary at the top of the [settings file][1] and add your setting value to the [config file][2].

Only input settings into the config file that you would like to set. If there is a setting that doesn't need to be set, don't include it in the config file.

[1]: src/SetSettings.py
[2]: src/config_file.cfg

## Settings Optimization
In SpinView, you may have noticed that there may be a difference between the acquisition frame rate, camera frame rate, and the processed frame rate. The difference between the acquisition frame rate and the camera frame rate would be due to a high exposure time. The difference between the camera frame rate and processed frame rate depends on your computer and what settings you have enabled on your camera. I found that disabling all settings which contain the keyword "auto" (found be searching "auto" in the features tab in SpinView) dramatically increases the processed frame rate. 

This becomes problematic when trying to synchronize cameras because the frame rate at which each camera takes photos determines their synchronization. I am working on automatically setting the acquisition frame rate for all of the cameras to the processed frame rate of the camera with the lowest processed frame rate, ensuring that all cameras take photos at the same time, albeit slowly. This may not end up being necessary – at least when I tried this in SpinView it was, but I'm not sure if the code has the same problem.

Another note is that the [multiple cameras synchronization file][3] does not perform true synchronization. If you would like to do that, it should be relatively simple to import the python multiprocessing package and write a loop, though I have tried, got an error, and gave up.

[3]: src/MultiCamAcq.py

## Logging Verbosities
A note on verbosity levels:
1. View basic informational messages with progress.
2. View settings being changed / photos being acquired.
3. View device information.
4. Verify changed settings.