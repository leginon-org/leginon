## FEI Scope: You can skip this if you plan to do [Modeled Stage Position calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Modeled_Stage_Position_calibration) because it will save the result in this form as well.

## JEOL Scope: Adjust BACKLASH parameter values in jeol.cfg if consistent stage position movement is not possible.

Stage Position matrix calibrations can used to navigate at low magnifications or in iterative nagivator movement. Modeled Stage
Position Rotation/Scale calibration also saves such matrix. Therefore, only one of them is needed.

[How does matrix calibration work?](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Shift_matrix_calibration)

1.  Leginon/Presets Manager> Select the low mag preset for the calibration and send
    its parameter to the microscope.
     
2.  Microscope> Make sure there are distinguishable features for cross correlation
    in the range of movement to be used and that the beam is not clipping the area of the digital camera
    acquisition. Removing the objective aperture may be necessary.
     
3.  Leginon/NodeSelector> select "Matrix" node.
     
4.  Acquire test image and change the Camera Configuration in "setting" window to values
    that will produce a good image in a reasonable exposure time. Don't forget that
    "Overwrite Preset" has to be checked if you want to change the Camera Configuration in
    the node.
     
5.  Leginon/Matrix/Toolbar/Settings> select correlation method in the window. Phase
    correlation is especially efficient in cases where periodic pattern exist. The pattern
    often causes cross correlation peak search to misidentify the correct peak in the
    multiple peak correlation map.
     
6.  Leginon/Matrix/Toolbar> select "stage position" as the Parameter and open the
    "Parameter Setting" window.
     
7.  Leginon/Matrix/Matrix Settings> Change "Average # position" to a number 1+ (less
    than 10 for a faster calibration). The value 1 will give a moderate to poor calibration.
    Recommendations are as follow:
     
    -   Phase correlation
         
    -   Stage position
         
    -   Tolerance = 12-50% Depending on the scopes and the accuracy of pixel size calibration at the magnification
         
    -   Shift fraction = 25%
         
    -   Average = 5
         
    -   Interval = 1.5e-05 meters
         
        Because the measurements are variable depending of stage position, an averaging
        technique is used to create a matrix that can be more generally applied to positions
        over a greater range. A better method is to model the stage position ( <http://emg.nysbc.org/publications/techreports/99-001/> ).
         
8.  Leginon/Matrix/Toolbar> left-click (Execute icon) to calibrate.
     
9.  The image should be shifting 10-30% of the imaging area. The images can be
    monitored in Image Display Panel with display selection in image control panel set to
    "image". The cross correlation and its peak can also be displayed. There has to be
    recognizable imaging feature that moves with stage movement for good correlation at all
    time for a good calibration. For example, if the CCD is covered completely by the grid
    bar, the calibration will certainly fail.
10. Use Navigation node to [check the result of the calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Checking_Matrix_and_Modeled_Stage_Position_Calibration).

## Troubleshooting:

The logger shows the percentage error and suggests a pixel size for the magnification.

### consistent percentage error in multiple measurement in LM

At LM range, this systematic error often happens because the pixel size has high uncertainty from extrapolation while the stage mechanics is pre-calibrated and reliable. As a result the latter should be used as the reference. If you are at eucentric height and focus as it should be in the calibration, you should adjust pixel size at this magnification as suggested.

### inconsistent percentage error in multiple measurement at high magnification

The field of view at high magnification is too small for the stage to move consistently according to our instruction for calibration. However, the magnification and pixel size are more reliable. Try using a lower magnification calibration in the same project mode to scale the value by magnification. For example, calibrate at hl preset and then scale that to en,fa magnifications. See [Scaling Stage Position Matrix](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Stage_Position_matrix_calibration/Scaling_Stage_Position_Matrix)

[< Beam Shift matrix calibration (FEI scopes)](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Beam_Shift_matrix_calibration) | [Modeled Stage Position calibration >](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Modeled_Stage_Position_calibration)
[< Image Beam Compensation calibration (JEOL scopes)](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Image_Beam_Compensation_Calibration) | [Modeled Stage Position calibration >](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Modeled_Stage_Position_calibration)
