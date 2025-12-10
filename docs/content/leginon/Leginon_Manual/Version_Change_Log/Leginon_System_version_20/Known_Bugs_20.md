In addition to the bugs listed below, you may view the [Known Bugs Report](http://emg.nysbc.org/redmine/projects/leginon/issues?query_id=18) which contains a dynamic list of known bugs.

### (New for 1.3) Navigator multiple move option does not work properly in MSI imaging sequence with image shift as the move type.

Temporary solution: Always use preset manager when move type is image shift.

### Web viewer may not display all targets on the parent image since target is transferred to a different version.

No temporary solution.

### Kill Application may not kill all process cleanly and may cause problem in connecting to TEM or camera when a new application is reloaded.

Temporary solution: Close leginon and clients and restart.

### Simulate Target use the current image shift as the target shift on top of its preset shift. Therefore, the acquired image may carry an additional image shift if there is an offset created from previouis acquisition.

Temporary solution: Always use Presets Manager to send the preset to be used in
simulation first before usinging Simulate Targets tool.

### Some, although fewer, User Notification "processing " icons do not disappear but stay pointing up after the node is done.

Temporary solution: None.

### When running on LINUX system, Preset selection in /Presets Manager/Importing Presets from Another Session/ add a selection when mouse is left-clicked rather than toggle the selection as in convention.

Temporary solution: Hold down to Ctrl key to select and deselect multiple presets.
Shift key still means selecting all between the two clicks.

Note: This problem is caused by some bug in wxPython for LINUX.

### Web 3way Image viewer does not always show in yellow the revised (i.e. after drift correction) current target in the parent image.

Temporary solution: None.

### Starting Manual Focus directly by clicking on the tool does not use preset but still check for the preset assigned for the focuser node.

[< Bug Fixes](/leginon/Leginon_Manual/Version_Change_Log/Leginon_System_version_20/Bug_Fixes_20)
