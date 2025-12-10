The Dose Calibrator calculates the electron dose at the current scope and camera state using the beam current of the Tecnai microscope. The information in term is used to calibrate the sensitivity of the CCD using the recorded dose measurement in counts/electron. Alternatively, a sensitivity value is directly inputted.

**Optional bindings for using preset instrument configuration:**

PresetsManagerNode - (PresetChangedEvent) -> DoseCalibrationNode

Other than standard Calibrator settings and tools, the calibrator node contains tools to move main microscope view screen to required position, and entries required for dose conversion. Dose calibration is only as accurate as the screen-current scale factor.

[< Corrector](/leginon/Leginon_Manual/Node_Descriptions/Corrector) | [Drift Manager >](/leginon/Leginon_Manual/Node_Descriptions/Drift_Manager)
