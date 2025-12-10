[imaging the phase plate slot at low magnification to check for contamination and recovery of the irradiated spots](/leginon/imaging_the_phase_plate_slot_at_low_magnification_to_check_for_contamination_and_recovery_of_the_irradiated_spots)

On FEI Volta phase plate slot there are 76 patches to be used. Each can be accessed by "Next" button in TEM user interface (TUI). Once Leginon is set up with AutoIt to click this button, it is possible to go through all patches and record diagnosis images which is the purpose of this node.

We do this once after it is installed. It gives us a feel for good and bad area. The phase plate moving mechanism is not accurate enough to return to the exact position globally but the move between patches is consistent.

Grid used: Grating Replica

1.  Remove Phase Plate, align the scope to eucentric focus, make sure the grid is at the eucentric height, and adjust imaging condition to give ~ 1 Å pixel. Exposure time should be enough to give clear Thon ring pass 4 Å resolution after direct detector frame alignment. Save this condition as the preset to be enterred in "Check PP Patches" node settings. The defocus should be --0.5 um and free of objective astigmatism. It should also use full resolution and size of the camera.


1.  Insert Phase Plate, wait for it to settle.


1.  Adjust to on-plane condition for the phase plate with the same preset as above.


1.  In "Calibration Application", select "Check PP Patches" node and open settings to add the preset to its preset order. Also increase "Wait time before acquiring image" to at least 5 second.


1.  Confirm on TUI under Aperture tag that the "Next" button is visible for **AutoIt** to click.


1.  Click on "Simulate Target" tool in "Check PP Patches" node. A dialogue should appear to allow you to enter phase plate identity, the current patch position etc. Once "OK" is clicked in the dialog, the acquisition will start.

The result images and its phase plate identity is saved. You can view them in the myamiweb image viewers.

## Estimate ctf

You should align the frames of these images if it is from a direct detector. CTF estimation resolution of the aligned images should then give you an idea if a patch is usable for high resolution. For example, if I aim to use phase plate for sub 3 Å structure, the CTF estimation resolution should go beyond that and without distortion.

[Generate Phase Plate Condition Map](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Check_Phase_Plate_Patches/Generate_Phase_Plate_Condition_Map)
