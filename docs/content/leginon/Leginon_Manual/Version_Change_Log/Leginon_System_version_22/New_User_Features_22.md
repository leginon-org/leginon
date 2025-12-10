## [Direct Electron DE-12 direct detection device support](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer/Direct_Electron_DE-12_direct_detection_device_support)

* Acquire summed frame image thru Leginon
* Trigger raw frame saving
* Transfer raw frame images off solide-state drive of DE-12 during data collection to a network drive.
* Compile corrected movie stack thru Appion

## Grid Selection and Labeling for Screening

* "Choose Grid" allows user to enter a short name for the grid and prepend the name with the project id similar to that used in grid-loading robot to identify the current grid within the session.

* An example of using this is in the new "Manual (2.2)" application.

## Saving Reference Images in special sessions

* The reference images used to be saved in the same session as the experiment data. They are sometimes accidentally removed when the whole experiment is archived. To avoid that, reference images are now saved in special sessions.


reference images are now saved automatically to special sessions name containing "_ref" in the same base leginon directory defined in leginon.cfg as image_path. Every 90 days, a new session is automatically created so that the very old ones can be archived away eventually. Also, if a linux user has no write permission to the existing reference session, a new one will be created so that there is no delay in data collection. All users still need read-access to these directories in order to use them.

For example, on Jun 1st, 2012, a user starts the first time a Leginon session. His/her leginon.cfg has these lines:

[Images]
path: /your_disk/leginon


Therefore, Leginon creates a reference session with this path

/your_disk/leginon/12jun01_ref_a



[< PyScope Changes](/leginon/PyScope_Changes_22)
