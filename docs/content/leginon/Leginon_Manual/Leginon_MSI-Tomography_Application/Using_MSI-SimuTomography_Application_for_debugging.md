MSI-SimuTomography application uses the images and parameters saved for a particular tilt series to recreate and display what the algorithm has done during the data collection. It is mainly for spotting problems that was not observed since the users are often away from the computer running the Leginon during data collection.

The application is available in your myami installation under leginon/applications and you can import it following the instruction for [Application Import](/leginon/Leginon_Manual/Administration_Tools/Applications) through the web administration tools.

## Starting the application

This application does not require the microscope to run and should always run on an existing session since you want to simulate an existing tilt series from an existing session.

1.  Start Leginon
        start-leginon.py
2.  Choose to return to the session that you want to run the simulator in, Edit the client list to remove the scope as an client so that you don't interfere someone else's running Leginon session.
3.  Leginon/Application/Run...> Choose from the run application list, "MSI-SimuTomography" to start the application
4.  Let all node launchers be your current computer, they have no consequences in this application.

## Setup parameters

1.  Leginon/Tomography> click on settings tool for the node to open the settings window.
2.  Leginon/Tomography/Settings> select the tilt series that you want to recreate display and change other parameters if you want to see the effect of different correction method on the tracking process. By default, you should use "saved value for this series" as the model.
3.  Leginon/Tomography/Settings> click "OK" button to save and close the settings window.

## Start and Observe the tracking process

Leginon/Tomography> click on "Simulated Target" tool to start the simulation. You can repeat the process as many times as you like.

The display layout looks like the tomography node in the actual data collection. You should check:

1.  Does the correlation peak appears at the expected position as indicated by the pair of images in the first two panels.
2.  Is there any error message appears in the Leginon logger window or at the text terminal where Leginon was launched.
3.  If you have changed the parameters used for correlating the images, does any of the print out in the text terminal regarding current Prediction or correlation in favor of finding the better tracking and/or correct position of the correlation peak?

If you find a better set of parameters, try them out on other tilt series in the same session to make sure that they do not cause degradation of tracking performance on them. If there is no problem, you can use the new parameter next time when you acquire tilt series of the similar sample.

[< Full Protocol on a F30 with an energy filter](/leginon/Leginon_Manual/Leginon_MSI-Tomography_Application/Full_Protocol_on_a_F30_with_an_energy_filter) | [Leginon "MSI-Tomography" Application ^](/leginon/Leginon_Manual/Leginon_MSI-Tomography_Application)
