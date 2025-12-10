On microscope PC, with myami-ed git branch of installation

## Edit Instruments.cfg used by leginon. Typically in C:\Program Files\myami

Add diffraction instrument as another tem. The class name is your normal instrument, for example, Glacios, with Diffr prefix. Therefore, add

    [difftem]
    class: fei.DiffrGlacios
    cs: 2.7e-3

## Add items required for the instrument and workflow to your fei.cfg. This should have exists with instruments.cfg

### Set pre-diffraction normalization magnification

Enter the index of the SA range magnification you want Leginon to normalize at before it switches to diffraction mode preset.
For example 37 is 150kx on Glacios where typical fa preset is at for typical Ceta-D configuration.

    PRE_DIFFRACTION_SA_MAGNIFICATION_INDEX = 37

Decide where you will put all the AutoIt script executable. For example: **C:\Program Files\AutoIt3**
Copy the items from your pyscope/fei.cfg.template to make sure you have the right syntax.

### Under [camera] module, add

    AUTOIT_TUI_ACQUIRE_EXE_PATH = C:\Program Files\Autoit3\TuiAcquire.exe
    AUTOIT_TIA_EXPORT_SERIES_EXE_PATH = C:\Program Files\Autoit3\TiaExportSeries.exe
    AUTOIT_TIA_EXPORTED_DATA_DIR = C:\Users\supervisor\Documents\FEI\TIA\Exported Data

### Add [beamstop] module and items needed at the end of some module.

    [beamstop]
    AUTOIT_IN_EXE_PATH =  C:\Program Files\Autoit3\BeamstopIn.exe
    AUTOIT_OUT_EXE_PATH = C:\Program Files\Autoit3\BeamstopOut.exe
