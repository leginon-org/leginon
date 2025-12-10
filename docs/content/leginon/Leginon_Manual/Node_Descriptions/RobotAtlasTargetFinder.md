RobotAtlasTargetFinder node display old grid atlas of all grids from the same session, allow targets to be picked or loaded, initiate, readjust the targets according to a reacquired image from the robot-reloaded grid, and publish the new targets for proper imaging in the 2nd pass.

**Required bindings with Robot node:**

Robot - (GridLoadedEvent) -> RobotAtlasTargetFinder
RobotAtlasTargetFinder - (UnloadGridEvent) -> Robot
RobotAtlasTargetFinder - (QueueGridEvent) -> Robot

**Required bindings to publish new targets and wait for them to be done:**

RobotAtlasTargetFinder - (ImageTargetListPublishEvent) -> next Acquisition
next Acquisition - (TargetListDoneEvent) -> RobotAtlasTargetFinder

**Required bindings to reacquire a image to readjust the targets on the grid:**

RobotAtlasTargetFinder - (ChangePresetEvent) -> Presets Manager
Presets Manager - (PresetChangedEvent) -> RobotAtlasTargetFinder

[< Robot](/leginon/Leginon_Manual/Node_Descriptions/Robot) | [Tomography >](/leginon/Leginon_Manual/Node_Descriptions/Tomography)
