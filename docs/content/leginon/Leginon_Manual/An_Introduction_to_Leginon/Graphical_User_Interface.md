## How to use this manual

Many places in the manual, a specific section of a window for a node on a
launcher/computer/instrument is mentioned. The first time they are mentioned, the full path
is shown as

computer/program window/node/subsection of the node to open the setting window/setting
window/section in the window>

It is assumed that the user knows how to follow this path to the specific section of the
window by reading the following graphical user interface (GUI) manual and by a little of
practice. A abbreviated path rather than the full path will be shown in the latter steps for
the same node or application.

## Leginon Window

The window is divided into sections.

-   Status bar - Leginon status display such as completion of application
    loading.

![](images/statusbar.png)

-   Main Menu - Submenus and options derived from Manager and Launcher

![](images/mainmenu.png)

-   Node Selector - Selection for the node shown in the toolbar, message log, and node
    panel. It is also used to indicate warning by turning red for broken node.

![](images/nodeselector.png)

-   Error indicator
    ![](images/error.png)
    - This icon will appear next to a node (in the Node Selector) that has an error.


-   Message Log Information indicator
    ![](images/info.png)
    - This icon will appear next to a node (in the Node Selector) that has information in its message log.


-   User Input indicator
    ![](images/userinput.png)
    - This icon will appear next to a node (in the Node Selector) that requires User input in order to continue processing.


-   Processing indicator
    ![](images/green0.png)
    - This icon will appear next to a node (in the Node Selector) that currently doing processing.

## Node Panel

-   Node Panel - The main display/control panel for the node selected by the node
    selector.

![](images/nodepanel2.png)

-   Toolbar - An area containing tools for general configuration and execution of the
    node as well as some tools for convenience specific for individual node.

![](images/toolbar.png)

-   Message Log - Expandable/scrollable box showing logged information for the
    node.

![](images/messagelog.png)

## Parameter Entry

-   Free entry box- For typing in either text or numbers. If in a setting window, the
    altered entry is saved to the database when it is exited with "OK" or after
    "Apply"/"Test". Most numerical entry accepts floating point number in any python format.
    For example, 10.2 can also be entered as 1.02e+2.

![](images/Entry_box.png)

-   Restricted-entry: The user can only select a valid entry from a list.

![](images/Entry_box_restricted.png)

-   List box- This type of selection box select either an ordered sequence or a simple
    unordered list. If ordered, the items in the sequence can order with "up" and "down"
    tools.

![](images/List_box.png)

* If ordered, the items in the sequence can be shifted around with "up" and "down"
tools.

* Either free or restricted entry box is used for entering a new item to the list.
"+" tool is used to add the entry to the list box. selecting an existing item and
press "-" tool removes the item from the list.

* Multiple items can be selected by holding down the "ctrl" or "shift" key. The
latter selects a range between the first and the new items.

## Image Viewing

-   Display Panel - where the image is shown.


-   (pixel value button)
    ![](images/value.png)
    - Pixel value display tool that shows the (x,y) coordinate the intensity value at the
    cursor. The coordinate origin is set at top-left corner.


-   (ruler button)
    ![](images/ruler.png)
    - Ruler tool that displays the distance between a reference point and the current
    cursor position. Left click at any position inside the display panel defines the
    reference point.


-   (zoom button)
    ![](images/zoom.png)
    - Magnifying glass tool that zoom in (left click) or out (right click) at the location
    of the cursor.


-   (zoom selector list)
    ![](images/zoomselector.png)
    - Direct zoom factor selector.


-   (cross hair button)
    ![](images/bluech.png)
    - Cross hair reference tool displaying a blue cross hair centered at
    the center of the image for reference.


-   (display range selection/input) - Contrast and brightness adjustment of the image
    display. The default is mean +/- 5*standard deviation of image intensity. This can be
    modified by setting the minimum (top scroll bar or entry box) and the maximaum (bottom
    scroll bar or entry box) of the display range.

![](images/contrbright.png)

-   Image Stats Panel

![](images/imstatpanel.png)

-   Image/Target/Marker Control Panel - where the image and targets to be displayed in
    the display panel are determined. Targets are indicated by short cross symbols or other
    shapes of different colors. The items shown with a screen icon are of image type. Items
    of image type can be displayed alone while markers will show only when one of the items
    of image type is also displayed.

![](images/imcontrolpanel.png)

* (status indicator)

![](images/green.png) ![](images/red.png)

- This can be either green or red. During a step-by-step testing of parameters,
green indicates that the step has been tested and you can proceed to the next
testing step. Skiping to a step below a red-indicated step will cause an
error.

* (image display tool)
![](images/display.png)
- Display selection. Only one of the image type can be displayed at
one time.

* (target/marker display tool)
![](images/target_display.png)
- Display target or marker selection. Pressed down (as shown for
the green target) is active. More than one type of markers can be displayed on
layers above the image. If the markers are overlapped, the marker last to be
activated for display is at the top.

* (marker tool)
![](images/arrow.png)
- Marker input selection. Certain markers can be manually edited.
In general, these are targets for further acquisition. In such case, the marker
selection tool can be activated by left clicking the icon. Once activated, left
click in the display panel adds the marker to the image and right click removes the
marker pointed to.

* (settings)
![](images/settings.png)
- Settings are available for certain items in the image control
panel, mainly steps in automatic hole finding. Left click opens the setting window
and the behavior of the setting window is similar to others of the same type.

## Tool Bar

Tool bar of the node contains tools for setting and execution of the node functions. In
addition, some tools are available as pop-up for convenience. The general rule for the flow
of setting up and execution is to go from left to right up to the execution tool (execution
icon).

![](images/toolbar.png)

## Settings Window

Settings windows are opened by left clicking its button

![](images/settings.png)

in the toolbar. Note that only one setting swindow can be opened at a time and that all
functions in the main leginon window is inactivated when a settings window is open even if
the leginon window is the focus. The content of the settings window depends on the purpose
of the settings. The general controls are described here:

* Test: found in settings of image processing steps. When clicked, the current setting
in the window is saved to database and applied to the current input and the results
saved as its output. If the item output is displayed in the node display panel, the
content will be changed accordingly.

![](images/test.png)

* Apply: save the modified setting to database for future execution but not the
current test input. It is activated only if the modification of the input is completed,
normally by pressing the Enter key on the keyboard. Since current GUI does not allow
changes to the main window to be made while setting window is on, Using button is not
necessary since "OK" button will save the settings anyway.

![](images/apply.png)

* Cancel: close the setting window and revert the setting to the last saved values.
This means you can not cancel setting modification if you have "test"ed or "apply"ed the
settings.

![](images/cancel.png)

* OK or Done: close the setting window and save all modified settings to the
database.

![](images/ok.png)

## Execution tools

Found in the node toolbar. They may take on different meanings for different node
classes. The general ones are described here:

* (Execute/Submit button)

![](images/play.png)

: Perform one of the four possible functions if available and active for a node:

# When the application is in standby, it executes, sometimes with setting up the
main function of the node.
# When the application is running automatically, it indicates that the node is in
use.
# When the application is paused for user input, it submit the user approved
inputs and continue on the flow.
# When the application is paused by the "pause" tool in the same node, it removes
the pause flag and continue on the application flow.

* (Pause button)

![](images/pause.png)

: Pause data processing flow when the current input in a queue list is done.

* (Abort button)

![](images/stop.png)

: Abort all data processing of the whole list in the queue.

[< Terminology](/leginon/Leginon_Manual/An_Introduction_to_Leginon/Terminology) | [Minimum Requirements and current NRAMM setup >](/leginon/Leginon_Manual/An_Introduction_to_Leginon/Minimum_Requirements_and_current_NRAMM_setup)

_
