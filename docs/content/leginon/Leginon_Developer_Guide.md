## Overview of the code repository

Over the years, Leginon has grown and divided. With the addition of the Appion processing pipeline, several components that were once subsystems of Leginon were broken out to be used as a common tool set for both Leginon and Appion. The top level master package that now contains the entire software suite developed at AMI is called *myami*. Inside of myami you will find leginon, appion and all of these common packages. Here is a brief description of the contents of the AMI software repository:

-   **myami** - the complete suite of software
    -   **appion** - the processing pipeline
    -   **comarray** - Python extension to retrieve COM SafeArrays into NumPy arrays (deprecated, see [Installing comtypes](/leginon/Installing_comtypes) instead)
    -   **dbschema** - If you are running your myami system out of a sandbox and frequently pulling changes from the repository, then your database schema is generally kept up to date automaticall. But most production installations update only between major revisions. The dbschema directory summarizes all of the database schema updates between revisions, which can be applied in sequence when doing a major jump in revisions.
    -   **imageviewer** - this is a newer image viewer widget for wx meant to replace the old ImageViewer widget in the Leginon GUI. So far only the tomography node uses it.
    -   **install** - adds automation to the installation process
    -   **leginon** - microscope control and automation
    -   **modules** - python extensions that must be compiled
        -   **libcv** - key point detection and matching
        -   **numextension** - misc image functions. More info here: [numextension](/leginon/Leginon_Developer_Guide/Numextension)
        -   **radermacher** - functions for tilt picker, see [TiltPicker installation](/tiltpicker/TiltPicker_Installation)
    -   **myamiweb** - all of the php web server stuff for the the web viewer, appion pipeline, etc.
    -   **programs** -
    -   **pyami** - miscellaneous pure python modules that are usefull for both leginon and appion
    -   **pyscope** - Python interface to several TEMs and cameras
    -   **redux** - a Python replacement for php_mrc, but also generally useful on its own for image conversions, FFTs, resizing, etc.
    -   **sinedon** - object relational mapping module, so you can use python objects to populate your MySQL database

## Sinedon usage

Sinedon is the ORM used in leginon. The data objects are dictionary-like so that the mapped field name with its values of the table are key-value pairs in this data objects.
leginondata.py in leginon packages is where the data classes are defined.

For example, the following python commands creates an instance of SessionData data object and prints the referenced names of the fields for this database table.

    from leginon import leginondata
    print(leginondata.SessionData().keys())

You can query database with this. results=2 makes it returns the a queryset contains the most recent 2 row of this table, sorted in descending order by their primary keys (accessed through dbid attribute, if you want to know).

    sessions = leginondata.SessionData().query(results=2)
    newest_session = sessions[0]
    print('primary key for the newest session=', newest_session.dbid)

You can also find out any field value by the key. For example, session name:

    print('name=', newest_session['name'])

Somtimes the a data object reference another data object. In SessionData, user field is a referenced UserData. If you want to know the lastname of the user who created this session. You can do

    print(newest_session['user']['lastname'])


Sinedon is lazy-loaded, meaning that it does not perform the query that retrieves this referenced object until you access it. This ensures performance.

If your script needs to save a new SessionData data row with a new session name, image path, and frame path, but keep using the same user, you can follow this:

    s= leginondata.SessionData(initializer=newest_session)
    s['name']='new_name'
    s['image path']='/data/leginon/new_name/rawdata'
    s['frame path']='/data/frames/new_name/rawdata'
    s.insert()

The insert method in sinedon data objects is recursive but default to not forced. It will check if the content is unique. Therefore if you repeat the last line twice, you only get one row of new data in SessionData and no new UserData is added.

If you are doing insert for history tracking (Most SettingsData insertion are this type of insert), then you can add force=True to your insert statement. See settingsfun.py for an example.

Please read leginon/leginondata.py to see all the data classes defined for leginon package.

## Brief description of the design of Leginon

Leginon is a flexible framework for automating your TEM data collection. The flexibility comes from the fact that key tasks are coded into *nodes*, which can then be dynamically assembled into an event driven *application*. Each node performs a task, and generates events to trigger other nodes to perform their tasks. In addition to passing events between each other, nodes may also share the data they produce. For example, an Acquisition node may acquire an image from the instrument, then generate an event to notify another node to process that image. Another area of flexibility is in how applications may distribute the nodes among several hosts on the network. Processing could be optimized depending on which nodes are on the instrument host versus which ones are on a more powerful host elsewhere.

## Access pyscope instrument get/set method from Node class instance

Pyscope TEM and CCDCamera and their subclasses defines the instrument control and are available in most Leginon Node classes through self.instrument. Only one TEM and CCDCamera class is active at a time and accessed through self.instrument.tem and self.instrument.ccdcamera. The get/set methods in the instrument class can be used a property as well as calling the method.

For example, to get stage position of the active TEM class in a node of Leginon, we can do either of these inside a function of the class

      pos = self.instrument.tem.StagePosition

      pos = self.instrument.tem.getStagePosition()

to set stage position which needs a dictionary input with valid keys (x,y,z,a), we could do either

      self.instrument.tem.StagePosition = {'x':0.0}

      self.instrument.tem.setStagePosition({'x':0.0})

See navigator.py Navigator class for some examples.

## Adding new features and functionality to Leginon

The two most common ways you will be adding a new idea to Leginon:

-   A small addition to an existing node. For example, a new parameter to auto focusing would require a new entry box in the GUI and a modification to some underlying function call.
-   A completely new feature that is different enough to belong in its own node. For example, a new target finding technique. See [Creating a new Leginon node](/leginon/Creating_a_new_Leginon_node)

## Simulation: when you do not have access to a real TEM and/or camera.

-   You still need the overall infrastructure in place: myami installed, database created, etc., but at least this can still be an option for a stand-alone laptop that is not even connected to the network.
-   configure your instruments.cfg file with SimTEM and SimCCDCamera instruments. These are the defaults in instruments.cfg.template.
-   Start Leginon and do not connect to any external clients during the session setup wizard
-   Go through calibrations as if they are real microscope and camera. You can however, [fake the values](/leginon/Leginon_Developer_Guide/Fake_calibrations_for_Leginon_simulator).
-   Most functionality can be tested, however your images will be simulated and the more advanced target finders may not work so well.
-   [Premade Realistic-looking calibration and images for simulation](/leginon/Leginon_Developer_Guide/Premade_Realistic-looking_calibration_and_images_for_simulation_)

## Useful diagonosis scripts

-   [testing pyscope instrument](/leginon/Testing_pyscope_instrument) functions without Leginon.
-   [setup simulator with VMware](/leginon/Leginon_Developer_Guide/Setup_simulator_with_VMware)
