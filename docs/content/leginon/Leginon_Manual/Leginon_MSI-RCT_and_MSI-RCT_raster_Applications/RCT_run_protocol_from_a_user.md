## Setup

### Days before

-   Pump down stage
-   Cryo-cycle for 4 hours (240 min)
-   Prepare grids

### Scope alignments

2.2.1 no sample

gun shift/tilt
condenser aperture
condenser stig.
check if cold trap is in
adjust eye pieces

2.2.2 with sample

z-height
focus both M and SA modes
objective stig.
objective aperture at hi mag, use focus to shrink beam, not intensity
at zero defocus
beam tilt pivot points X,Y
rotation center

### Presets and Magnifications

  -------- ------------ --------------- ---------------------- -----------------------------------
  preset   mag          camera config   defocus                notes
  gr       120X         512x8           0                      do not cycle through
  sq       1700X        1024x4          --3.0e-4               for square_centering
  cs       1700X        1024x4          --3.0e-4               for rct_targeting, copy of sq
  hl       5000X        512x8           --5.0e-5               image shift alignment and z-focus
  en       50kX-100kX   4096x1          --1.5e-6 to --3.5e-6   
  fa       50kX-100kX   512x4           --1.5e-6               beam focus and drift checks
  -------- ------------ --------------- ---------------------- -----------------------------------

### Leginon

2.4.1 pre-Altas

beam shift/intensity for each preset
align image shifts btw presets
optional: fine tune rotation center in Leginon, available in any focus node using the fa preset
on rare occasions: check optical axis using Leginon tool, this is only required if the square is shifting alot when you tilt the stage

2.4.2 post-Atlas

RCT node settings optimization
make sure the number of features is between 700 and 1500
take a picture both with and without the grid bar
take a picture both untilted and tilted
calibrate dose
RCT node setup
re-align presets
re-center objective aperture

## Running Leginon RCT

Start a square:
Square Targeting (if you have an atlas)
Go to "Square Targeting"
Hit the reload button
Select a new square with the green cross
Click the play |> button
Simulate Square (if you do NOT have an atlas)
Go to "Square"
Hit the simulate target button
Square centering
When Leginon is finished, a question mark will appear next to the "Square Centering" node
Click on the "Square Centering" node
Select one z-focus position (blue cross) and one imaging position (green position) close to the center of the square
Click the play |> button
RCT Targeting
When Leginon is finished setting the z-height, a question mark will appear next to the "RCT Targeting" node
Click on the "RCT Targeting" node
Now you select all the holes to image (not too close to the edge) and a single focus position
Optional: obtain a picture of the tilted square
Click on the "Navigation" node
Open up VNC viewer of the tecnai
In the VNC window, set the tilt angle to the desire angle
In the "Navigation" node, collect an image by clicking on the acquire button (camera logo) at the top
Important, in the VNC window, return the tilt angle to zero degrees, otherwise all your images will fail
Now select you targets in the "RCT Targeting" node and view the tilted image in the "Navigation" node. Jump back and forth between the two nodes until you select all holes present in both images.
When finished, hit the play |> button
Focusing
If manual focusing is enabled, wait for the manual focus window to pop up
focus the microscope, reset the defocus, and click the red stop button.
Watch your images in the "RCT" node

## Nitrogen fill

Since RCT only focuses once per square, when you fill the dewar, you must refocus to account for changes in the z-height and focus during refill and there is no check for drift calm down so you must manually wait for drift to subside.

Steps in Nitrogen fill:

Pause RCT node
Wait until Leginon is paused
Fill holder and cold trap dewars
Turn off lights
Check if objective aperture is inserted
RESET TIMER
Focus
simulate z-focus
send hole preset to scope
navigate to good focus spot in navigator
simulate focus in the focus node
repeat focus until drift subsides
If there is an empty hole: you can measure dose or collect bright fields
Declare drift
Hit play button on RCT node
Check images to make sure they are good
Uncheck user verification of targets

This page was last modified 16:45, 16 July 2010.

[< RCT application calibration](/leginon/Leginon_Manual/Leginon_MSI-RCT_and_MSI-RCT_raster_Applications/RCT_calibration)
