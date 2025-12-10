This feature allows selection of aperture of TFS microscopes with automated apertures. The current implementation uses AutoIt Scripting and reads the configuration from c:\Program Files (x86)\myami\fei.cfg

## Setup

### compile autoit script

See [AutoIt program and script compilation](/leginon/Leginon_Manual/New_User_Features_35/Continuous_tilt_electron_diffraction_recording/AutoIt_program_and_script_compilation)

The script is pyscope/autoit/ApertureSelection.au3
Use AutoIt suite to compile it. Either 32 or 64-bit version works as far as I know. Save the executable at the place you plan to specify in fei.cfg

### Setup pyscope fei.cfg

Copy from pyscope/fei.cfg.template these lines to fei.cfg used on your scope. In standard installation, this should be "c:\Program Files (x86)\myami\fei.cfg"

**Note: The current script assumes fei.cfg is in the above-mentioned location. If you put it somewhere else, please change the autoit script to reflect that.**

Modify these settings according to your scope.

    [aperture]
    # Disable control of auto apertures if not working or not available
    # not all versions of microscope software allows auto aperture control
    # from scripting level.
    USE_AUTO_APERTURE = False
    # AutoIt Automation
    AUTOIT_APERTURE_SELECTION_EXE_PATH = c:\Users\supervisor\Desktop\Anchi\AutoItScripts\ApertureSelection.exe
    # Does the Titan column has automated c3 aperture ?  This affects the id of the
    # gui button for AutoIt script. 
    HAS_AUTO_C3 = True
    # Individual aperture selections.  If retractable, add open at the end of the list
    # List these in the order of what appears in the TUI
    # Note: can not handle multiple apertures of the same name.
    CONDENSER_2 = 150, 100, 50, 20
    OBJECTIVE = 100, 70, 50, open
    # Optional selected area aperture control. comment or remove the line to deactivate it.
    SELECTED_AREA = 200,100, 40, 10, open

## Testing

### Testing the AutoIt executable

1.  Open TEM user interface.
2.  Retract the objective aperture.
3.  Double click Autoit executable to run.
    If this works right, it should insert the 100 um aperture.

### Testing in with python command from pyscope

    from pyscope import fei
    f=fei.Krios()  # Change this to match your instrument class

    f.getApertureSelections('objective') # This should give you the list you specified in fei.cfg
    '100', '70', '50' , 'open'

    f.getApertureSelection('objective')  # The returned value should be the current aperture position as a string
    '100'

    f.setApertureSelection('objective', '50') # This should insert the 50 um aperture

    f.retractApertureMechanism('objective') # This should retract the aperture as if you click on the Activate/Deactivate aperture button to disable it.

## Use it in Leginon

The most likely usage of this is in [TEM controller](/leginon/Leginon_Manual/Node_Descriptions/TEM_Controller) (aliased as TEM_Remote in MSI application).
