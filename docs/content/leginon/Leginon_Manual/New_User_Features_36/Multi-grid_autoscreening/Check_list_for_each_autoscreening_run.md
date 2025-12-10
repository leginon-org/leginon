## Decide whether you want to just acquire atlas or go through the full MSI workflow in the autoscreening

## Have an example session that has the settings to go through the workflow without interruption : No queuing at any Targeting node.

## (Grid mapping Option 1) Setup grid loading list text file

Autoscreen reads a **tab-separated** text file that contains the slot number and the session comment to setup the sequence of grid loading and screening. The grids will be screened in the order or the list.

Optionally, grids can be in different project from the example session. You can enter the project name in the third field.

An example file is attached in this wiki called grid.list

    3    best test grid      project1
    2    second best test grid        project2

## (Grid mapping Option 2) prepare a mental list to enter the order of grid position in cassette (base 1) to screen

## Check aperture positions

If you have set special aperture position for Grid node, you need to set the apertures at the position you want for high magnification imaging (Exposure node). This default will be what leginon will return to after individual node finishes its acquisition task.
