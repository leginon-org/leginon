-   [Leginon has frozen](/leginon/Leginon_Manual/Trouble_shooting/General_operation_problems#Leginon_main_window_has_frozen)


-   [Leginon has crached](/leginon/Leginon_Manual/Trouble_shooting/General_operation_problems#Leginon_has_crashed)


-   [Python process window does not close after Leginon or Client GUI is closed](/leginon/Leginon_Manual/Trouble_shooting/General_operation_problems#Python_window_does_not_close_on_Windows_after_Leginon_GUI_window_is_closed)


-   [Leginon does not resume data collection after restart](/leginon/Leginon_Manual/Trouble_shooting/General_operation_problems#Data_collection_does_not_resume_after_restarting_Leginon)


-   [Parameter used does not follow the input](/leginon/Leginon_Manual/Trouble_shooting/General_operation_problems#Acquired_image_or_program_parameters_do_not_behave_in_the_same_way_as_the_input)


-   [Changing parameters in setting window does not change node image display](/leginon/Leginon_Manual/Trouble_shooting/General_operation_problems#Parameters_in_setting_windows_do_not_apply_to_the_node_image_display)


-   [Create atlas in different dimension seems not to function](/leginon/Leginon_Manual/Trouble_shooting/General_operation_problems#Parameters_in_setting_windows_do_not_apply_to_the_node_image_display)


-   [Error in starting MSI application with error regarding reference data can not be found](/leginon/Leginon_Manual/Trouble_shooting/General_operation_problems#Parameters_in_setting_windows_do_not_apply_to_the_node_image_display)

## Leginon main window has frozen

Commonly Why: You have a setting window open somewhere. The main window can not do anything if there is a subwindow open.

Solution:

-   Find the setting window on your desktop and close it.
-   Other reason: Run out of memory or other hardware/software/network problems.

Solution:

1.  If the freeze is reproducable, record and report the circumstance when this happens with [Leginon redmine](http://emg.nysbc.org/redmine/projects/leginon/issues/new)
     
2.  Kill frozen Leginon window by one of the following. Try the gentler ones listed at front first. Check to see if any Leginon related process is running by Unix command >ps. If there are left-over python processes, try the next more aggresive one.
     
    -   close the window
         
    -   main>ctrl-c
         
    -   main>xkill
         
        A cursor in the shape of a skeleton will show up. Point it to the window you want to kill and click on it)
         
    -   main>killall --9 python
         
        This kills all processes with name containing python. Therefore, it may kill other process you run in the background!
         
3.  scope> kill and restart Leginon Client if desired.
     
    -   Close the python window. The Leginon window will close automatically this way.
         
    -   If several restart of leginon is needed, Leginon Client is more likely to behave badly without its own restart.
         
4.  Follow [Restarting procedure to continue data acquisition](/leginon/Leginon_Manual/Trouble_shooting/Restarting_procedure_to_continue_data_acquisition)

Still not working: Check for hardware and network problems.

## Leginon has crashed

Commonly Why: You have click too many places and make changes so fast that leginon can not follow it.

Solution:

-   Slow down, especially in preset manager.
-   Other reason: Run out of memory or other hardware/software/network problems.

Solution:

1.  If the crash is reproducable, record and report the circumstance when this happens to those in charge with [Leginon redmine](http://emg.nysbc.org/redmine/projects/leginon/issues/new)


1.  Check to see if any Leginon related process is running by Unix command >ps. If there are left-over python processes, try the next more aggresive one.
     
    -   main>ctrl-c
         
    -   main>killall --9 python
         
        This kills all processes with name containing python. Therefore, it may kill other process you run in the background!
         
2.  scope> kill and restart Leginon Client if desired.
     
    -   Close the python window. The Leginon window will close automatically this way.
         
    -   If several restart of leginon is needed, Leginon Client is more likely to behave badly without its own restart.
         
3.  main> [Restarting procedure to continue data acquisition](/leginon/Leginon_Manual/Trouble_shooting/Restarting_procedure_to_continue_data_acquisition)

Still not working: Check for hardware and network problems.

## Python window does not close on Windows after Leginon GUI window is closed

Why: Python process controls Leginon GUI window. On Windows, Python process is considered broken without Leginon GUI.

-   Always close the python process window to exit both Leginon GUI and the python process.

## Data collection does not resume after restarting Leginon

Commonly Why:

For applications that process targets on grid atlas such as MSI and "Multiscale Tomography", resuming data collection depends on whether "queuing" option is used and if there are still targets left in the queues.

-   Follow the restart instruction

## Acquired image or program parameters do not behave in the same way as the input

Commonly Why: An invalid input is entered such as an invalid camera setting, text in place of an inumber.

-   For camera setting: Leginon/Presets Manager> Send the suspected preset to scope and check the actual values in scope/Instrument/Camera> with a refresh.


-   For all other inputs: Check by reenter the value and hit "Enter" on the keyboard. The cursor will return to the front of the number and the entry box no longer highlighted if it is valid.


-   Preset Manager> Select another preset to refresh the parameter list and then select the problematic preset and check its current saved parameter.

## Parameters in setting windows do not apply to the node image display

### Why:

-   The display panel is set to output other than the direct result of the setting.


-   The function needs to be excuted to its input in the setting window. Use "Test" button to do this.


-   if still not working, "Apply" the parameters before "Test" or "Create" (in Suqare Targeting Node).

## Fail to load a node in an new application with DataAccessError

### Why:

-   A bug in default setting loading causes some JAHCFinder or HoleFinder nodes with bad reference to LowPassFilterSettings.

You may want to get help from the most experienced user at your institute to do these:

-   Start Leginon as "administrator".


-   Identify the node name that failed to load in the application.


-   Start the same application.


-   If you get the same problem, the database entry will need modification, get help from Leginon team to do this if you don't know how.


-   If the application is loaded normally, select the problematic node.


-   If the node belongs to JAHCFinder Class, open the settings for Template. Change LowPassFilter Sigma to a different value, apply the change and then change it back before exist with OK. This will create a new and valid data reference to the node's settings.


-   If the node belongs to HoleFinder Class, open the settings for Edge and for Template. Repeat the same sequence as above.

[< Restarting procedure to continue data acquisition](/leginon/Leginon_Manual/Trouble_shooting/Restarting_procedure_to_continue_data_acquisition) | [Hardware Troubles >](/leginon/Leginon_Manual/Trouble_shooting/Hardware_Troubles)
