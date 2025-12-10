The Basic usage of JEM scopes with Leginon is complete even though not the most efficient due to a few hardware issue that we do not yet over come. A few functions does not work as described below.

## What does not work:

-   PiezoStage is not used yet.
-   Automatic Omega energy filter slit centering and filter lens (FL) adjustment.
-   Moterized aperture is not yet used for centering.

## "image beam shift" on JEOL scopes is equivalent to "image shift" applied by the users on FEI instrument

Such movement should move feature in the view without induced movement of the beam.

## Stage Tilt (known as alpha, or TX) accuracy may be limited to 0.2-0.3 degree.

Because there is no feedback at such high precision, a requested tilt of 1 degree can be off by 0.3 degrees. As a result, the calculated eucentric height from stage tilt within autofocus procedure will be wrong. To avoid this problem, It may be necessary to use larger stage tilt autofocus focus sequence. The notes in [Adding a new focus sequence to a focus node](/leginon/Leginon_Manual/Multi-Scale_Imaging_Applications_in_General/Adding_a_new_focus_sequence_to_a_focus_node) is useful for designing this. At NYSBC, the minimal tilt used in stage tilt autofocusing is 2 degrees, and often 4 degrees when possible.

## Special MSI Application designed to avoid using LOWMAG sq preset in the target adjustment

Some model has such a slower relax time in image shift in LOWMAG range that it is necessary not to access it in target adjustment. An additional targeting/imaging step is added in this application so that queued up exposure targets will not be adjusted using sq preset.

The xml file for the application we have used with K2 Summit camera can be found in

    /your_myami/leginon/applications/J-MSI-T2.xml

You can import the application using [Applications](/leginon/Leginon_Manual/Administration_Tools/Applications) import tool in myamiweb. The settings needed for the application can be imported into Leginon using python file /your_myami/dbschema/import_leginon_settings.py with

    cd /your_myami/dbschema
    python ./import_leginon_settings.py J-MSI-T2


It will prompt you for location of the settings json file if it can not find it automatically. The location of the file is /your_myami/leginon/applications/J-MSI-T2.json

The work flow includes an extra "Hole Centering" target selection and "Better Hole" acquisition node with "hc" preset at the same preset parameters as "hl". As a result, later target adjustment on image acquired through this new node does not need to go to "sq" preset.

## Operation related to energy filter

While we can insert and remove the energy filter slit, MSI operation that acquires images at lower magnification frequently causes instability of the beam path within the energy filter. Common problem observed is that the contrast of "hl" image acquired become reversed due to misalignment of slit. The only successful example so far used the following strategy:

1.  Set up all presets without inserting energy filter slit.
2.  Activate queuing in "Exposure Targeting" node.
3.  Queue up all targets.
4.  Activate "energy filter" option in en/fa/fc/hl presets, i.e., all presets that will take images once the queue in "Exposure Targeting" is submit to process.
5.  Align the energy filter and image and beam shift of en/fa/fc/hl presets until stable.
6.  Click "Submit Queued Targets" in "Exposure Targeting" to start final exposure data collection.
