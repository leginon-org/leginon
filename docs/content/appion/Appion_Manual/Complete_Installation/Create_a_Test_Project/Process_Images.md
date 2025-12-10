#### Testing simple appion processing job submission

Upload template is a good example to try:

1.  Create a small mrc image as your template to be uploaded.
    You may instead download a [sample GroEL template](http://emg.nysbc.org/redmine/attachments/download/491/align23-average0-10may19r30.mrc)
     
2.  Log into the Appion processing page.
     
3.  Select Upload template in Import tools in the Appion processing menu of an existing session.
     
4.  Type in the needed information.
    If using the sample GroEl template, the Diameter is 180 and the pixel size is 3.26.
     
5.  When you finish filling in the form you may chose between **Just show command** and **Upload template**.
    If you chose **Just show command**, you will copy and past the command into a Terminal.
    You may also choose your processing host and run the job by clicking "Upload Template".
     
6.  For simple process such as this, the webpage will take a little while to refresh until the job is completed.
     
7.  If you get the message "Template is uploaded", the process is successful and if you refresh the page you will find the template in the available list.

#### Testing PBS-required appion processing job submission

Particle selection such as DogPicker is a good example to try:

1.  Click on DoG Picking under Particle Selection menu
2.  Enter the required parameters.
    If using sample GroEl, all you need to enter is the particle diameter of 180.
3.  When you finish filling a form for an appion processing, choose your processing host and run the job. Pages for monitoring the job become available after the job is queued and subsequently begins running. If the status appears as "Running or Queued" at first, the setup is likely correct.
4.  After a while, the process will be completed and the status becomes "Done" when you click to have the Status updated on the page.
5.  If you receive the message: *ERROR in job submission. Check the cluster* Torque may not be set up correctly.
