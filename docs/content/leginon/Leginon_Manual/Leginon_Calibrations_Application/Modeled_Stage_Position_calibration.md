## Note: FEI Compustages made after around 2014 have much smaller periodical fluctuation than the previous models. The calibration can be done with Matrix node is likely good enough. This calibration with 0 harmonic term can be used in the case that the x and y axis are not quite orthogonal.

The "GonioModeling" node, an instance of Modeler node class, models the goniometer/stage movement to give a more accurate stage position/movement calibration. The stage position is modeled in both and y directions. For a more accurate calibration, many points or images need to be acquired to give a more accurate mathematical fit to the function. This calibration works best on a grid that will always give good cross correlations. Slot grids give large areas that can cross correlate well, but this type of grid tends to drift. Negatively stained grids or grids with dirts on it and carbon in the background will work well. Used Quantifoil grid can be used, too, if there is enough dirt or large protein complex that keeps one hole distinquishable from all others.

Modeled Stage Position calibration will also copy its results in image scale and rotation in the form of stage position matrix calibration. Therefore, if Modeled Stage Position calibration is performed in "GonioModeling" node, there is no need to calibration stage position matrix alone in "Matrix" node.

> *How does modeled stage position calibration work?*

> There are two parts of results from doing a modeled stage calibration: 1) a function (in
> the form of a harmonic series) that models the mechanical behavior of the stage, and 2) a
> magnification adjustment (scaling and rotation) that allows the model function to be used at
> different magnifications. Part 1 needs to be done at only one magnification, because the
> result will be normalized in the database so that it can be used at any other magnification.
> Part 2 needs to be done at any other magnifications that you wish to use this calibration.
> The user interface of GonModeler node gives you two methods: "Fit Model" and "Rotation/Scale
> Only" These two methods are really identical except for the final result they store in the
> database. "Fit Model" will store both part 1 and 2 above. "Rotation/Scale Only" will only
> store part 2 (and assumes that you already have part 1 done). Since "Fit Model" is
> responsible for part 1, you generally need to measure a lot of points to get a good fit. You
> will normally select between 2 and 5 terms for the harmonic series to get a good fit. **FEI stage after 2014 will do well with 0 term, just enough to handle slightly non orthogonal situation**.
> The "Mag Only" method will also fit a function to your measured points using the number of terms
> you specify. But the resulting best fit function is not stored in the database. Only the
> constant term of the resulting function is stored, because this can be used to scale the
> existing normalized model function to the current magnification.

> See ( <http://emg.nysbc.org/publications/techreports/99-001/> ).

## Full calibration

NOTE: This full calibration needs to be completed for both the x and y axis, but at only
one magnification. The Magnification Adjustment calibration below can be after this has been
completed if the calibration needs to be improved.

1.  Microscope>Place a grid into the microscope that will cross correlate well at
    low magnifications or at the mag used for "sq" preset, e.g. 550x.
     
2.  Microscope>Go to 550x. (Use magnifications between 550x - 1100x for best
    results)
     
    or
     
    Leginon/Presets Manager> Select the "sq" preset for the calibration and send
    its parameter to the microscope.
     
3.  Leginon/Node Selector> select "Goniomodeling" node.
     
4.  Leginon/GonioModeling/Settings/Measurement>:
     
    -   Choose x axis
         
    -   Choose 25-200 points (25 is sufficient to cover 2 periods of a 60 um model
        with the 5e-06 m interval below)
         
    -   Default tolerance is 25 %. A larger value may be necessary to include all
        valid points.
         
    -   Choose a 5e-06 meters interval ( so that 5 harmonic terms of a 60 um model
        can be sampled sufficiently)
         
    -   Enter a label (Default is session name). The label separates measurements of
        the same magnification but the same one can be used for different magnifications
        and axes.
         
    -   Click OK to exit setting window.
         
5.  Leginon/GonioModeling> left click "Measure" tool ![](images/cam_ruler.png) to start measuring shift of the image upon each movement. For all 200
    points to be completed, the process will take about 50 minutes
     
6.  Leginon/GonioModeling/Settings/Modeling>
    Check the parameters. Most of them should be filled in automatically according to
    the measurements just made.
     
    -   label: same name that was used in the Measurement.
         
    -   magnification: same magnification that was used to collect the data points
        in the Measurement.
         
    -   axis: same as what was just measured.
         
    -   Use the default 5 terms for the periodical model fitting. Use 0 terms if
        fit as a straight line.

 

Deactivate "Scale and Rotation Adjustment Only".
 

1.  Leginon/GonioModeling> left click Calibrate tool ![](images/play.png) to start model fitting.
     
2.  Once fitted, the data and the harmonic series fit for the mechanical error can be
    viewed through http://yourhost/myamiweb/admin.php under [Goniometer](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Modeled_Stage_Position_calibration). A good fit should look like this:
     
    ![](images/gon_graph.png)

The y-axis in the graph is the deviation from linearity normalized so that if the movement is linearly responding to the instruction sent by the program, the y-value would remain at 1.00.

0.99 means that the resulting movement is 1 % short of what it is asked to moved to (meaning that if you ask it to move 5 um, it moved to 4.95 um). The lowest point in the example graph above gives a y-value of 0.70.

NOTE: Newer generation of microscope has less of the oscillation. You may find that you get better fit with fewer harmonic terms. If this is the case, just change the number of the terms and left click on ![](images/play.png) again. If your deviation from linearity never exceeds 1 % except the very first measurement, you can use 0 terms, just like what you do for goniometer y-axis below.

1.  Repeat steps 3 to 7 for the y axis. You can use the same label as the one for x
    axis. If your goniometer has no periodic deviation from a linear movement for the y
    axis, use 0 terms for harmonic series fitting.
     
2.  Use Navigation node to [check the result of the calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Checking_Matrix_and_Modeled_Stage_Position_Calibration) after both axes are fitted.

If the data are over fitted, the modeled move may be worse than the simple linear
matrix calibration. In such cases, it is better to decrease the number of terms in the
fitting and redo the Fit Model step. For example, on our Two older FEI Tecnai, the x periods
was ~ 62 microns and fitted well with 5 harmonic terms. The y axis did not have a true
harmonic model, therefore, 0 terms were used.

During a data acquisition session, if the targeted holes are not being centered, first
check image alignment between sq and hl presets. If it is o.k., redo the Mag Only
calibration (see below) for a shorter calibration time. If fails, the full calibration is
needed.

**Full GonModeling Calibration Need for the Example MSI:**

  Preset   magnification
  -------- ---------------
  sq       550

## Trouble Shooting Bad Points in the Measurement

A bad point is an outlier imagex or imagey measurement. The imagex and imagey values are
displayed in the message log window. They comes from, in most cases, failure in finding the
correct correlation peaks. Not all bad points will be rejected correctly because they can
accidentally fall within the tolerance. Since they can only be removed within the database
once inserted, avoiding them is preferable.

To avoid bad points coming from false correlation peaks, you can do one or more of the
following:

-   If the bad points come from drifting grid or grid with bad contrast in general,
    change the grid to one that doesn't drift as much or that has better contrast.


-   move the initial stage position to a different place where objects can be followed
    in the images.


-   If bad points occur because the grid is moved to a grid bar that blocks all the
    electron beam, do a smaller number of measurements in a good area and then move to
    another area, repeat the measurement under the same label to accumulate statistics
    rather than a large number of measurement in a continuous series. For example, repeat
    the instruction for the measurement with 20 points at 10 different good area rather than
    do one for 200 points which likely run into a bad stretch.


-   If the above strategy fails, go to a lower magnification that will be able to cover
    more than just the grid bar from a mesh grid in the image. Do the "Scale/Rotation
    Adjustment Only" fitting at the current magnification which does not need as good a
    coverage.

NOTE: Some of the valid data points may be rejected if the tolerance is set too low in
the measurement. They are, however, important in defining the model that is aimed to correct
these deviations. The tolerance should be increased if well correlated shifts are
rejected.

## Magnification and image rotation adjustment of the model

Once a full calibration of the goniometer model is done at one magnification, a so-call
"Scale/Rotation-only" calibration is all that is needed for using the model at a different
magnification. Small number of measurements is used as well.

1.  Microscope>Place a grid into the microscope that will cross correlate well at
    low magnifications or at the mag to be calibrated
     
2.  Microscope>Go to the desired magnification.
     
    or
     
    Leginon/Presets Manager> Select the required preset for the calibration and
    send its parameter to the microscope.
     
3.  Leginon/Node Selector> select "Goniomodeling" node.
     
4.  Leginon/GonioModeling/Settings/Measurement>:
     
    -   Choose x axis
         
    -   Choose 5-20 points
         
    -   Choose a 5e-06 interval (use a larger value if a low magnification is used so
        that the shift is significant. Use a smaller value for high magnification so that
        the shift is less than half of the imaging area)
         
    -   Enter a label (Default is session name). The label separates measurements of
        the same magnification but the same one can be used for different magnifications
        and axes.
         
    -   Click OK to exit setting window.
         
5.  Leginon/GonioModeling> left click Measure tool ![](images/cam_ruler.png) to start data acquisition.
     
6.  Leginon/GonioModeling/Settings/Modeling>
     
    -   Scale and Roation Adjustment Only = yes.
         
    -   Terms = Not Relevent.
         
7.  Leginon/GonioModeling> left click Calibrate tool ![](images/play.png) to start model fitting.
     
8.  Repeat steps 3 to 7 for the y axis. You can use the same label as the one for x
    axis.
     
9.  Use Navigation node to [check the result of the calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Checking_Matrix_and_Modeled_Stage_Position_Calibration) after both axes are calibrated.

**GonModeling Mag Only Calibration Need for the Example MSI:**

  Preset                                       magnification
  -------------------------------------------- ---------------
  gr                                           120
  hl (optional if not acquiring tilted data)   5000

[< Stage Position matrix calibration](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Stage_Position_matrix_calibration) | [Scaling Stage Position Matrix >](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Stage_Position_matrix_calibration/Scaling_Stage_Position_Matrix)
