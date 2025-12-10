The Tomography node is a subclass of [Acquisition](/leginon/Leginon_Manual/Node_Descriptions/Acquisition). This node receives a Published Target List and navigates to each target using the specified Move Type. Then, a series of images at assigned tilt angles are acquired and published to the database. Many of the Algorithms are based on UCSF Tomo. The node can also initiate dose measurement and alignment of zero loss peak for Gatan energy filter.

Be aware that this node multiplies the CCD counts by 10 and converts the values into signed Int16 before it is displayed and saved as MRC file to reduce the file size. Therefore, a CCD count (after binning and flat-field correction) of 3276.8 or higher will overflow.

**Required bindings:**

TomographyNodeAlias- (ChangePresetEvent) -> PresetsManagerNode
PresetsManagerNode - (PresetChangedEvent) -> TomographyNodeAlias

**Bindings with the previous target makers or click target finder:**

TargetMakerNodeAlias - (ImageTargetListPublishEvent) -> TomographyNodeAlias
TomographyNodeAlias - (TargetListDoneEvent) -> TargetMakerNodeAlias

**Optional Bindings with DriftManager to allow target correction after drift:**

TomographyNodeAlias - (NeedTargetShiftEvent) -> DriftManagerNodeAlias
DriftManagerNodeAlias - (AcquisitionImageDriftPublishEvent) -> TomographyNodeAlias

**Optional Bindings with another Acqusition subclass (for example, Focuser or Acquisition) that processes target types rejected by Tomography node:**

TomographyNodeAlias - (ImageTargetListPublishEvent) -> AnotherAcquisitionSubNodeAlias
AnotherAcquisitionSubNodeAlias - (TargetListDoneEvent) -> TomographyNodeAlias

**Optional Bindings to Reference subclass (for example, DoseMeasurement or AlighZLP) that initiates a set process at the reference target position:**

TomographyNodeAlias - (DoseMeasurementPublishEvent) -> MeasureDoseNodeAlias
TomographyNodeAlias - (AlignZeroLossPeakPublishEvent) -> AlighZeroLossPeakAlias

## Tomography Toolbar ( Leginon/Tomography/Toolbar> )

-   same tools are available as for any Acquisition sub Class node.

## Tomography Settings ( Leginon/Tomography/Settings> )

The top portion is identical to Acquisition/Settings in an Acquisition node. Only the part related to Tomography is described.

-   Tilt min, max, start, and step angles (in degree).

Start at 0 degree and using a negative step cause the node to collect data in the negative angles first.

-   Use equally sloped (symmetric) angles, power of 2 angles in 180 degree range can be used instead of the default equal angle increment.


-   Exposure Total dose is divided by the number of tilt angles to obtain the actual exposure time with known dose of the preset. The actual exposure time should also be limited by Min/Max specified.


-   "Before Collection Measure Dose" will acquire a dose image (512x512 at the center using current preset and at the reference image. The result will update the preset dose for the data collection dose fractionation calculation.


-   Before Collection Run buffer cycle |Align zero loss peak dose what it says.

[< RobotAtlasTargetFinder](/leginon/Leginon_Manual/Node_Descriptions/RobotAtlasTargetFinder) | [Transform Manager >](/leginon/Leginon_Manual/Node_Descriptions/Transform_Manager_)
