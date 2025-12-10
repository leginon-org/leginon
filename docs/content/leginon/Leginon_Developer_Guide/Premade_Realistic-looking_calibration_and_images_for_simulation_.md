A set of simTEM and simCameras were made to simulate the set up of energy-filtered Krios coupled with Ceta and Gatan K2 camera. This was made for https://github.com/nysbc/leginon-tutorial

Here is what you can do to add it to your development sandbox.

## Create a folder to hold the simulated images Download the folder simimages and its content from https://emg.nysbc.org/redmine/projects/leginon/repository/revisions/myami-tutorial/show/tutorial_data Make sure the directory is writable by the user starting the leginon.

## Modify your Instruments.cfg to include these instruments

    [Sim TEM]
    class: simtem.SimTEM300
    cs: 2.7e-3
    simpar: /abosolute_path_to_your/simimages

    [Sim Cam]
    class: simccdcamera2.SimCCDCamera
    zplane: 40
    height: 4096
    width: 4096
    simpar: /abosolute_path_to_your/simimages

    [Sim K2]
    class: simccdcamera2.SimK2CountingCamera
    zplane: 70
    width: 3710
    height: 3838
    simpar: /abosolute_path_to_your/simimages

**These two steps makes the camera look for the images in your simimages directory according to the simTEM magnification and binning**

## Import instruments, calibrations and presets

### 1. Go to your myami clone under dbschema/tools to access these python scripts:

    import_leginon_instruments.py
    import_leginon_cal.py
    import_leginon_preset.py

### 2. Download these files attached to this wiki page to current directory (Find them at the bottom of this page by opening the tab "Files")

    instruments.json
    mags_leginon-docker+SimTEM300.json
    preset_SimTEM300+leginon-docker+SimCCDCamera.json
    preset_SimTEM300+leginon-docker+SimK2CountingCamera.json
    cal_SimTEM300+leginon-docker+SimCCDCamera.json
    cal_SimTEM300+leginon-docker+SimK2CountingCamera.json

### 3. Modify the hostname in the json files

These files are exported from a computer with hostname "leginon-docker". Do import these to your host, you need to change that part of the filename to your hostname. If you are not sure, proceed to the next step and it will give you an error and a hint on what name you should change it to.

### 4. Performing the import

Let's say that your sinedon.cfg specify the host to be localhost, and your host mapping has been set up to use leginon-docker as the hostname within leginon operation in pyami.cfg, then you should run these in order

    ./import_leginon_instruments.py localhost
    ./import_leginon_presets.py localhost preset_SimTEM300+leginon-docker+SimCCDCamera.json
    ./import_leginon_presets.py localhost preset_SimTEM300+leginon-docker+SimK2CountingCamera.json
    ./import_leginon_cal.py localhost cal_SimTEM300+leginon-docker+SimCCDCamera.json
    ./import_leginon_cal.py localhost cal_SimTEM300+leginon-docker+SimK2CountingCamera.json

## For future reset database to this state

1. Use phpMyadmin to drop all tables in projectdb and leginondb.

2. Download the two sql files attached to this wiki

leginondb.sql
projectdb.sql

3. Run the following mysql commands to populate the database that gives you the end result of a usable simulation installation.

    mysql -u your_mysql_user -p projectdb < projectdb.sql
    mysql -u your_mysql_user -p leginondb < leginondb.sql
