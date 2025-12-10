## Material

1.  Gold-shadowed diffraction grating replica for TEM calibration such as Ted Pella's prodoct !#606 or !#607.

-   If such a grid with Gold coating is not available, other material that produces known spacing diffraction in sub-nm range can be used. However, the gold <111> spacing 0.236e-9 meters used in **get_beamtilt_scale.py** need to be replaced.

## Procedures

-   Do this calibration at one of the high tension values you plan to use Leginon at.

1.  Insert the specimen holder with the grid in the microscope
2.  From microscope-controlling PC, navigate to the installed myami/pyscope directory. Most likely **C:\Python27\Lib\site-packages\pyscope**
3.  Find the python file **get_beamtilt_scale.py**
4.  If non-gold grid is used, modify the spacing value with a plain-text editor at the line
        gold_diffraction = wavelength/0.236e-9
5.  Start the script by double-left click on it.
6.  Follow the instruction to determine the scale factor.
7.  At the end of the script, the beam should be tilted back to the center and the script window closed. If the window does not close, force it to close should not cause any problem.
