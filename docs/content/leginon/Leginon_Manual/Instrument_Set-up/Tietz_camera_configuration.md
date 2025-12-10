Register the Tietz ping callback function. From a command line window:

    cd C:\python25\Lib\Site-Packages\pyScope
    C:\python25\python.exe tietzping.py


Some Tietz camera dimensions are slightly larger than a standard size, for example, 2084 x 2084 instead of the standard 2048 x 2048. Some software will have trouble dealing with these dimensions. It is recommended to force the camera to the lower standard size (some multiple of 2^n). Modify the function that gets camera dimension in tietz.py, gatan.py, or tia.py depending on which camera you are using.

- Go to C:\Python25\Lib\site-packages\pyScope

- Edit tietz.py, gatan.py, or tia.py with a plain text editor

- Find the function "getCameraSize" and replace its contents to force it to return a "hard coded" size. For example:

def getCameraSize(self):
return {'x': 2048, 'y': 2048}



### For Complete Installation, go to [Calibration Application](/leginon/Leginon_Manual/Leginon_Calibrations_Application) Chapter next.

[< Leginon Image Orientation](/leginon/Leginon_Manual/Instrument_Set-up/Leginon_image_orientation) | [Good Alignments Save Time>](/leginon/Leginon_Manual/Instrument_Set-up/Good_Alignments_Save_Time)
