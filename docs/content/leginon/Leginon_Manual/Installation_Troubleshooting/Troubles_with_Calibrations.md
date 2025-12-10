-   [Available magnification from pixel size calibration is
    different from that said on the scope](/leginon/Leginon_Manual/Installation_Troubleshooting/Troubles_with_Calibrations#h2.-Magnification-list-not-consistent-with-that-at-the-microscope)


-   [Stage does not move after a pyScope update on the
    computer controlling the microscope](/leginon/Leginon_Manual/Installation_Troubleshooting/Test_run_operation_problems#h2. Leginon-fails-to-move-the-goniometer-after-a-new-installation-or-update-of-pyScope)

## Magnification list not consistent with that at the microscope

Commonly Why: Instrument was not selected correctly when Leginon is installed

Solution: Check the parameters of the named instrument in Administration Tool

## Export calibrations as json file and send to development team

Once you have a session that successfully use the settings that you would like to distribute

    cd /your_myami/dbschema/tools
    python ./export_leginon_settings.py source_database_hostname source_camera_hosthame camera_name

For example,

    python ./export_leginon_settings.py my_leginon_dbhost krios-k2 GatanK2Counting

[< Troubles with Imaging](/leginon/Leginon_Manual/Installation_Troubleshooting/Troubles_with_Imaging)
