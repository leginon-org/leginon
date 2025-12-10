Robot node sits between robot controlling program and other Leginon acquisition sequence.

Leginon Robot node communicates with the grid-loading robot controlling program to:

1.  check that the robot exists and is activated
     
2.  tell the robot to load/unload a specific grid
     
3.  hear from the robot when the grid loading/unloading is successful/failed

Note: This node works only with NRAMM grid loading robot. You should modify it to suit your robot for the above functions. As long as it has the same event binding to perform the following functions, your custom node can be used with any Leginon acquisition sequence.

For normal MSI application, the user select grids from an existing grid tray in the Robot node first, then the node interacts with an acquisition sequence in the Leginon application to:

1.  start the image acquisition sequence
     
2.  receive a notice that the acquisition sequence is completed
     
    In the case of 2nd acquisition sequence of grids with targets selected on the old grid atlas, the robot need to also
     
3.  recieve information on which grid to be loaded

**Normal MSI application Required bindings:**

Robot - (MakeTargetListEvent) -> MosaicTargetMaker
target handler such as Acquisition or TargetFilter - (TargetListDone) -> Robot

**Required bindings for 2nd Pass application that re-registrate targets on the specific grid:**

Robot - (GridLoadedEvent) -> RobotAtlasTargetFinder
RobotAtlasTargetFinder - (UnloadGridEvent) -> Robot
RobotAtlasTargetFinder - (QueueGridEvent) -> Robot

Additional Requirement: project database with robot grid and tray information.

[< RCT](/leginon/Leginon_Manual/Node_Descriptions/RCT) | [RobotAtlasTargetFinder >](/leginon/Leginon_Manual/Node_Descriptions/RobotAtlasTargetFinder)
