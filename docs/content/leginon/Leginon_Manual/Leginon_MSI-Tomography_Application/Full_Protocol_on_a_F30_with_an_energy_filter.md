This is edited from a complete protocol written by Lu Gan (Jensen Lab, Caltech) for users
who have not used general MSI applications. It is modified to reflect the current Leginon
version and a current and graphic-rich protocol by Jian Shi (contact him at
jianshi@caltech.edu for a copy) of the same group.

## Notes

-   Make sure EFTEM is always on


-   If presets manager has error, disable then enable "Filtered" box in
    Tecnai/TUI/GIF> menu. (TUI: Tecnai User Interface)


-   Leginon re-aligns ZLP, using a "reference" hole, after each tilt series.


-   Pause Leginon (for filling dewars, etc.): wait until tilt series is almost done,
    then press "PAUSE" in FOCUS node. Leginon will pause at start of next tilt
    series.


-   Overall scheme: Take grid atlas. At reference position, do cross-over correction,
    align presets, center objective aperture. Select and preview targets. Prepare data
    collection (gr and sq presets = skip sequence). Take dose in tomography setting. Let
    objective lens equilibrate. Align ZLP, insert objective aperture, fire away!

## Initial setup

1.  Tecnai/GIF> Tune GIF with scope column empty
2.  Tecnai/TUI/Stage> Set Z = 0.
3.  Tecnai/TUI> Turn on Intensity Zoom
4.  Tecnai> Remove objective aperture.
5.  Quit UCSF Tomo, TEM Auto-functions, Low-Dose kit.

## Start Leginon

1.  Launch Leginon
2.  Choose either to start a new session or continue an old one, then launch Multiscale
    Tomography from Applications menu.

## Presets setup with empty column

1.  Leginon/Presets Manager> Set up all the presets except align image shifts. If
    starting new session, import presets from previous session. If you want to preview
    images at high mag, make or copy a preview called "preview," which should be set to 3x3
    to 4x4 binning for greater contrast.

## Flat fielding and dose calibration

1.  Tecnai/TUI/EFTEM> Make sure that "filter" is on.
2.  Leginon/Presets Manager> tomo preset to scope.
3.  Tecnai/TUI/GIF> Go back to hole and re-align ZLP (and tune GIF if it's been ~24
    hours since last
4.  Leginon/Correction/Settings> set camera configuration to match that of the
    preset. Choose to use 2 correction channels.
5.  Leginon/Correction> acquire dark current, then acquire bright image, then
    acquire corrected image to make sure "flat-fielding" worked.
6.  Leginon/Presets manager> redo dose measurement.
7.  Leginon/Tomography> recheck dose.
8.  Leginon/Correction> repeat 4 and 5 for preset fa and hl if they are of different
    camera binning.

## Presets setup and grid atlas

1.  Insert Grid.
2.  Make sure you're near eucentric height (z = 0 is close enough for Leginon, unless
    your grid is seriously bent).
3.  You should know from experience whether the imported "gr" preset aligns reasonable
    well to higher mags so that you can reach your intended grid square, however inaccurate,
    without alignment. If this is true, you can follow 4 and 5 immediately. If not, you will
    need to manually move to a test sacrificial square at Tecnai and acquire the grid atlas
    after presets alignment.
4.  Leginon/Grid Targeting> Calculate and then publish a grid atlas using the "Grid
    Targeting" node. Do NOT pick targets in "Square" node during atlas assembly.
5.  Leginon/Square Targeting> Pick an broken square on the grid atlas and press the
    play icon, then save position on Tecnai/TUI/Stage> or in Leginon/Navigation/Stage
    Locations>. Repeat for a sacrificial square. The broken square is used to manually
    align the ZLP; the sacrificial square is used to align presets, objective lens, and to
    record test images.

## Presets alignment

Note: steps 1 and 2 are only necessary for really bad grids (you'll know).

1.  Tecnai/TUI> stage: go to the sacrificial square. Turn on wobbler
2.  Tecnai/DM> do auto eucentric height and auto focus.
3.  Leginon/Presets Manager> hl preset to scope.
4.  Tecnai/TUI> move the stage to a feature recongnizable across the presets.
5.  Leginon/Presets Manager> tomo preset to scope.
6.  Tecnai/TUI> recenter the feature accurately.
7.  Leginon/Presets Manager> Follow [image shift
    alignment procedure](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/MSI_set_up_in_more_details#Medium-mag-preset-image-and-beam-shift-refinement) in general MSI set-up using tomo preset as the
    reference.

## Objective aperture centering

1.  Leginon/Presets Manager> tomography presets to scope.
2.  Tecnai/TUI/motorized apertures> Put in objective aperture.
3.  Tecnai> Go into diffraction mode.
4.  Tecnai> Center image using diffraction shift-X&amp;Y.
5.  Tecnai/TUI/motorized apertures> Click center in motorized apertures menu.
6.  Tecnai/TUI/motorized apertures> Center objective aperture, then remove objective
    aperture.

## Target acquisition

1. Leginon/Grid Targeting> Remove objective aperture, Rename and calculate a new
grid atlas, then publish to make a new atlas, and then Reinsert objective
aperture.

*Note: You only need to take this (second) atlas if the presets - especially
square and hole - are poorly aligned, which you'll find out from the previous
alignments. If the presets were already aligned, then you can use the original grid
atlas. *

2. Leginon/Square Targeting> Click on the purple crosshair icon (reference point)
and click on a broken square, which will be used for ZLP alignment and dosage.

3. Leginon/Square Targeting> Pick squares that look good, then press Play button ![](images/play.png).

4. Leginon/Hole Targeting> While square targets are getting collected, you can
start picking targets in the hole targeting menu. Pick a bunch of holes (but not
adjacent ones), then pick a focus point for rough Z- focus. To advance to the next
square, press the play button but NOT Queue- play ![](images/send_queue_out.png).

5. Leginon/Hole Targeting> After the hole targets are all selected, insert the
objective aperture and press Queue-play.

6. Leginon/Tomography Targeting> DON'T PRESS Queue-play until ready for final
tomography acquisition.

7. Leginon/Tomography Targeting>Remember to pick a FOCUS spot for each hole and
tomography target!

Tip: you can mouse over the target and get an estimate of the average intensity in
the popup menu, which lists X,Y,Cnts. This feature lets you rapidly screen for (1)
squares with the thinnest ice and (2) the thinnest targets.

8. Leginon/Tomography Targeting> To preview target, use preview crosshair to pick
the target:

-   SET defocus in preview preset to minus 1.2 e-06 m and adjust the exposure time (in
    milliseconds) such that the dose is ~ 0.2 - 0.5 e-/Angstrum^2 - VERY
    IMPORTANT!
-   If you pick a preview target and press Play button, it will be processed
    immediately. Therefore, don't do it until all hl images are taken.
-   After you have inspected the preview image, you can come back to Tomography
    Targeting node to pick final targets on the same image. Alternatively, you can
    pick the targets first with the preview target and then remove the unwanted ones
    after previewing.

9. Leginon/Tomography> check data collection parameters: dose, tilt range, tilt
interval. See [notes on image intensity recorded through
tomography](/leginon/Leginon_Manual/Leginon_MSI-Tomography_Application/Running_the_application#Import_Notes_about_Image_Intensity_Recorded_through_Tomography_Node). (If you want --60 to 60 tilts, you should ender --61 to 61 since the
limiting algorithm is "smaller than" not "smaller than or equal to".

10. Leginon/Presets> setup data collection parameters for focus & tomography:
mag, defocus, INT (INT for focus should be greater than for tomo).

## Final checklist: Getting ready to collect

-   Leginon/Presets manager> tomo preset to scope.


-   Tecnai/TUI/Stage> Go to reference point.


-   Leginon/Tomography node> re-check dose and re-center beam.


-   Leginon/Exposure targeting> press queue-play. Atlas does NOT need to be
    reloaded.

[< Running the application](/leginon/Leginon_Manual/Leginon_MSI-Tomography_Application/Running_the_application) | [Using "MSI-SimuTomography" Application for debugging >](/leginon/Leginon_Manual/Leginon_MSI-Tomography_Application/Using_MSI-SimuTomography_Application_for_debugging)
