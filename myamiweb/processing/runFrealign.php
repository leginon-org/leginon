<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an Eman Job for submission to a cluster
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";

$selectedcluster=$CLUSTER_CONFIGS[0];
if ($_POST['cluster']) {
	$selectedcluster=$_POST['cluster'];
}
$selectedcluster=strtolower($selectedcluster);
@include_once $selectedcluster.".php";

/*
******************************************
******************************************
******************************************
*/

if ($_POST['submitjob'])
	submitJob(); // submit job
elseif ($_POST['showjob'])
	writeJobFile(); // write job file
elseif ($_POST['jobid'])
	jobForm(); // fill out job form
else
	selectFrealignJob(); // select a prepared frealign job

/*
******************************************
******************************************
******************************************
*/

function selectFrealignJob($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	processing_header("Frealign Job Launcher","Frealign Job Launcher", $javafunc);
	if ($expId) {
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		exit;
	}
	$particle = new particledata();

	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";

	// get prepared frealign jobs
	//$frealignjobs = $particle->getJobIdsFromSession($expId, $jobtype='prepfrealign', $status='D');
	$rawfrealignjobs = $particle->getPreparedFrealignJobs();

	// print jobs with radio button
	if (!$rawfrealignjobs) {
		echo "<font color='#CC3333' size='+2'>No prepared frealign jobs found</font>\n";
		exit;
	} 

	// check if jobs have associated cluster jobs
	$frealignjobs = array();
	foreach ($rawfrealignjobs as $frealignjob) {
		$frealignrun = $particle->getClusterJobByTypeAndPath('runfrealign', $frealignjob['path']);
		if (!$frealignrun)
			$frealignjobs[] = $frealignjob;
	}

	// print jobs with radio button
	if (!$frealignjobs) {
		echo "<font color='#CC3333' size='+2'>No prepared frealign jobs available</font>\n";
		exit;
	} 

	echo "<table class='tableborder' border='1'>\n";
	foreach ($frealignjobs as $frealignjob) {
		echo "<tr><td>\n";
		$id = $frealignjob['DEF_id'];
		if ($frealignjob['hidden'] != 1) {
			echo "<input type='radio' NAME='jobid' value='$id' ";
			echo "><br/>\n";
			echo"Launch<br/>Job\n";
		}
		echo "</td><td>\n";

		echo frealigntable($frealignjob['DEF_id']);

		echo "</td></tr>\n";
	}
	echo "</table>\n\n";

	echo "<P><input type='SUBMIT' NAME='submitprepared' VALUE='Use this prepared job'></FORM>\n";

	echo frealignRef();

	processing_footer();
	exit;
};

/*
******************************************
******************************************
******************************************
*/

function jobForm($extra=false) {
	global $clusterdata, $CLUSTER_CONFIGS, $selectedcluster;
	$expId = $_GET['expId'];
	if ($expId) {
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		exit;
	}
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	$jobid = $_POST['jobid'];

	// write out errors, if any came up:
	if (!$jobid)
		selectFrealignJob("ERROR: No prepared frealign job id was selected");
	if (!($user && $pass))
		selectFrealignJob("ERROR: You are not logged in");
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	$particle = new particledata();
	$jobdatas = $particle->getPreparedFrealignJobs($jobid);
	$jobdata = $jobdatas[0];
	$rundir = $jobdata['path'];
	$name = $jobdata['name'];
	$nodes = $jobdata['nodes'];
	$ppn = $jobdata['ppn'];
	$rpn = $jobdata['rpn'];
	$memory = $jobdata['memory'];

	// prepare stack values
	$refinestackid = $jobdata['REF|ApStackData|stack'];
	$refinestackdata = $particle->getStackParams($refinestackid);
	$numpart=$particle->getNumStackParticles($refinestackid);
	$apix = $particle->getStackPixelSizeFromStackId($refinestackid)*1e10;
	$boxsize = $refinestackdata['boxsize'];
	$refinestackvals = "$refinestackid|--|$apix|--|$boxsize|--|$numpart|--|$refinestackdata[path]|--|$refinestackdata[name]";
	$reconstackid = $jobdata['REF|ApStackData|reconstack'];
	if ($reconstackid) {
		$reconstackdata = $particle->getStackParams($reconstackid);
		$reconstackvals = "$reconstackid|--|$apix|--|$boxsize|--|$numpart|--|$reconstackdata[path]|--|$reconstackdata[name]";
	}
	// prepare model values
	$modelid = $jobdata['REF|ApInitialModelData|model'];
	$modeldata = $particle->getInitModelInfo($modelid);
	$symdata = $particle->getSymInfo($modeldata['REF|ApSymmetryData|symmetry']);
	$modelvals = "$modelid|--|$modeldata[path]|--|$modeldata[name]|--|$modeldata[boxsize]|--|$symdata[symmetry]";
	// Hack: we must assign the POST values
	$_POST['model'] = $modelvals;
	$_POST['stackval'] = $refinestackvals;

	// set remote path
	$leginondata = new leginondata();
	$sessiondata = $leginondata->getSessionInfo($expId);
	$sessionpath = $sessiondata['Image path'];
	ereg("(.*)leginon(.*)rawdata", $sessionpath, $reg_match);
	$rootpath = "appion".$reg_match[2]."recon/";
	$sessionpath=$reg_match[1].$rootpath;
	$clusterdata->set_rootpath($rootpath);
	$clusterdata->post_data();
	$clusterdefaults = ($selectedcluster==$_POST['clustermemo']) ? true : false;

	$walltime = ($_POST['walltime'] && $clusterdefaults) ? $_POST['walltime'] : C_WALLTIME_DEF;
	$cput = ($_POST['cput'] && $clusterdefaults) ? $_POST['cput'] : C_CPUTIME_DEF;

	$javafunc .= writeJavaPopupFunctions('eman');
	processing_header("Frealign Job Launcher","Frealign Job Launcher", $javafunc);

	echo "<form name='frealignjob' method='post' action='$formaction'><br />\n";
	echo "<input type='hidden' name='clustermemo' value='$selectedcluster'>\n";
	echo "<input type='hidden' name='jobid' value='$jobid'>\n";
	echo "<input type='hidden' NAME='model' value='$modelvals'>\n";
	echo "<input type='hidden' NAME='refinestackvals' value='$refinestackvals'>\n";
	echo "<input type='hidden' NAME='stackval' value='$refinestackvals'>\n";
	echo "<input type='hidden' NAME='reconstackvals' value='$reconstackvals'>\n";

	// SETUP FILELIST TO COPY OVER FILES
	$sendfilelist = "";
	$ext=strrchr($refinestackdata['name'],'.');
	$refinestackname=substr($refinestackdata['name'],0,-strlen($ext));
	$sendfilelist .= formatEndPath($refinestackdata['path']).$refinestackname.".hed";
	$sendfilelist .= "|--|";
	$sendfilelist .= formatEndPath($refinestackdata['path']).$refinestackname.".img";
	$sendfilelist .= "|--|";
	$sendfilelist .= formatEndPath($rundir).$jobdata['tarfile'];
	if ($reconstackid) {
		$reconstackname=substr($reconstackdata['name'],0,-strlen($ext));
		$sendfilelist .= "|--|";
		$sendfilelist .= formatEndPath($reconstackdata['path']).$reconstackname.".hed";
		$sendfilelist .= "|--|";
		$sendfilelist .= formatEndPath($reconstackdata['path']).$reconstackname.".img";
	}
	echo "<input type='hidden' NAME='sendfilelist' value='$sendfilelist'>\n";
	$receivefilelist = "results.tgz|--|models.tgz";
	echo "<input type='hidden' NAME='receivefilelist' value='$receivefilelist'>\n";

	echo "<table border='0' cellpadding='0' cellspacing='0' width='600'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr>\n";
	echo "<td><b>Cluster:</b></td>\n";
	echo "<td><select name='cluster' onchange='frealignjob.submit()'>\n";
	foreach ($CLUSTER_CONFIGS as $cluster) {
		$s = ($cluster == $_POST['cluster']) ? 'selected' : '';
		echo '<option value="'.$cluster.'" '.$s.' >'.$cluster.'</option>'."\n";
	}
	echo "</select></td></tr>\n";

	echo "<tr><td><b>Run Name:</b></td><td>$name</td></tr>\n";
	echo "<input type='hidden' name='jobname' value='$name'>\n";
	echo "<tr><td><b>Run Directory:</b></td><td>$rundir</td></tr>\n";
	$outdir = ereg_replace($name."$", "", $rundir);
	echo "<input type='hidden' name='rundir' value='$rundir'>\n";
	echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	echo "</table>\n";
	echo closeRoundBorder();
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "<p>\n";

	//--- overall PBS tables
	echo "<table border='0'><tr><td valign='top'>"; 

	//--- Cluster Parameters
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr>\n";
	echo "<td colspan='4' align='center'>\n";
	echo "<h4>PBS Cluster Parameters</h4>\n";
	echo "</td>\n";
	echo "</tr>\n";
	// row 1 col 1-2
	echo "<tr><td>\n";
		echo docpop('nodes',"Nodes: ");
	echo "</td><td>\n";
		echo "<b>$nodes</b>";
	echo "<input type='hidden' name='nodes' value='$nodes'>\n";
	// row 1 col 3-4
	echo "</td><td>\n";
		echo docpop('procpernode',"Proc/Node: ");
	echo "</td><td>\n";
		echo "<b>$ppn</b>";
	echo "<input type='hidden' name='ppn' value='$ppn'>\n";
	echo "</td><td>\n";
		echo docpop('reconpernode',"Recons/Node: ");
	echo "</td><td>\n";
		echo "<b>$rpn</b>";
	echo "<input type='hidden' name='rpn' value='$rpn'>\n";
	// row 1 col 5-6
	echo "</td><td>\n";
		echo docpop('memory',"Memory: ");
	echo "</td><td>\n";
		echo "<b>$memory GB</b>";
	echo "<input type='hidden' name='memory' value='$memory'>\n";
	// row 2 col 1-3
	echo "</td></tr><tr><td>&nbsp;\n";
	echo "</td></tr><tr><td>\n";
		echo docpop('walltime',"Wall Time: ");
	echo "</td><td>\n";
		echo "<input type='text' NAME='walltime' VALUE='$walltime' SIZE='4'>";
	echo "</td><td>\n";
		echo "hours";
	// row 2 col 4-6
	echo "</td><td>\n";
		echo docpop('cputime',"CPU Time: ");
	echo "</td><td>\n";
		echo "<input type='text' NAME='cput' VALUE='$cput' SIZE='4'>";
	echo "</td><td>\n";
		echo "hours";
	echo "</td></tr>\n";
	echo "</table>\n";
	// row 3
	echo $clusterdata->cluster_parameters();
	echo closeRoundBorder();
	echo "<br/>\n";
	echo "<br/>\n";

	echo"</td></tr></table>"; //overall table

	echo"<input type='SUBMIT' NAME='showjob' VALUE='Show Job File'><br/><hr/>\n";

	echo"</form><br/>\n";

	echo frealignRef();

	//echo "StackID: $stackid -- ModelID: $modelid<br/>\n";
	echo "<table class='tablebubble'><tr><td>\n";
	echo stacksummarytable($refinestackid, true);
	if ($reconstackid) {
		echo "</td></tr><tr><td>\n";
		echo stacksummarytable($reconstackid, true);
	}
	echo "</td></tr><tr><td>\n";
	echo modelsummarytable($modelid, true);
	echo "</td></tr></table>\n";

	processing_footer();
	exit;
}
/*
******************************************
******************************************
******************************************
*/

function writeJobFile ($extra=False) {
	global $clusterdata;
	$particle = new particledata();
	$expId = $_GET['expId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	$jobid = $_POST['jobid'];
	if (!$jobid)
		selectFrealignJob("ERROR: No prepared frealign job id was selected");
	$jobdatas = $particle->getPreparedFrealignJobs($jobid);
	$jobdata = $jobdatas[0];

	if (!($user && $pass))
		jobForm("ERROR: You are not logged in");
	if (!$_POST['nodes'])
		jobForm("ERROR: No nodes specified, setting default=".C_NODES_DEF);
	if (!$_POST['ppn'])
		jobForm("ERROR: No processors per node specified, setting default=".C_PPN_DEF);
	if ($_POST['ppn'] > C_PPN_MAX )
		jobForm("ERROR: Max processors per node is ".C_PPN_MAX);
	if ($_POST['nodes'] > C_NODES_MAX )
		jobForm("ERROR: Max nodes on ".C_NAME." is ".C_NODES_MAX);
	if (!$_POST['walltime'])
		jobForm("ERROR: No walltime specified, setting default=".C_WALLTIME_DEF);
	if ($_POST['walltime'] > C_WALLTIME_MAX )
		jobForm("ERROR: Max walltime is ".C_WALLTIME_MAX);
	if (!$_POST['cput'])
		jobForm("ERROR: No CPU time specified, setting default=".C_CPUTIME_DEF);
	if ($_POST['cput'] > C_CPUTIME_MAX)
		jobForm("ERROR: Max CPU time is ".C_CPUTIME_MAX);

	$clustername = C_NAME;
	$clusterpath = $clusterdata->get_path();
	$clusterpath = formatEndPath($clusterpath);
	$clusterdata->post_data();
	// insert the job file into the database
	if (!$extra) {
		$javafunc.=$clusterdata->get_javascript();
	}
	processing_header("Frealign Job Launcher","Frealign Job Launcher", $javafunc);

	// write out errors, if any came up:
	if (!$extra) {
		echo $clusterdata->cluster_check_msg();
		echo "<p>";
	} else {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	// get the stack info (pixel size, box size)
	$refinestackinfo = explode('|--|',$_POST['refinestackvals']);
	$refinestackid = $refinestackinfo[0];
	$reconstackinfo = explode('|--|',$_POST['reconstackvals']);
	$reconstackid = $reconstackinfo[0];

	// get the model id
	$modelinfo=explode('|--|',$_POST['model']);
	$modelid = $modelinfo[0];
	$initmodel = $particle->getInitModelInfo($modelid);

	$header.= "#PBS -l nodes=".$jobdata['nodes'].":ppn=".$jobdata['ppn']."\n";
	$header.= "#PBS -l walltime=".$_POST['walltime'].":00:00\n";
	$header.= "#PBS -l cput=".$_POST['cput'].":00:00\n";
	$header.= "#PBS -l mem=".$jobdata['memory']."gb\n";
	$header.= "#PBS -m e\n";
	$header.= "#PBS -r n\n";
	$header.= "#PBS -j oe\n\n";

	$clusterjob.= "# refineStackId: $refinestackid\n";
	$clusterjob.= "# reconStackId: $reconstackid\n";
	$clusterjob.= "# modelId: $modelid\n\n";
	
	$procs=$jobdata['nodes']*$jobdata['rpn'];

	$runfile = formatEndPath($jobdata['path'])."frealign.run.job";
	$runlines = file_get_contents($runfile);

	$runlines .= "\n";
	$runlines .= "tar -czf results.tgz *iter* *.txt *.log\n";
	$runlines .= "tar -czf models.tgz threed*\n";

	$clusterjob .= $clusterdata->cluster_job_file($runlines);

	$jobfile = $jobdata['name'].".job";

	echo "<form name='frealignjob' method='POST' action='$formAction'>\n";
	echo "<input type='hidden' name='clustername' value='".C_NAME."'>\n";
	echo "<input type='hidden' name='cluster' value='".C_NAME."'>\n";
	echo "<input type='hidden' NAME='clusterpath' value='$clusterpath'>\n";
	echo "<input type='hidden' NAME='dmfpath' value='".$_POST['dmfpath']."'>\n";
	echo "<input type='hidden' NAME='jobname' value='".$jobdata['name']."'>\n";
	echo "<input type='hidden' NAME='outdir' value='".$_POST['outdir']."'>\n";
	echo "<input type='hidden' NAME='mem' value='".$jobdata['memory']."gb'>\n";
	echo "<input type='hidden' NAME='model' value='".$_POST['model']."'>\n";

	// convert \n to /\n's for script
	$header_conv=preg_replace('/\n/','|--|',$header);

	echo "<input type='hidden' NAME='header' VALUE='$header_conv'>\n";
	echo "<input type='submit' NAME='submitjob' VALUE='Submit Job to Cluster'>\n";
	echo "</form>\n";
	echo "</p>";
	if (!$extra) {
		echo "<hr>\n";
		echo "<pre>\n";
		echo $header;
		echo $clusterjob;
		echo "</pre>\n";
		$tmpfile = "/tmp/$jobfile";
		// write file to tmp directory
		$f = fopen($tmpfile,'w');
		fwrite($f, $clusterjob);
		fclose($f);
	}

	echo frealignRef();

	processing_footer();
	exit;
}
/*
******************************************
******************************************
******************************************
*/

function submitJob($extra=False) {
	global $clusterdata;
	$particle = new particledata();
	$clusterdata->post_data();

	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$host = $clusterdata->hostname;
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	if (!($user && $pass))
		jobForm("<B>ERROR:</B> Enter a user name and password");

	$jobname = $_POST['jobname'];
	$outdir = $_POST['outdir'].$jobname;

	$dmfpath=null;
	if (!empty($_POST['dmfpath'])) {
		$dmfpath=$_POST['dmfpath'].$jobname;
	}

	$clusterpath=$_POST['clusterpath'].$jobname;
	$jobfile="$jobname.job";
	$tmpjobfile = "/tmp/$jobfile";
	if (!file_exists($tmpjobfile))
		writeJobFile("<B>ERROR:</B> Could not find temp jobfile: $tmpjobfile");	

	$jobid=$particle->insertClusterJobData($host,$outdir,$dmfpath,$clusterpath,$jobfile,$expId,'runfrealign',$user);

	// add header & job id to the beginning of the script
	// convert /\n's back to \n for the script
	$header = explode('|--|',$_POST['header']);
	$clusterjob = "## $jobname\n";
	foreach ($header as $l) $clusterjob.="$l\n";

	$clusterjob.= C_APPION_BIN."updateAppionDB.py $jobid R $projectId\n\n";
	$clusterjob.= "# jobId: $jobid\n";
	$clusterjob.= "# projectId: $projectId\n";
	$clusterlastline.= C_APPION_BIN."updateAppionDB.py $jobid D $projectId\nexit\n\n";
	$f = file_get_contents($tmpjobfile);
	file_put_contents($tmpjobfile, $clusterjob . $f . $clusterlastline);

	processing_header("Frealign Job Launcher","Frealign Job Launcher", $javafunc);
	

	// create appion directory & copy job file
	$cmd = "mkdir -p $clusterpath;\n";
	
	$rvalue = exec_over_ssh($host, $user, $pass, $cmd, True);
	if ($rvalue === false ){
		$errMsg = "Error: Could not create run directory on $host: ";
		$errMsg .= pconnError();
		echo "<hr>\n<font color='#CC3333' size='+1'>$errMsg</font>\n";
		unlink ($tmpjobfile); //make sure to clean up after ourselves
		exit;
	}
	
	$remoteJobFile = "$clusterpath/$jobfile";
	$rvalue = scp($host, $user, $pass, $tmpjobfile, $remoteJobFile);	
	if (!$rvalue){
		$errMsg = "Error: Copying jobfile to $clusterpath on $host failed: ";
		$errMsg .= pconnError();
		echo "<hr>\n<font color='#CC3333' size='+1'>$errMsg</font>\n";
		unlink($tmpjobfile);//make sure to clean up after ourselves
		exit;
	}
		
	//The preceding lines make the call to this function redundant as it
	//is implimented in some cluster configs.
	//$clusterdata->cluster_cmd($host, $user, $pass);

	// if on guppy, clusterpath is same as outdir
	$path = formatEndPath($clusterdata->get_path()).$jobname;
	echo "<table width='600'>\n";
	echo "<tr><td>Appion Directory</td><td>$outdir</td></tr>\n";
	echo "<tr><td>Cluster Job File</td><td>$path.job</td></tr>\n";
	echo "<tr><td>Appion Job Id</td><td>$jobid</td></tr>\n";
	echo "<tr><td>Job File Name</td><td>$jobname.job</td></tr>\n";
	
	// submit job on host
	$cmd = "cd $path; qsub $jobfile;\n";
	
	//If exec_over_ssh returns false the job submition failed do to a connection
	//error.
	if ($jobnumstr === false){		
		$errMsg = "Error: submitting job to $host failed:  ";
		$errMsg .= pconnError();
		echo "</table><p>\n";
		echo "<hr>\n<font color='#CC3333' size='+1'>$errMsg</font>\n";
		unlink($tmpjobfile); //make sure to clean up after ourselves
		exit;
	}
	
	$jobnum = trim($jobnumstr);
	echo "<tr><td>Cluster Job Id</td><td>$jobnum</td></tr>\n";
	$jobnum = ereg_replace('\..*','',$jobnum);
	
	// Chech for no-connection related error in job submission.
	if (!is_numeric($jobnum)) {
		echo "</table><p>\n";
		echo "<hr>\n<font color='#CC3333' size='+1'>ERROR: job submission failed</font>\n";
		echo "message: '$jobnum'<br/>";
		processing_footer();
		unlink($tmpjobfile);//make sure to clean up after ourselves
		exit;
	}

	// We need to check the status of the job so that we do not overwrite it in the following updateClusterQueue refs #706
	$jobinfo = $particle->getJobInfoFromId($jobid);
	
	// This could still overwrite the status if the job file is executed after the if and before updateClusterQueue below
	if ( $jobinfo['status'] ) {
		$status = $jobinfo['status'];
	} else {
		$status = 'Q';
	}
	
	// insert cluster job id into row that was just created
	$particle->updateClusterQueue($jobid, $jobnum, $status);
	
	echo "<tr><td>Cluster Directory</td><td>$clusterpath</td></tr>\n";
	echo "<tr><td>Job number</td><td>$jobnum</td></tr>\n";
	echo "</table>\n";

	// check jobs that are running on the cluster
	echo "<P>Jobs currently running on the cluster:\n";
	$subjobs = checkClusterJobs($host,$user,$pass);
	if ($subjobs) {echo "<PRE>$subjobs</PRE>\n";}
	else {echo "<FONT COLOR='#CC3333'>No Jobs on the cluster, check your settings</FONT>\n";}
	echo "<p><a href='checkRefineJobs.php?expId=$expId'>"
		."[Check Status of Jobs Associated with this Experiment]</a><p>\n";
	echo "<P><hr>\n<font color='#CC3333' size='+1'>Do not hit 'reload' - it will re-submit job</FONT><P>\n";
	processing_footer(True, True);
	unlink($tmpjobfile);//make sure to clean up after ourselves
	exit;
}

/*
******************************************
******************************************
******************************************
*/

?>
