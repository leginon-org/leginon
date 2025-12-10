AutoCTF distributed by Thermo Fisher with phase plate installation and EPU is well suited for this purpose. You should first become familiar with its operation before starting this calibration.

-   TIP: AutoCTF will set the camera it uses based on the last image acquisition. You can use K2 behind GIF if you acquire a K2 image in leginon or TIA **BEFORE** opening AutoCTF. If you have too much idle time and K2 retracted by itself, AutoCtf will default to use pre-GIF camera, though.

The settings and calibration procedure using AutoCTF are based on Wim Hagen's protocol. So do the idea of correcting for astigmatism that resulted in https://www.ebi.ac.uk/pdbe/emdb/empiar/entry/10200/

## AutoCTF settings change from settings file.

-   Search for the configuration file autoctf.autoctfsetting.
-   Edit this xml file with a text editor while AutoCTF is **NOT** running.
    -   Change NAzimuthalAngles from 4 to 8 for better accuracy.

## AutoCTF settings from gui

-   10 mrad beam tilt without objective aperture
-   Use high but short exposure for best result. We use twice the exposure dose rate than normal by changing spot size. For example, full readout area and 2x binning from k2 counting mode and 2 s exposure.

## Recommended routine for correcting coma, astigmatism and defocus with AutoCTF

Astigamatism and coma are best corrected separately. Here, the procedure assumes that we aim for --2.5 um defocus.

1. Run AutoStigmate and Auto-Defocus until it is at --2.5 um and free of astigmatism.
2. Run Auto-coma until it converges
3. Redo 1.
