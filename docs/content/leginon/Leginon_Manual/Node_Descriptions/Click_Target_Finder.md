Click Target Finder is a basic node that takes input images and allows the user to manually select targets on the input image. The image target list is the output of this node. Because most of its subnodes such as Holde Finder and RasterFinder have the option of skipping automatic finding, they can perform the job of this base class. Therefore, the node is seldom used.

**Required bindings for recieving images and publishing targets:**

previous Acquisition or Focuser- (AcquisitionImagePublishEvent) -> ClickTarget Finder
ClickTargetFinder - (ImageTargetListPublishEvent) -> next Acquisition or Focuser
ClickTargetFinder - (QueuePublishEvent) -> next Acquisition or Focuser
ClickTargetFinder - (ReferenceTargetListPublishEvent) -> AlignZeroLossPeak or MeasureDose

**Required bindings for proper waiting among nodes:**

ClickTargetFinder- (ImageProcessDoneEvent) - > previous Acquisition or Focuser
next Acquisition or Focuser- (TargetListDoneEvent) - > ClickTargetFinder

This node only has the ability to display target types and submit (send) new image targets to another node via the Submit Targets button.

## Settings

-   Allow for user verification of picked holes = When enabled, this feature will pause and wait for the user to verify whether the correct exposure and focus targets have been selected after the Hole Finder finished processing the input image.


-   Queue up targets = When enabled, submit targets do not publish them immediately but to put them in a target list queue.


-   Declare drift when queue submitted= When enabled, force target shift correction when the queue is submitted. Useful when accurate targeting is needed.

[< Beam Tilt Imager](/leginon/Leginon_Manual/Node_Descriptions/Beam_Tilt_Imager) | [Corrector >](/leginon/Leginon_Manual/Node_Descriptions/Corrector)
