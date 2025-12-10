There are two options:
1. Move to the next patch when the phase shift develop passes a fixed phase shift.
2. Move to the next patch with fixed the dose accumulation or time regardless of phase shift.

Our recommendation is to try out a full workflow of a good standard specimen to find out what works for you.

Our experience is to use option 2. The particular phase plate we tested on did not ever got phase shift of a very large number such as 160 degrees (the maximum was around 130 degrees in this case), but we found that 3D classification of the particles prefer particles in the middle exposures even though the phase shifts were in 30-90 degrees range (an estimation since this was a zero-defocus data collection), or 3rd to 15th exposure. For reasons unknown, later images were blurred and missing details in a similar manner to those shown as high phase shift image in https://elifesciences.org/content/6/e23006

To give a starting value, I give here the dose information in this particular experiment on 20S proteasome:

  ----------------------------------------- -----------------------------------------
  Krios-K2Camera pixel size                 1.1 Å/pixel
  Illumination diameter                     1.43 um on specimen
  Exposure dose rate on camera              8 electrons/pixel after the phase plate
  Attenuation of beam by the phase plate    10 %
  Exposure time                             7.0 seconds
  Total specimen exposure                   44 e/Å^2
  Charge time after moving to a new patch   30 seconds
  ----------------------------------------- -----------------------------------------
