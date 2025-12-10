The basic steps that will be described in detail below are:

-   Code the core functionality in a new subclass
-   Define required attribute for all node classes:
    -   Node Settings and its defaults
    -   GUI Panel
    -   Input/Output Events
-   Define new data type or event this node produces
-   Make the gui
-   register it with the list of available nodes

For each task, it is easiest to look at an existing node as an example. Usually we just make a copy of a node the is similar in function and go from there.

Two examples are provided here:

1.  Buffer Cycle as a condition fixer
2.  Matlab targetfinder

## Example 1: Buffer Cycling

We have a base class in Leginon that creates a node to fix a particular instrument condition. The module is leginon/condition.py. When a FixConditionEvent is sent to it, it will check the database to find whether the condition fixing has been done recently. If it has past the timeout defined in its settings (Defined by ConditionerSettingsData in leginondata.py), then it will execute the action defined in its fixCondition function, and reset the timer.

The FixConditionEvent is sent normally from the final exposure Acquisition Node (named "Exposure", "Tomography" etc. depending on the node class and application". While the condition is being fixed, the node will wait for it to return before starting to process the targets it received (meaning moving to the acquisition position, focusing, etc).

To make a new subclass that triggers the vacuum pump that pumps the buffer area of the scope, we will make a subclass of Conditioner here, called BufferCycler. There is no settings change, but we want its settings saved separately from the parent.

## Code the core functionality

-   Make a new class in your new module. Let it inherit a class of Leginon nodes. The lowest base class you can use is node.Node

In our example, see leginon/buffercycler.py [leginon/buffercycle.py](https://emg.nysbc.org/redmine/projects/leginon/repository/revisions/trunk/entry/leginon/buffercycler.py)

The new class inherits conditioner.Conditioner. It defines the string for condition type in setCTypes, and how to call buffer cycling.

## Define the required attributes for all nodes

### Settings

-   The data class that is usually added when a new node is added is the one defines its settings in Leginon gui. Its name should have the class name as prefix.
-   To make the class uses the new settings class, it is defined in the module.

In our example:

1.  Look at the difference in leginon/leginondata.py for [revision 8e7808](https://emg.nysbc.org/redmine/projects/leginon/repository/revisions/8e78081f0d4f2f04675bced4bbb59683bb3c9511), a new subclass of ConditionerSettingsData is defined as BufferCyclerSettingsData without adding anything new.
2.  We define the settings class used in buffercycler.py
        settingsclass = leginondata.BufferCyclerSettingsData
3.  The defaults of the buffer cycler settings are also inherited from conditioner.Conditioner
        defaultsettings = conditioner.Conditioner.defaultsettings

### GUI panel class

Define panelclass to make the class load the right gui panel that you will write later.

    panelclass = leginon.gui.wx.BufferCycler.Panel

### Input/Output Events

We inherit the eventinputs of the parent class in the example.

    eventinputs = conditioner.Conditioner.eventinputs

## Define new data type or event this node produces

New output data type should be defined in leginondata.py, and new event, if any, defined in event.py

Neither is needed in the example.

## Create the user interface

See [leginon/gui/wx/BufferCycle.py](https://emg.nysbc.org/redmine/projects/leginon/repository/revisions/trunk/entry/leginon/BufferCycler.py) for an inherited example that does not need any new definition. This is the minimal definition of Leginon gui.

1.  Make a new file under leginon/gui/wx for the gui definition. In the example: gui/wx/BufferCycler.py
2.  Define Panel Class
3.  OnSettingsTool method, SettingsDialog class, and ScrolledSettings are redefined in this module so that the local one is used.

## Register the node

Register the node by adding it to leginon/allnodes.py as shown in the modification made in r18567

## Add the new node to an application

Use similar procedure as in [Application Editor in Leginon](/leginon/Leginon_Manual/Create_and_Edit_Applications/Use_the_Application_Editor_to_create_Leginon_applications) to add your new node and its event bindings to an existing application.

In our example,

We can add a new node in "MSI-T" application under "Main". The node is created from "BufferCycler" class and named as "Pump Buffer". It needs an FixCondition event binding from "Exposure" node.

## Example 2: TestTargetFinder

We have a base class in Leginon that creates a node to set targets on the input image. The module is leginon/targetfinder.py. The base class in there is TargetFinder.
When a AcquisitionImagePublishEvent is sent to it, it allows targets to be defined on it.

To make a new subclass that uses simple assignment of targets, we will make a subclass of TargetFinder here, called TestTargetFinder. You can see the resulting subclass code in leginon/testtargetfinder.py

## Code the core functionality

-   Make a new class in your new module.

In this example, you can copy leginon/testtargetfinder.py It inherits targetfinder.TargetFinder and start from there.

In this example, it overwrites findTargets function of the base class to create targets from the input and set them on the gui. In this example, the function you need to modify if you want to make one like it is testFindTarget

Instead of the example list of tuples (x,y) coordinates on the image

        focus_targets_on_image = [(50,20)]
        acquisition_targets_on_image = [(100,100),(200,100)]


Your code should analyze self.image (a numpy array representing the image) and find the targets, then set the two variables focus_targets_on_image and acquisition_targets_on_image in the same format.

## The rest of process is the same as the first example.

If your algorithm requires no variable input, you won't have to add new settings, nor add events. gui can also just use gui/wx/TestTargetFinder.py. You just need to register it in allnodes.py and replace another TargetFinder subclass node in the MSI application.

back to [Leginon Developer Guide](/leginon/Leginon_Developer_Guide)
