## Preparation in DM

### Check camera configuration for the orientation. Set it to Leginon orientation as determined during setup.

### Hardware dark/gain reference acquisition

Hardware dark and gain correction need to be done by DM to count electrons. You should therefore obtain dark and gain references and upload them to the hardware (HW). You can do these in [Leginon image orientation](/leginon/Leginon_Manual/Instrument_Set-up/Leginon_image_orientation) in 2.21 and above versions of DM.

* Gatan recommends frequent hardware dark reference update. This does not require the beam. You can do it everyday while getting the scope ready.

1.  Make sure the temperature of the camera is stable at where it should be cooled to.
2.  Set the Direct Detection mode to Counted (just in case of DM gui bug).
3.  Click on "Update HW Dark Reference". This takes about 4 minutes.

-   Once a while, but not very often (such as once a week or longer), all references should be retaken. This takes at least 15 minutes.

### Check exposure base time.

As a frame camera and counting, the valid exposure time and frame time are not continuous, you should check if the numbers are acceptable by DM by typing in the number and attempt to acquire an image. DM gui will automatically adjust the number to a valid one. When you later set the numbers in Leginon gui, DM internally put it to valid numbers but will not update its own gui nor Leginon's value in the database.

## Changes from DM 2.30 to 2.31

If you have used Leginon in DM 2.30 or before and are upgrading to 2.31, you would notice that more defects show up in the Leginon corrected images. This is because the new version no longer make these correction at hardward level. Just use Leginon's [Correction node](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Bright_and_Dark_reference_images#Find-A-Single-Bad-Pixel) "Add Extreme Points To Bad Pixel List" tool in its toolbar to search for those gives 0 in the bright images to do the correction in Leginon.

## Recommended dose rate and exposure time for different K2 modes

This recommendation is based on our experience.

As a general rule, the dose rate corresponds to the value used during DM gain reference acquisition. You can put down the small viewing screen once the intensity is adjusted at the beginning of DM procedure to get the values. You will notice that Linear mode calibration uses much higher beam intensity than the calibration for counted/super-resolution modes. For our Tecnai F20 at 200 kV, the former reading of exposure time by the small viewing screen is 0.25 s while the value for latter is 1.6 s. You should use similar intensity during Leginon calibration and data collection.

At 1.2 A/pixel, we use the following for final exposure that has binning of 1:

  ---------------------------- ----------------------------------- --------------------------------------- ------------------------------------------------------------------------------------------
  mode                         small viewing screen exp time (s)   detector dose rate (e/physical pixel)   acquisition exposure time for ~ 20 e/A^2 specimen dose with 1.2 A/pixel pixel size (s)
  Linear                       0.25                                64                                      0.5
  Counted/Super-resolution*   1.6                                 10                                      5.0
  ---------------------------- ----------------------------------- --------------------------------------- ------------------------------------------------------------------------------------------

*Most literature recommend at even lower dose in the range of 6-8 e/s/pixel. This is just a number we have had success with.
You can use DM's reading of dose rate while it is in counted mode and **UNBINNed** to get a reasonable estimate.

## Preset Recommendation

Because of its small size, we have a modified [Quick-start procedure](/leginon/MSI_Quick-start_for_DD_only) we use regularly at NRAMM FEI F20.
See [Pre-MSI Set-up#Preset-Design-Example-for-small-pixel-Gatan-K2-camera-alone](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Pre-MSI_Set-up#Preset-Design-Example-for-small-pixel-Gatan-K2-camera-alone) specific for K2 camera using counted/super-resolution mode.

## Where are Leginon gain references ?

See [Make movie stack with darkbrightnormgain references yourself without LeginonAppion libraries](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K2_Summit_Support/Make_DDD_movie_stack/Make_movie_stack_with_darkbrightnormgain_references_yourself_without_LeginonAppion_libraries)
