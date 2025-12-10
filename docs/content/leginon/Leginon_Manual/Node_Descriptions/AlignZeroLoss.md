AlignZeroLoss class is used to align the energy filter slit so that zero loss peak is allowed to pass through optimally. It is used with Gatan Energy Filter such as Bioquantum series. At given interval and optionally below an intensity threshold, the alignment process is initiated.

## Reference target requirement:

The alignment requires an area that either empty or with little obstruction. This reference target stage position must be defined for the node to function.

## Bindings

**Required Binding for initiate the time interval check and alignment**

*When [phase plate aligner](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/Volta_Phase_Plate_Usage/Phase_Plate_Aligner_Node_Class) is used for phase plate, bind phase plate aligner with align zeo loss peak to force zero loss peak alignment at each phase plate patch change.

[Phase Plate Aligner](/leginon/Leginon_Manual/Leginon_System_version_33/New_User_Features_33/Volta_Phase_Plate_Usage/Phase_Plate_Aligner_Node_Class) -> FixAlignment -> Align Zero Loss Peak

**Required Binding for moving to reference target**

Align Zero Loss Peak ~~[ChangePresetEvent]{style="text-align:right;"}~~> Presets Manager
Presets Manger -> PresetChangedEvent -> Align Zero Loss Peak
Align Zero Loss Peak -> MoveToTargetEvent -> Navigator
Navigator -> MoveToTargetDoneEvent -> Align Zero Loss Peak

## Reference Target Settings

-   Bypass Conditioner should be deactivated for the node to be used.


-   Move Type
    -   Presets Manager: Single move according to the stage position of the target
    -   Navigator: Iterative movement for more accurate targeting. The use case is a grid with no large empty area. If gold foil is used on such grid, it is not easy to return to the desired open hole. To use this, follow the below instruction:

1.  Send a preset that is easy to recognize and return to, such as sq preset.
2.  In Align ZLP node, click on the camera icon to acquire an image. The center of this image is saved as the reference target.
3.  Set up in the settings the desired Navigator Target Tolerance and Navigator Acceptable Tolerance.

## Check Zero Loss Peak Shift Settings

-   Set the standard deviation threshold to 0 if you want it to do alignment based only on time interval.
