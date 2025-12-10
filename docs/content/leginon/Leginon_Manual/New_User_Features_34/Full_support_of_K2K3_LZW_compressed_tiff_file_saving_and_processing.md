Saving LZW compressed tiff file for K2/K3 dark subtracted frame movies saves disk space and speed up file transfer because of its smaller file size.
This works on 3.3 version as well but rawtransfer.py and Appion preprocessing pipeline did not work with it. With this version, everything should work seemlessly.

To turn it on, set in your dmsem.cfg [k2] section on the K2/K3 computer to

    SAVE_LZW_TIFF_FRAMES = True

For K3, you should ask Gatan for access to collect in "Dark subtracted" correction mode in order to take advantage of LZW compression. See [Gatan K3 installation and setup](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Gatan_K3_installation_and_setup) under "DM processing]]
