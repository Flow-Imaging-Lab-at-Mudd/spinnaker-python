## 3D Flir Camera Configuration
A collection of files meant to help setup and take synchronized photos using PySpin for Flir cameras.

It is recommended that before using this package, to explore the available settings on SpinView first in order to understand how they might affect your camera's output.

### Available Settings
All available settings that can be configured are those that appear in the "Settings" panel on the windows version of SpinView. To add new settings, make sure to add the corresponding setting to the dictionary at the top of the [settings file][1] and add your setting value to the [config file][2].

Only input settings into the config file that you would like to set. If there is a setting that doesn't need to be set, don't include it in the config file.

[1]: src/SetSettings.py
[2]: src/config_file.cfg

### Synchronized Acquisition
To perform synchronized acquisition, first ensure that your cameras are set up in the [primary/secondary configuration][5] specified by the FLIR website. Then, set the corresponding settings in the config file using the `[primary]` and `[secondary]` configuration file headers (default settings are given in the [config file][2]). First run the [settings file][1], then run the [synchronized multiple camera acquisition file][4]. The cameras will start acquiring images once it detects all cameras, and the script will prompt you to press `enter` when you're ready to end acquisition. All files will be saved to the folders `MultiCamAcqTest` and `Timestamps`. The synchronized acquisition uses Joshua Hunt's [parallel-pyspin][8] package with OpenCV backend.

To run diagnostics on this data, run the [diagnostics file][6], with the corresponding config settings in the [config file][2] (only needed if using the aggregate `-a` command line flag*). The diagnostics data includes the an array of distances (i.e. seconds delayed from the first camera to capture a frame) and the average fps for all four cameras. If a large number of frames were captured, the script will aggregate data from a range of frames (averaging fps and distances over all frames in the range).

Finally, an automated image acquisition script for camera calibration is given in the [test image acquisition script][7]. In the the [config file][2], make sure to set the millimeter measurement the first image is acquired at (`RangeMin`), the difference between the millimeter measurement of the first and last images (`zC`), and the difference in millimeters between two successive images (`StepDist`). Make sure that `zC` is divisible by `StepDist`. 

*The aggregate flag was implemented for testing purposes and probably won't be needed for general use – essentially, the acquisition file can be set to automatically acquire video for a range of frames (e.g. back-to-back videos, the first with 100 frames, the second 150, third 200, etc.). The aggregate flag can then automatically run diagnostics on all videos without having to rerun the diagnostics file. The `RangeMin`, `RangeMax`, and `NumReps` flags  give the range of frames that were captured using the formatting of `numpy.linspace`.


[5]: https://www.flir.com/support-center/iis/machine-vision/application-note/configuring-synchronized-capture-with-multiple-cameras/
[6]: src/diagnostics.py
[7]: src/AcquireTestImages.py
[8]: https://github.com/jbhunt/parallel-pyspin

### Unsynchronized Settings Optimization [DEPRECATED]

In SpinView, you may have noticed that there may be a difference between the acquisition frame rate, camera frame rate, and the processed frame rate. The difference between the acquisition frame rate and the camera frame rate would be due to a high exposure time. The difference between the camera frame rate and processed frame rate depends on your computer and what settings you have enabled on your camera. I found that disabling all settings which contain the keyword "auto" (found by searching "auto" in the features tab in SpinView) dramatically increases the processed frame rate. 

This becomes problematic when trying to synchronize cameras because the frame rate at which each camera takes photos determines their synchronization. 
I am working on automatically setting the acquisition frame rate for all of the cameras to the processed frame rate of the camera with the lowest processed frame rate, ensuring that all cameras take photos at the same time, albeit slowly. This may not end up being necessary – at least when I tried this in SpinView it was, but I'm not sure if the code has the same problem.

Another note is that the [multiple cameras acquisition file][3] does not perform true synchronization. 
If you would like to do that, use the [synchronized multiple camera acquisition file][4].

[3]: src/MultiCamAcq.py
[4]: src/MultiCamAcqSync.py

### Logging Verbosities
A note on verbosity levels:
1. View basic informational messages with progress.
2. View settings being changed / photos being acquired.
3. View device information.
4. Verify changed settings.