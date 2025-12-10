## Testing

### Testing php-ssh2 installation

Check your info.php as you did with mrctool installation. Corrected installed extension should show up in the output of info.php. Reference http://emg.nysbc.org/documentation/leginon/bk02ch04s07.php under the section **Check php information** and **Alternative approach if mrc module does not show up in info.php output**.

### Testing ssh log in

Use the top right form on the processing page to log in as if doing an ssh session. The page will acknowledge that you have been logged in if the setup is correct. You will be able to edit description of a run and to hide failed runs when logged in. The option for submitting the job appears at the bottom of the processing form whenever available.

### Testing simple appion processing job submission

Upload template is a good example to try:

1.  Create a small mrc image as your template to be uploaded.
2.  Select Upload template in Import tools in the appionweb processing menu of an existing session.
3.  Type in the needed information.
4.  When you finish filling the form, instead of clicking on "Just show command", choose your processing host and run the job by clicking "Upload Template".
5.  For simple process such as this, the webpage will take a little while to refresh until the job is completed.
6.  If you get the message "Template is uploaded", the process is successful and if you refresh the page you will find the template in the available list.

### Testing PBS-required appion processing job submission

Particle selection such as DogPicker is a good example to try:

1.  Click on DoG Picking under Particle Selection menu
2.  Enter the required parameters
3.  When you finish filling a form for an appion processing, choose your processing host and run the job. Pages for monitoring the job become available after the job is queued and subsequently begins running. If the status appears as "Running or Queued" at first, the setup is likely correct.
4.  After a while, the process will be completed and the status becomes "Done" when you click to have the Status updated on the page.

### Check *your_cluster.php* setup

For reconstructions involving iterations of different parameters such as EMAN reconstruction by refinement, the *your_cluster.php* is used to generate the script. Examine the script created on the web form and modify *your_cluster.php* You can copy the script to your cluster and test run/modify it until it is correct.

_

[< Configure web server to submit job to local cluster](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing/Configure_web_server_to_submit_job_to_local_cluster) | [Potential job submission problems >](/appion/Potential_job_submission_problems)
