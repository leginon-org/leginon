<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an Spider Job for submission to a cluster
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";
require_once "inc/path.inc";

$selectedcluster=$CLUSTER_CONFIGS[0];
if ($_POST['cluster']) {
	$selectedcluster=$_POST['cluster'];
}
$selectedcluster=strtolower($selectedcluster);
@include_once $selectedcluster.".php";

if ($_POST['write']) {
	// write job file
	$particle = new particledata();

	if (!$_POST['nodes']) jobForm("ERROR: No nodes specified, setting default=".C_NODES_DEF);
	if (!$_POST['ppn']) jobForm("ERROR: No processors per node specified, setting default=".C_PPN_DEF);
	if ($_POST['ppn'] > C_PPN_MAX ) jobForm("ERROR: Max processors per node is ".C_PPN_MAX);
	if ($_POST['nodes'] > C_NODES_MAX ) jobForm("ERROR: Max nodes on ".C_NAME." is ".C_NODES_MAX);
	if (!$_POST['walltime']) jobForm("ERROR: No walltime specified, setting default=".C_WALLTIME_DEF);
	if ($_POST['walltime'] > C_WALLTIME_MAX ) jobForm("ERROR: Max walltime is ".C_WALLTIME_MAX);
	if (!$_POST['cput']) jobForm("ERROR: No CPU time specified, setting default=".C_CPUTIME_DEF);
	if ($_POST['cput'] > C_CPUTIME_MAX) jobForm("ERROR: Max CPU time is ".C_CPUTIME_MAX);
	if (!$_POST['rprocs']) jobForm("ERROR: No reconstruction ppn specified, setting default=".C_RPROCS_DEF);
	if ($_POST['rprocs'] > $_POST['ppn'])
	  jobForm("ERROR: Asking to reconstruct on more processors than available");


	if (!$_POST['ang_inc']) jobForm("ERROR: no angular increment set for iteration $i");
	if (!$_POST['mask']) jobForm("ERROR: no mask set for iteration $i");

	$lastring=($_POST['lastring']) ? $_POST['lastring']:$_POST['mask'];
	// make sure that xysearch & lastring are appropriate
	$stackinfo=explode('|--|',$_POST['stackval']);
	$halfbox=$stackinfo[2]/2-2;
	if (($_POST['xysearch']+$lastring) > $halfbox) jobForm("ERROR: lastring + xysearch must be less than $halfbox");

	// check that job file doesn't already exist
	$outdir = Path::formatEndPath($_POST['outdir']);
	$outdir .= $_POST['jobname'];

	// jobname ends with .job
	$jobname = $_POST['jobname'];
	$jobname .= '.job';
	$exists = $particle->getJobFileFromPath($outdir,$jobname);
	writeJobFile();
}

elseif ($_POST['submitstackmodel']) {
	// create job form
	## make sure a stack and model were selected
	if (!$_POST['model']) stackModelForm("ERROR: no initial model selected");
	if (!$_POST['stackval']) stackModelForm("ERROR: no stack selected");
	jobForm();
}

elseif ($_POST['submitjob']) {
	// submit job
	$particle = new particledata();
	$clusterdata->post_data();

	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$host = $clusterdata->hostname;
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	if (!($user && $pass)) writeJobFile("<B>ERROR:</B> Enter a user name and password");

	$jobname = $_POST['jobname'];
	$outdir = $_POST['outdir'].$jobname;

	$dmfpath=null;
	if (!empty($_POST['dmfpath'])) {
		$dmfpath=$_POST['dmfpath'].$jobname;
	}

	$clusterpath=$_POST['clusterpath'].$jobname;
	$jobfile="$jobname.job";
	$tmpjobfile = "/tmp/$jobfile";
	
	$jobid=$particle->insertClusterJobData($host,$outdir,$dmfpath,$clusterpath,$jobfile,$expId,'recon',$user);

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

	processing_header("SPIDER Job Submitted","SPIDER Job Submitted",$javafunc);
	

	// create appion directory & copy job file
	$cmd = "mkdir -p $clusterpath;\n";
	
	$rvalue = exec_over_ssh($host, $user, $pass, $cmd, false);
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
	
	
	$path = Path::formatEndPath($clusterdata->get_path()).$jobname;
	echo "<table width='600'>\n";
	echo "<tr><td>Appion Directory</td><td>$outdir</td></tr>\n";
	echo "<tr><td>Cluster Job File</td><td>$path.job</td></tr>\n";
	echo "<tr><td>Job File Name</td><td>$jobname.job</td></tr>\n";

	// submit job on host
	$cmd = "cd $path; qsub $jobfile;\n";
	$jobnumstr = exec_over_ssh($host, $user, $pass, $cmd, True);
  
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
	$jobnum = preg_replace('%\..*%','',$jobnum);
	
	// Chech for no-connection related error in job submission.
	if (!is_numeric($jobnum)) {
		echo "</table><p>\n";
		echo "<hr>\n<font color='#CC3333' size='+1'>ERROR: job submission failed</font>\n";
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
	else {echo "<FONT COLOR='RED'>No Jobs on the cluster, check your settings</FONT>\n";}
	echo "<p><a href='checkRefineJobs.php?expId=$expId'>[Check Status of Jobs Associated with this Experiment]</a><p>\n";
	echo "<P><hr>\n<font color='#CC3333' size='+1'>Do not hit 'reload' - it will re-submit job</FONT><P>\n";
	processing_footer(True, True);
	unlink($tmpjobfile);//make sure to clean up after ourselves
	exit;
}

else stackModelForm();

function stackModelForm($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectId = getProjectId();

	$javafunc="<script src='../js/viewer.js'></script>\n";
	processing_header("Spider Job Generator","Spider Job Generator",$javafunc);

	if ($expId) {
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		exit;
	}

	$particle = new particledata();

	// get initial models associated with project
	$models = $particle->getModelsFromProject($projectId);

	// find each stack entry in database
	$stackIds = $particle->getStackIds($expId);
	$stackinfo = explode('|--|', $_POST['stackval']);
	$stackidval = $stackinfo[0];
	$apix = $stackinfo[1];
	$box = $stackinfo[2];

	// write out errors, if any came up:
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";

	echo"<b>Stack:</b><br>";
	$particle->getStackSelector($stackIds, $stackidval, '');

	// show initial models
	echo "<P><B>Model:</B><br><A HREF='uploadmodel.php?expId=$expId'>[Upload a new initial model]</A><br>\n";
	echo "<P><input type='SUBMIT' NAME='submitstackmodel' VALUE='Use this stack and model'><br>\n";

	$minf = explode('|--|',$_POST['model']);
	if (is_array($models) && count($models)>0) {
		echo "<table class='tableborder' border='1'>\n";
		foreach ($models as $model) {
			echo "<tr><td>\n";
			$modelid = $model['DEF_id'];
			$symdata = $particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);
			$modelvals = "$model[DEF_id]|--|$model[path]|--|$model[name]|--|$model[boxsize]|--|$symdata[symmetry]";
			echo "<input type='radio' NAME='model' value='$modelvals' ";
			// check if model was selected
			if ($modelid == $minf[0]) echo " CHECKED";
			echo ">\n";
			echo"Use<br/>Model\n";

			echo "</td><td>\n";

			echo modelsummarytable($modelid, true);

			echo "</td></tr>\n";
		}
		echo "</table>\n\n";
		echo "<P><input type='SUBMIT' NAME='submitstackmodel' VALUE='Use this stack and model'></FORM>\n";
	}
	else echo "No initial models in database";

	echo spiderRef();

	processing_footer();
	exit;
}


function jobForm($extra=false) {
	global $clusterdata, $CLUSTER_CONFIGS, $selectedcluster;
	$expId = $_GET['expId'];

	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	// get path data for this session for output
	$leginondata = new leginondata();
	$sessiondata = $leginondata->getSessionInfo($expId);
	$sessionpath=getBaseAppionPath($sessiondata).'/recon/';
	preg_match("%(.*)appion(.*)recon%", $sessionpath, $reg_match);
	$rootpath = "appion".$reg_match[2]."recon/";

	$clusterdata->set_rootpath($rootpath);
	$clusterdata->post_data();

	$particle = new particledata();


	// get stack data
	$stackinfo = explode('|--|',$_POST['stackval']);
	$box = $stackinfo[2];

	// get model data
	$modelinfo = explode('|--|',$_POST['model']);
	$syminfo = explode(' ',$modelinfo[4]);
	$modsym=$syminfo[0];
	if ($modsym == 'Icosahedral') $modsym='icos';

	$clusterdefaults = ($selectedcluster==$_POST['clustermemo']) ? true : false;
	

	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$reconruns = count($particle->getJobIdsFromSession($expId, 'recon'));
	while (file_exists($outdir.'recon'.($reconruns+1)))
		$reconruns += 1;
	$defrunid = 'recon'.($reconruns+1);
	$jobname = ($_POST['jobname']) ? $_POST['jobname'] : $defrunid;

	$nodes = ($_POST['nodes'] && $clusterdefaults) ? $_POST['nodes'] : C_NODES_DEF;
	$ppn = ($_POST['ppn'] && $clusterdefaults) ? $_POST['ppn'] : C_PPN_DEF;
	$rprocs = ($_POST['rprocs'] && $clusterdefaults) ? $_POST['rprocs'] : C_RPROCS_DEF;
	$walltime = ($_POST['walltime'] && $clusterdefaults) ? $_POST['walltime'] : C_WALLTIME_DEF;
	$cput = ($_POST['cput'] && $clusterdefaults) ? $_POST['cput'] : C_CPUTIME_DEF;

	$numiters= ($_POST['numiters']) ? $_POST['numiters'] : 1;
	if ($_POST['duplicate']) {
		$numiters+=1;
		$j=$_POST['duplicate'];
	}
	else $j=$numiters;

	$javafunc .= defaultReconValues($box);
	$javafunc .= writeJavaPopupFunctions('spider');
	processing_header("SPIDER Job Generator","SPIDER Job Generator",$javafunc);
	// write out errors, if any came up:
	if (!($user && $pass)) echo "<font color='red'><B>WARNING!!!</B> You are not logged in!!!</font><br />";
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo "<form name='spiderjob' method='post' action='$formaction'><br />\n";
	echo "<input type='hidden' name='submitstackmodel' value='true'>\n";
	echo "<input type='hidden' name='clustermemo' value='".$selectedcluster."'>\n";
	echo "<input type='hidden' name='model' value='".$_POST['model']."'>\n";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";

	echo "<table border='0' cellpadding='0' cellspacing='0' width='600'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
	echo "<tr>
    <td><b>Cluster:</b></td>
		<td><select name='cluster' onchange='spiderjob.submit()'>
		";
		foreach ($CLUSTER_CONFIGS as $cluster) {
			$s = ($cluster == $_POST['cluster']) ? 'selected' : '';
			echo '<option value="'.$cluster.'" '.$s.' >'.$cluster.'</option>'."\n";
		}
	echo "
		</select></td>
  </tr>
  <tr>
    <td><B>Job Run Name:</B></td>
    <td><input type='text' name='jobname' value='$jobname' size='20'></td>
  </tr>
  <tr>
    <td><B>Output Directory:</B></td>
    <td><input type='text' NAME='outdir' value='$outdir' size='50'></td>
  </tr>
  </table>\n";
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
	echo "<tr>
      <td><a href='#' id='lcp1' onMouseOver='popLayer(\"nodes\", \"lcp1\")' onMouseOut='hideLayer()'>Nodes:</A></td>
      <td><input type='text' NAME='nodes' VALUE='$nodes' SIZE='4' MAXCHAR='4'></td>
      <td><a href='#' id='lcp2' onMouseOver='popLayer(\"procpernode\", \"lcp2\")' onMouseOut='hideLayer()'>Proc/Node:</A></td>
      <td><input type='text' NAME='ppn' VALUE='$ppn' SIZE='3'></td>
    </tr>
    <tr>
      <td><a href='#' id='lcp3' onMouseOver='popLayer(\"walltime\", \"lcp3\")' onMouseOut='hideLayer()'>Wall Time:</A></td>
      <td><input type='text' NAME='walltime' VALUE='$walltime' SIZE='4'></td>
      <td><a href='#' id='lcp4' onMouseOver='popLayer(\"cputime\", \"lcp4\")' onMouseOut='hideLayer()'>CPU Time</A></td>
      <td><input type='text' NAME='cput' VALUE='$cput' SIZE='4'></td>
    </tr>
    <tr>
      <td colspan='4'>
      Reconstruction procs per node:<input type='text' NAME='rprocs' VALUE='$rprocs' SIZE='3'>
      </td>
    </tr>
    </table>\n";
/*
	echo closeRoundBorder();

	echo"</td><td valign='top'>"; //overall table

	//DMF Parameters TABLE
	echo openRoundBorder();
*/
	echo $clusterdata->cluster_parameters();

	echo closeRoundBorder();
	echo"</td></tr></table>"; //overall table

	$bgcolor="#E8E8E8";
	$display_keys = array('sym','mask','imask','firstring','lastring','xysearch','lp','hp','xyshift','keep');  
	echo"
  <br />
  <H4 style='align=\'center\' >SPIDER Reconstruction Parameters</H4>
  <hr />
	";

	echo "<input type='BUTTON' onClick='setDefaults(this.form)' VALUE='Set Defaults for Iteration 1'>\n";
	echo "<br />
  <TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4>
    <tr>\n";
	foreach ($display_keys as $p) {
		echo "<td align='center' bgcolor='$bgcolor'><font class='sf'>\n";
		echo docpop($p,$p);
		echo "</font></td>\n";
	}
	echo "</tr>\n";
	echo "<tr>\n";
	foreach ($display_keys as $p) {
		if ($p == 'sym') $sym = ($_POST['sym']) ? $_POST['sym'] : $modsym;
		else ${$p} = ($_POST[$p]!='') ? $_POST[$p] : '';
		echo "<td><input type='text' name='$p' size='4' value='${$p}'></td>\n";
	}
	echo "</tr>\n";
	echo "</table>\n";
	echo "<br>\n";
	$ang_inc = ($_POST['ang_inc']) ? $_POST['ang_inc'] : '';
	echo docpop('ang_inc',"Angular Increments:");
	echo "<input type='text' name='ang_inc' value='$ang_inc' size='30'>\n";
	echo "<br>\n";
	echo "<input type='submit' name='write' value='Create Job File'>\n";
  	echo "</form>\n";

	echo spiderRef();

	processing_footer();
	exit;
}

function getPBSMemoryNeeded($boxsize) {
	$particle = new particledata();
	$angles=explode(',',$_POST['ang_inc']);
	$numiters=count($angles);
	$maxang=$angles[$numiters-1];
	$emansym=$_POST["sym"];
	$symdata = $particle->getSymmetryDataFromEmanName($emansym);
	$foldsym = (int) $symdata['fold_symmetry'];
	$numproj = 18000.0/($foldsym*$maxang*$maxang);
	$memneed = $numproj*$boxsize*$boxsize*16.0;
	$numgig = ceil($memneed/1073741824.0);
	$sizestr = sprintf("%dgb", $numgig);
	return $sizestr;
}

function writeJobFile ($extra=False) {
	global $clusterdata;
	$particle = new particledata();
	$expId = $_GET['expId'];
	$projectId = getProjectId();

	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$dmfpath = $_POST['dmfpath'];

	$jobname = $_POST['jobname'];
	$jobfile ="$jobname.job";
	$logfile ="$jobname.log";
	
	$clustername = C_NAME;
	$outdir = Path::formatEndPath($_POST['outdir']);

	$clusterpath=$clusterdata->get_path();
	$clusterpath = Path::formatEndPath($clusterpath);

	$clusterdata->post_data();

	// get the stack info (pixel size, box size)
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$apix=$stackinfo[1];
	$box=$stackinfo[2];

	// get the model id
	$modelinfo=explode('|--|',$_POST['model']);
	$modelid=$modelinfo[0];
	$initmodel = $particle->getInitModelInfo($modelid);
	if ($initmodel['boxsize'] != $box) $rebox = True; 
	if (round($initmodel['pixelsize'],2) != round($apix,2)) $rescale = "scale=".$initmodel['pixelsize']/$apix;

	$angles=explode(',',$_POST['ang_inc']);
	$numiters=count($angles);
	
	// insert the job file into the database
	if (!$extra) {
		$javafunc.=$clusterdata->get_javascript();
	}
	processing_header("SPIDER Job Generator","SPIDER Job Generator", $javafunc);
	$header.= "#PBS -l nodes=".$_POST['nodes'].":ppn=".$_POST['ppn']."\n";
	$header.= "#PBS -l walltime=".$_POST['walltime'].":00:00\n";
	$header.= "#PBS -l cput=".$_POST['cput'].":00:00\n";
	$header.= "#PBS -l mem=".getPBSMemoryNeeded($box)."\n";
	$header.= "#PBS -m e\n";
	$header.= "#PBS -r n\n";
	$header.= "#PBS -j oe\n\n";
	$clusterjob = "# stackId: $stackidval\n";
	$clusterjob.= "# modelId: $modelid\n\n";
	
	$ang=$_POST["ang"];
	$mask=$_POST["mask"];
	$imask=$_POST["imask"];
	$sym=$_POST["sym"];
	$keep=$_POST["keep"];
	$xyshift=$_POST["xyshift"];
	$keep=$_POST['keep'];
	$firstring=$_POST['firstring'];
	$lastring=$_POST['lastring'];
	$xysearch=$_POST['xysearch'];
	$ang=$_POST['ang_inc'];
	$xysearch=$_POST['xysearch'];
	$lp=$_POST['lp'];
	$hp=$_POST['hp'];
	$proc=$_POST['nodes']*$_POST['ppn'];

	$line="apmqRefine.py ";
	$line.="--stack=$stackidval ";
	$line.="--projectid=$projectId ";
	$line.="--mask=$mask ";
	if ($imask) $line.="--imask=$imask ";
	$line.="--allowed-shift=$xyshift ";
  	$line.="--keepsig=$keep ";
	$line.="--modelid=$modelid ";
	$line.="--first-ring=$firstring ";
	$line.="--last-ring=$lastring ";
	$line.="--xy-search=$xysearch ";
	$line.="--xy-step=1 ";
	$line.="--increment=$ang ";
	if ($lp) $line.="--lowpass=$lp ";
	if ($hp) $line.="--highpass=$hp ";
	$line.="--proc=$proc ";
	$line.="--rundir=. ";
	$spijob= "\nwebcaller.py '$line' ../$logfile\n";
	
	$clusterjob .= $clusterdata->cluster_job_file($spijob);
	
	if (!$extra) {
		echo $clusterdata->cluster_check_msg();
		echo "<p>";
	} else {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo "<form name='spiderjob' method='POST' action='$formAction'>\n";
	echo "<input type='hidden' name='clustername' value='".C_NAME."'>\n";
	echo "<input type='hidden' name='cluster' value='".C_NAME."'>\n";
	echo "<input type='hidden' NAME='clusterpath' value='$clusterpath'>\n";
	echo "<input type='hidden' NAME='dmfpath' value='$dmfpath'>\n";
	echo "<input type='hidden' NAME='jobname' value='$jobname'>\n";
	echo "<input type='hidden' NAME='outdir' value='$outdir'>\n";

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
		fwrite($f,$clusterjob);
		fclose($f);
	}	

	echo spiderRef();

	processing_footer();
	exit;
}

function defaultReconValues ($box) {
	$rad = ($box/2)-8;
	$javafunc = "
<script type='text/javascript'>
	function setDefaults(obj) {
		obj.mask.value = '$rad';
		obj.keep.value = '0';
		obj.xysearch.value = '6';
		obj.firstring.value = '1';
		obj.lastring.value = '$rad';
		obj.lp.value= '10';
		obj.hp.value= '800';
		obj.xyshift.value='0.2';
		return;
	}
</script>\n";
	return $javafunc;
};

?>
