The Focuser node is responsible for focusing. Focus sequence determines the sequence of focus steps that can be applied to the focus target the node received. For each item in the sequence, a preset is chosen for imaging and the method of focus (Autofocus or Manual focus) is selected. For autofocus method, defocus and astigmation are measured by beam tilt induced image shift. Alternatively distance from the eucentric height is measured by two opposite stage alpha tilts. The correction type then determines which and how the correction is made. Manual
focus, either through a z height or defocus change, is possible. Eucentric focus can be send to/received form the scope, and the user can also reset current zero defocus. Note that when stage z is used for focus correction, drift is declared automatically so that the drift manager can handle the position change properly.

When the stage is tilted significantly, distortion of the image occurs when beam is tilted. Cosine stretching (Ziese et al. 2003 J. Microscopy 211,179-185) boosts the correlation peak during autofocusing. In addition, a defocus offset is made according to the tilt geometry so that equivalent level of defocus is achieved with image shift at any targeted location. This correction is made automatically.

**Required bindings to Presets Manager:**

FocuserNode - (ChangePresetEvent) -> PresetsManagerNode
PresetManagerNode - (PresetChangedEvent) -> FocuserNode

Focuser normally receives rejected target list from acquisition node rather than from a TargetFinderNode Class although it is possible, too.

AcquisitionNodeAlias - (ImageTargetListPublishEvent) -> FocuserNode
FocuserNode - (TargetListDoneEvent) -> AcquisitionNodeAlias

**For the focuser that initiates drift monitoring, two bindings are needed:**

FocuserNode - (DriftMonitorRequestEvent) -> DriftManagerNode
DriftManagerNode - (DriftMonitorResultEvent) -> FocusNode

**Required Bindings to use drift check image for auto focusing:**

DriftManagerNode - (AcquisitionImagePublishEvent) -> RCTNode

**Bindings needed if to be Fourier transformed:**

FocuserNode- (AcquisitionImagePublishEvent) ->FFTMakerNode

**Focuser node may need target shift correction upon drift:**

FocuserNode - (NeedTargetShiftEvent) - > DriftManagerNode
DriftManagerNode~~(AcquisitionImageDriftPublishEvent)~~> FocuserNode

**Optional Bindings with Navigator to allow (iterative) target move correction:**

AcquisitionNodeAlias - (MoveToTargetEvent) -> NavigatorNodeAlias

## Toolbar

-   Settings = set acquisition and ice melting parameters


-   Focus Sequence = set sequence and focus parameters


-   Play|Pause|Abort = Restart|Pause|Abort focus target processing.


-   Simulate Target|LoopPlay|LoopAbort= Single acquisition|Multiple acquisition with time delay|Stop multiple acquisition of a simulate target


-   Browse Image= Load an image and publish it from this node and pass on for processing.


-   Manual Focus = open the Manual Focus (continuous image acquisition) display to manually correct defocus or stage z ![](images/manualfocus.png)


-   Align Rotation Center = use the current autofocus calibration to align the rotation center beam tilt.

## Settings

-   See [Acquisition node Settings](/leginon/Leginon_Manual/Node_Descriptions/Acquisition)


-   Manual focus tool preset = the preset used for manual focus tool described in the Tool section. This is independent to manual focusing in the focus sequence (new in version 2.2). The pixel size after binning, if any, should be small so that low-defocus can be read.


-   Melt preset = preset used to melt the ice. The beam should be strong and does not need to cover the detector since it is not used for image acquisition.
-   Ice melt time (s) = time the acuisition preset will be fixed over the carbon of an ice grid in order to melt the ice for a better autofocus result. The main screen is lowered to protect th CCD during the long exposure.


-   Acquire final image = enabled means the acquisition image will be acquired after completion of all focus sequence.

## Focus Sequence Settings

-   Sequence = add and select the sequence item to which the settings apply.


-   Enable = perform the focusing function of the selected sequence item.


-   Preset = select the preset used in the focusing.


-   Focuse method = Manual | Beam Tilt | Stage Tilt


-   Autofocus

## Beam tilt (mrad if Beam Tilt; degree if Stage Tilt)= the amount the tilt will be when running the autofocus routine
 
## Use "phase or cross" correlation to register image shift in the autofocus
 
## Fit limit = refers to the fitting residual in the tilt induced image shift equation that determines the defocus and astigmation. If no stigmator calibration was done, the limit need to be higher.
 
## Correction type = Defocus | None | Stage Z
 
## Check for drift greater than "3e-10" meters/s (off by default)
 
## Stigmator correct = enabled means that astigmatism will be corrected
 
## Stigmator Defocus Min/Max = minimum and maximum defocus values (m) used for correcting the astigmatism

## Manual Focus

-   Settings:

- Mask radius: "1" % of image = center percentage of FFT that is masked out in order to see the FFT easier on the screen

- Icrement: 5e-7 m = the incremental amount of defocus or stage z change

-   Play = restart continous image acquisition


-   Pause = pause the continous image acquistion


-   Stop = stop the continuous image acquisition


-   "Defocus | Stage Z" = correction options


-   Plus | Minus = increment by Defocus or Stage Z


-   `<blank> m = value that can be set with Set Instrument button


-   Set Instrument = send the above defocus/stage Z value to the microscope


-   Reset Defocus = reset the defocus to zero at the microscope


-   Eucentric from instrument = save eucentric height value from the microscope


-   Eucentric to instrument = send the saved Leginon eucentric height to the microscope


-   Image = show the current image


-   Power = show the FFT of the current image

## Align Rotation Center

-   Align the beam tilt to the rotation center based on the current defocus/stigmator calibration.

[< FFT Maker](/leginon/Leginon_Manual/Node_Descriptions/FFT_Maker) | [Gon Modeler >](/leginon/Leginon_Manual/Node_Descriptions/Gon_Modeler)
