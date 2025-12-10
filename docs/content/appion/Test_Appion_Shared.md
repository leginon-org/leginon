## Test Appion

-   If appion was installed using `setup.py` you are ready to test out appion.


-   Run the following script to test import of Appion libraries and binaries:
        cd myami/appion/
        ./check.sh

    
    **NOTE**
    You can ignore EMAN, MATLAB, and UCSF Chimera errors at this point.
     
    What about: raise LeginonConfigError('set IMAGE_PATH in leginonconfig.py')
    leginon.leginonconfig.LeginonConfigError: set IMAGE_PATH in leginonconfig.py

>You need to [edit leginon.cfg](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Configure_leginoncfg).

-   Run the following script to test the installation of 3rd party processing packages:
        cd myami/appion/test
        python check3rdPartyPackages.py
