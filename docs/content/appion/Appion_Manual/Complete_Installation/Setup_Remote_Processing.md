The web interface for Appion allows one to directly login to a computer and process Appion jobs. But this requires a job submission system to be installed.

## Types of clusters:

-   Local cluster a.k.a. processing host --- This is a cluster that has all of the data directories mounted locally and all processing software installed. This configuration is used for all jobs except Refine Reconstruction jobs.
-   Refine Reconstruction cluster a.k.a. cluster --- This is a cluster that is used for Refine Reconstruction jobs. It therefore only needs a limited selection of software. It is possible that the data is not accessible and will need to be transfered for processing.

**Note:** The Local Cluster and Refine Reconstruction Cluster can be the same machine, but you will still need to perform all the setup instructions below for each type of cluster.

## Local Cluster Appion processing setup

The following applies to both the web-server computer (setup earlier) and a job submission system on a local cluster. The job submission system usually consists of a head node (main computer) for receiving and scheduling jobs and individual processing nodes (slave computers) for running jobs. All of these system CAN exist on an single computer.

1.  [Setup job submission server](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing/Setup_job_submission_server)
2.  [Install SSH module for PHP](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing/Install_SSH_module_for_PHP)
3.  [Configure web server to submit job to local cluster](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing/Configure_web_server_to_submit_job_to_local_cluster)
4.  [Testing job submission](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing/Testing_job_submission)
5.  [Potential job submission problems](/appion/Potential_job_submission_problems)

## Appion Refinement Reconstruction Processing through ssh setup

1.  [Edit the default_cluster.php file](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing/Configure_web_server_to_submit_jobs) (Appion version 2.1 and earlier only)

[< Additional Database Server Setup After Web Server Installation](/appion/Appion_Manual/Complete_Installation/Additional_Database_Server_Setup_after_Web_Server_Installation) | [Create a Test Project >](/appion/Appion_Manual/Complete_Installation/Create_a_Test_Project)
