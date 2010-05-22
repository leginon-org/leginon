<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/summarytables.inc";

// IF valueS SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadRecon();
}

// Create the form page
else {
	createUploadReconForm();
}

function createUploadReconForm($extra=false, $title='UploadRecon.py Launcher', $heading='Upload Reconstruction Results') {
	// check if session provided
	$expId = $_GET['expId'];
	$jobId = $_GET['jobId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
		if ($jobId) $formAction.="&jobId=$jobId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}

	$javafunctions .= writeJavaPopupFunctions('appion');  

	$particle = new particledata();

	// if uploading a specific recon, get recon info from database & job file
	if ($jobId) {
		$jobinfo = $particle->getJobInfoFromId($jobId);
		$jobrunid = ereg_replace('\.job$','',$jobinfo['name']);
		$sessionpath = ereg_replace($jobrunid,'',$jobinfo['appath']);
		$jobfile = $jobinfo['appath'].'/'.$jobinfo['name'];
		$f = file($jobfile);
		$package='EMAN';
		foreach ($f as $line) {
			if (preg_match('/^\#\sstackId:\s/',$line)) $stackid=ereg_replace('# stackId: ','',trim($line));
			elseif (preg_match('/^\#\smodelId:\s/',$line)) $modelid=ereg_replace('# modelId: ','',trim($line));
			elseif (preg_match('/^coran_for_cls.py\s/',$line)) $package='EMAN/SpiCoran';
			elseif (preg_match('/^msgPassing_subClassification.py\s/',$line)) $package='EMAN/MsgP';
			if ($stackid && $modelid && $package) break;
		}
		if (file_exists($jobinfo['appath'].'/classes_coran.1.hed'))
			$package='EMAN/SpiCoran';
	}

	$projectId=getProjectId();

	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:

	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	
	echo "<form name='viewerform' method='post' action='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	
	if (!empty($sessioninfo) && !$jobId) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","recon/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	echo "<input type='hidden' name='outdir' value='$sessionpath'>\n";
	
	// Set any existing parameters in form
	$package = ($_POST['package']) ? $_POST['package'] : $package;
	$contour = ($_POST['contour']) ? $_POST['contour'] : '2.0';
	$mass = ($_POST['mass']) ? $_POST['mass'] : '';
	$zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.0';
	$filter = ($_POST['filter']) ? $_POST['filter'] : '';
	$reconname = ($_POST['reconname']) ? $_POST['reconname'] : '';
	$description = $_POST['description'];
	$oneiteration = ($_POST['oneiteration']=="on") ? "CHECKED" : "";
	$iteration = $_POST['iteration'];
	$contiteration = ($_POST['contiteration']=="on") ? "CHECKED" : "";
	$startiteration = $_POST['startiteration'];

	// main table
	echo "<table border='3' class='tableborder'>\n";
	echo "<tr><td>\n";
	echo "<table border='0' cellspacing='10'>\n";
	echo "<tr><td>\n";

	// stats table
	echo "<table>\n";
	echo "<tr><td>\n";
		echo "<b>Recon Name:</b>\n";
	echo "</td><td>\n";
	if ($jobId)
		echo "$jobrunid<input type='hidden' name='reconname' value='$jobrunid'>";
	else
		echo "<input type='text' name='reconname' value='$reconname' size='50'>";
	echo "</td></tr>\n";

	echo "<tr><td>\n";
		echo "<b>Recon Directory:</b>\n";
	echo "</td><td>\n";
	if ($jobId)
		echo "$sessionpath\n";
	else
		echo "<input type='text' name='reconpath' value='$sessionpath' size='50'/>";

	// Stack Info
	echo "<tr><td colspan='2'>\n";
	if ($jobId) {
		echo "<input type='hidden' name='stackid' value='$stackid'>\n";
		echo stacksummarytable($stackid, $mini=true);
	} else {
		echo "Stack:\n";
		$stackIds = $particle->getStackIds($sessionId);
		$particle->getStackSelector($stackIds, '', '');
	}
	echo "</td></tr>\n";

	// Initial Model Info
	echo "<tr><td colspan='2'>\n";
	if ($jobId) {
		echo "<input type='hidden' name='modelid' value='$modelid'>\n";
		echo modelsummarytable($modelid, $mini=true);
	} else {
		echo "Initial Model:\n";
		echo "
			<SELECT name='modelid'>
			<OPTION value=''>Select One</OPTION>\n";
		$models=$particle->getModelsFromProject($projectId);
		foreach ($models as $model) {
			echo "<OPTION value='$model[DEF_id]'";
			if ($model['DEF_id']==$_POST['model']) echo " SELECTED";
			echo "> ".$model['DEF_id']." ($model[description])";
			echo "</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
	echo "</td></tr>\n";

	echo "</td></tr>\n";
	echo "</table>\n";

	// description field
	echo "</td></tr>\n";
	echo "<tr><td>\n";
	echo "<br/>";
	echo "<b>Recon Description:</b><br/>";
	echo "<textarea name='description' rows='3' cols='80'>$description</textarea><br/>";
	echo "<input type='checkbox' name='oneiteration' $oneiteration><B>Upload only iteration </b>";
	echo "<input type='text' name='iteration' value='$iteration' size='4'/><br />";
	echo "<input type='checkbox' name='contiteration' $contiteration><b>Begin with iteration </b>";
	echo "<input type='text' name='startiteration' value='$startiteration' size='4'/><br/>";
	echo "<br/>";

	// Refinement Strategy
	echo "Refinement Strategy:\n";
	$eman      = array(
		'description'=>'<b><font color="#00cc00">Normal EMAN refine</font></b>',
		'setting'=>'EMAN');
	$eman_msgp = array(
		'description'=>'<b><font color="#cc0000">EMAN refine with Message Passing</font></b>',
		'setting'=>'EMAN/MsgP');
	$eman_coran= array(
		'description'=>'<b><font color="#0000cc">EMAN refine with SPIDER Coran</font></b>',
		'setting'=>'EMAN/SpiCoran');
	$packages=array('EMAN'=>$eman,'EMAN/SpiCoran'=>$eman_coran,'EMAN/MsgP'=>$eman_msgp);
	if ($jobId) {
		echo "$package<input type='hidden' name='package' value='$package'><br/>\n";
		echo "Type: '".$packages[$package]['description']."'<br/>\n";
		echo "<br/>\n";
	} else {
		echo "Process Used:
				<select name='package'> ";
		foreach ($packages as $p) {
			echo "<option value='$p[setting]'";
			// select previously set package on resubmit
			if ($p['setting']==$package) echo " SELECTED";
			echo ">  $p[description]";
			echo "</option>\n";
		}
		echo "</select>";
	}
	echo "</td></tr>\n";

	echo "<tr><td class='tablebg'>";
	echo "<br/>";
	echo "<b>Snapshot Options:</b>\n";
	echo "<br/>";
	echo "<input type='text' name='contour' value='$contour' size='4'> Contour Level\n";
	echo "<br/>";
	echo "<input type='text' name='mass' value='$mass' size='4'> Mass (in kDa)\n";
	echo "<br/>";
	echo "<input type='text' name='zoom' value='$zoom' size='4'>\n";	
	echo docpop('snapzoom', 'Zoom');
	echo "<br/>";
	echo "<input type='text' name='filter' value='$filter' size='4'>\n";	
	echo docpop('snapfilter', 'Fixed Low Pass Filter <i>(in &Aring;ngstr&ouml;ms)</i>');
	echo "<br/><br/>";
	echo "</td></tr>\n"
;
	echo "<tr><td align='center'>\n";
	echo "<hr/>\n";
	echo getSubmitForm("Upload Recon");

	// main table
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "</td></tr>\n";
	echo "</table>\n";

	echo "</form>\n";
	echo "</center>\n";

	echo emanRef();

	processing_footer();
	exit;
}

function runUploadRecon() {
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];
 
	$command.="uploadRecon.py ";

	$particle = new particledata();

	// parse params
	$jobId=$_GET['jobId'];
	$description=$_POST['description'];
	$contour=$_POST['contour'];
	$mass=$_POST['mass'];
	$zoom=$_POST['zoom'];
	$filter=$_POST['filter'];
	$oneiteration=$_POST['oneiteration'];
	$iteration=$_POST['iteration'];
	$contiteration=$_POST['contiteration'];
	$startiteration=$_POST['startiteration'];

	//make sure a recon run name was entered
	$runid=$_POST['reconname'];
	if ($_POST['reconname']) $runid=$_POST['reconname'];
	if (!$runid) createUploadReconForm("<B>ERROR:</B> Enter a name of the recon run");
	
	//make sure a stack was chosen
	if ($_POST['stackid'])
		$stackid = $_POST['stackid'];
	elseif ($_POST['stackval'])
		list($stackid, $apix, $boxsize) = split('\|--\|',$_POST['stackval']);
	else
		createUploadReconForm("<B>ERROR:</B> Select the image stack used");


	//make sure a model was chosen
	$modelid = $_POST['modelid'];
	if (!$modelid)
		createUploadReconForm("<B>ERROR:</B> Select the initial model used");
	
	//make sure a package was chosen
	$package=$_POST['package'];
	if (!$package)
		createUploadReconForm("<B>ERROR:</B> Enter the reconstruction process used");

	//make sure a description was entered
	$description=$_POST['description'];
	if (!$description) createUploadReconForm("<B>ERROR:</B> Enter a description of the reconstruction");

	//make sure a package was chosen
	if ($_POST['reconpath'] && $_POST['reconpath']!="./") {
		$reconpath = $_POST['reconpath'];
		if (substr($reconpath,-1,1)!='/') $reconpath.='/';
		$runpath = $reconpath.$runid;
		if (!file_exists($runpath)) createUploadReconForm("<B>ERROR:</B> Could not find recon run directory: ".$runpath);
	}
	else {
		$runpath = "./";
	}
	
	//make sure specific result file is present
	if ($jobId) {
		$jobinfo = $particle->getJobInfoFromId($jobId);
		$fileerror = checkRequiredFileError($jobinfo['appath'],'resolution.txt'); 
	} else {
		$fileerror = checkRequiredFileError($runpath,'resolution.txt'); 
	}
	if ($fileerror) createUploadReconForm($fileerror);

	//make sure the user only want one iteration to be uploaded
	if ($iteration) {
		if (!$oneiteration=='on') createUploadReconForm("<B>ERROR:</B> Select the check box if you really want to upload only one iteration");
	}
	else {
		if ($oneiteration) createUploadReconForm("<B>ERROR:</B> Enter the iteration number if you really want to upload only one iteration");
	}

	//make sure the user wants to start iteration from the middle
	if ($startiteration) {
		if (!$contiteration=='on') createUploadReconForm("<B>ERROR:</B> Select the check box if you really want to begin at iteration $startiteration");
	}
	else {
		if ($contiteration) createUploadReconForm("<B>ERROR:</B> Enter the iteration number if you really don't want to start at the beginning");
	}

	$command.="--projectid=".getProjectId()." ";
	$command.="--runname=$runid ";
	$command.="--stackid=$stackid ";
	$command.="--modelid=$modelid ";
	$command.="--package=$package ";
	if (!$jobId) $command.="--rundir=$runpath ";
	if ($jobId) $command.="--jobid=$jobId ";
	if ($contour) $command.="--contour=$contour ";
	if ($mass) $command.="--mass=$mass ";
	if ($zoom) $command.="--zoom=$zoom ";
	if ($filter) $command.="--filter=$filter ";
	if ($oneiteration=='on' && $iteration) $command.="--oneiter=$iteration ";
	if ($contiteration=='on' && $startiteration) $command.="--startiter=$startiteration ";
	$command.="--description=\"$description\"";
	
	// submit job to cluster
	if ($_POST['process']=="Upload Recon") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadReconForm("<b>ERROR:</b> Enter a user name and password");
		$sub = submitAppionJob($command,$outdir,$runid,$expId,'uploadrecon');
		// if errors:
		if ($sub) createUploadReconForm("<b>ERROR:</b> $sub");
		exit;
	}
	processing_header("UploadRecon Run","UploadRecon Params");
	echo emanRef();
	echo "
	<table class='tableborder' width='600' border='1'>
	<tr><td colspan='2'>
	<b>UploadRecon Command:</b><br>
	$command
	</td></tr>
	<tr><td>run name</td><td>$runid</td></tr>
	<tr><td>stack ID</td><td>$stackid</td></tr>
	<tr><td>model ID</td><td>$modelid</td></tr>
	<tr><td>path</td><td>$reconpath</td></tr>
	<tr><td>jobid</td><td>$jobId</td></tr>
	<tr><td>snapshot contour</td><td>$contour</td></tr>
	<tr><td>snapshot mass</td><td>$mass</td></tr>
	<tr><td>snapshot zoom</td><td>$zoom</td></tr>
	<tr><td>snapshot filter</td><td>$filter</td></tr>
	<tr><td>description</td><td>$description</td></tr>
	</table>\n";
	processing_footer();
}
?>
