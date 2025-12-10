We have two major folders in the appion folder:

-   appionlib: contains libraries, a collection of common functions that are needed by more than one python program, e.g., ssnrResolution, averageStack, and lowPassFilter.
-   bin: contains the programs that take command line input, e.g., makestack2.py, templateCorrelator.py, maxlikeAlignment.py

Other useful directories:

-   pyami: a collection of common functions to both appion and leginon, save MRC file, save SPIDER file, etc.

## Most important python files:

### Database mapping file

-   source:trunk/appion/appionlib/appiondata.py: describes how the database is put together, if you need to add a new column go here

> see also source:trunk/leginon/leginondata.py and source:trunk/leginon/projectdata.py

### Appion Script hierarchy

#### basicScript

-   source:trunk/appion/appionlib/basicScript.py
-   contains all the base functions: `setupParserOptions`, `checkConflicts`, `start`
-   used only for basic scripts outside of the pipeline, e.g., *source:trunk/appion/bin/makeSnapshots.py*, *source:trunk/appion/bin/ApDogPicker.py*
-   write a log file
-   running statistics

#### appionScript

-   source:trunk/appion/appionlib/appionScript.py
-   Most common function class used 68 programs in appion, e.g., *source:trunk/appion/bin/uploadStack.py*, *source:trunk/appion/bin/subStack.py*, and *source:trunk/appion/bin/maxlikeAlignment.py*
-   based on basicScript, but
    -   adds database connection to log information about run
    -   adds default commandline options, such as `--runname`, `--commit/--no-commit`, `--rundir`, `--projectid`, and `--description`

#### appionLoop2

-   source:trunk/appion/appionlib/appionLoop2.py
-   based on appionScript but loops over all images in a session
    -   adds default commandline options, such as `--sessionname`, `--preset`, `--limit`, `--continue`, `--shuffle`, and `--no-rejects`
    -   requires `--runname` to be defined
-   ideal when the same function needs to be run on all images, e.g. ACE
-   used in 15 programs, e.g., *source:trunk/appion/bin/pyace.py*, *source:trunk/appion/bin/pyace2.py*, and *source:trunk/appion/bin/makestack2.py*

#### filterLoop

-   source:trunk/appion/appionlib/filterLoop.py
-   based on appionLoop2 but add low pass, high pass, plane regression and other filters
-   used in only two functions, manualmask.py and *source:trunk/appion/bin/jpgmaker.py* (a program to make jpeg cache images of the session)

#### particleLoop2

-   source:trunk/appion/appionlib/particleLoop2.py
-   based on filterLoop but adds particle picking capabilies
    -   creates the jpeg with the circles
    -   uploads particle picks to the database
-   used in 7 different particle pickers, e.g., *source:trunk/appion/bin/manualpicker.py*, *source:trunk/appion/bin/tiltAutoAligner.py* and *source:trunk/appion/bin/templateCorrelator.py*
