The BeamFixer acquires 3x3 images at the requested beam shift step size centered around
the current value to find the best beam shift and then update the value to Presets Manager. A
list of presets that the update is to be applied is entered in the settings and the first
preset in the list is used for the best beam shift determination. The beam shift step size is
relative to that of the imaging area of the first preset, too.

**Required bindings:**

AcquisitionNodeAlias - (FixBeamEvent) -> BeamFixerNode
BeamFixerNodeAlias - (PresetChangeEvent) -> PresetsManagerNode
BeamFixerNodeAlias - (UpdatePresetEvent) -> PresetsManagerNode
PresetsManagerNode - (PresetChangedEvent) -> BeamFixerNodeAlias

**Target Required:**

Reference Target (best of an empty area)

## BeamFixer Toolbar ( Leginon/BeamFixer/Toolbar> )

-   Settings = open the Acquisition Settings window to control behavior properties of the beam fixer node


-   Play = test the node setting at the current position.

## BeamFixer Settings ( Leginon/BeamFixer/Settings> )

-   Use "image shift | stage position | modeled stage position | image beam shift" to move to target.
     
    The type of calibration movement that is used to navigate to the target. In general, modeled stage position or stage position should be used.


-   If request performed less than xx seconds ago, ignore request.
     
    This is used to control the frequency of the adjustment.


-   Presets Order List
     
    The first preset is used for best shift determination. The beam shift of all presets in the list will be updated with the best value determined in this process. In general, these are presets at the same and the highest magnification used in final acquisition and fine autofocusing. The preset with smallest beam foot print would be the best as the best shift determining preset.


-   Shift beam by xx% of the image (using the first preset in the Presets Order List)


-   Override Preset and Camera Configuration
     
    Used mainly in testing and/or when the best-shift-determining preset is of large dimension so that it is slow to acquire.

[< Acquisition](/leginon/Leginon_Manual/Node_Descriptions/Acquisition) | [Beam Tilt Calibrator >](/leginon/Leginon_Manual/Node_Descriptions/Beam_Tilt_Calibrator)
