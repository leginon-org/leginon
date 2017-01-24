<?php
// compress this file if the browser accepts it.
if (substr_count($_SERVER['HTTP_ACCEPT_ENCODING'], 'gzip')) ob_start("ob_gzhandler"); else ob_start();
/**
 *      The Leginon software is Copyright under 
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://leginon.org
 *
 *      Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

// IF valueS SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadRecon();
} else {
	// Create the form page
	createUploadReconForm();
}

function createUploadReconForm( $extra=false, $title='UploadRecon.py Launcher', $heading='Upload Reconstruction Results' ) 
{
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
	
	if (!$jobId) $extra = "ERROR: No prepared refine job id was selected";

	$javafunctions .= writeJavaPopupFunctions('appion');  

	$particle = new particledata();
	
	// ------------Get Job info, model and stack info-------------
	// Get the selected refinement job info from the database 
	if ( $jobId ) {
		// get name of job from apAppionJobData and lookup ApPrepRefineData based on that
		$jobdata = $particle->getJobInfoFromId( $jobId );
		$jobfile = $jobdata['name'];
		
		// remove any extentions to the name like .job
		$pos = strpos($jobfile, ".");
		if ($pos !== false) {
			$runname = substr($jobfile, 0, $pos);
		} else {
			$runname = $jobfile;
		}
		
		$refinejobdatas = $particle->getPreparedRefineJobs(false, false, true, $runname );
		$refjobdata 	= $refinejobdatas[0];
		$refineID 		= $refjobdata['DEF_id'];
		$method 		= $refjobdata['method'];
		$rundir 		= $refjobdata['path'];
		$outdir 		= preg_replace('%'.$runname."$%", "", $rundir); 
		$description 	= $refjobdata['description'];
		$refinestackid 	= $refjobdata['REF|ApStackData|stack'];
		$reconstackid 	= $refjobdata['REF|ApStackData|reconstack'];
	
		// Get refine stack preparation parameters
		// TODO: this may need to be modified if we have multiple stacks???
		$stacks		= $particle->getPreparedRefineStackData($refineID);
		$lastPart 	= $stacks[0][last_part];
		$lp 		= $stacks[0][lowpass];
		$hp 		= $stacks[0][highpass];
		$bin 		= $stacks[0][bin];	
		$apix 		= $stacks[0][apix];	
		$cs 		= $stacks[0][cs];	
		$boxsize 	= $stacks[0][boxsize];	
		$stackfilename = $stacks[0][filename]; 
		
		// Get initial models
		$models = $particle->getModelsFromRefineID( $refineID );
		
		// Create lists of model names and ids for the summary tables and command
		foreach( $models as $model ) {
			$modelNames .= $model['filename'].",";
			$modelIds   .= $model['DEF_id'].",";			
		}
		$modelNames = trim($modelNames, ",");
		$modelIds   = trim($modelIds, ",");
		$modelid	= $models[0]['DEF_id']; // only display info for the first model
		
		if (file_exists($rundir.'/classes_coran.1.hed')) {
			$method='EMAN/SpiCoran';
		}		
	}	

	$projectId = getProjectId();

	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:

	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	
	echo "<form name='viewerform' method='post' action='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	
	if (!empty($sessioninfo) && !$jobId) {
		$rundir=getBaseAppionPath($sessioninfo).'/recon/';
	}

	echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	
	// Set any existing parameters in form
	$method = ($_POST['package']) ? $_POST['package'] : $method;
	$contour = ($_POST['contour']) ? $_POST['contour'] : '2.0';
	$mass = ($_POST['mass']) ? $_POST['mass'] : '';
	$zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.0';
	$filter = ($_POST['filter']) ? $_POST['filter'] : '';
	$runname = ($_POST['runname']) ? $_POST['runname'] : $runname;
	$reconpath = ($_POST['reconpath']) ? $_POST['reconpath'] : $rundir;
	$description = $_POST['description'] ? $_POST['description'] : $description;
	$itertype = ($_POST['itertype']) ? $_POST['itertype'] : "all";
	$iteration = $_POST['iteration'];
	$startiteration = $_POST['startiteration'];
	$enditeration = $_POST['enditeration'];
	$apix = $_POST['apix'] ? $_POST['apix'] : $apix;
	$boxsize = $_POST['boxsize'] ? $_POST['boxsize'] : $boxsize;

	echo "<input type='hidden' name='boxsize' value='$boxsize'>\n";
	echo "<input type='hidden' name='apix' value='$apix'>\n";
	
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
		echo "<input type='text' name='runname' value='$runname' size='50'>";
	echo "</td></tr>\n";

	echo "<tr><td>\n";
		echo "<b>Recon Directory:</b>\n";
	echo "</td><td>\n";
		echo "<input type='text' name='reconpath' value='$reconpath' size='50'/>";

	// Stack Info
	echo "<tr><td colspan='2'>\n";
	if ($jobId) {
		echo "<input type='hidden' name='stackid' value='$refinestackid'>\n";
		echo stacksummarytable($refinestackid, $mini=true);
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
	echo "<b>Iterations to upload:</b><br/>";
	echo "<input type='radio' name='itertype' value='all' ";
	if ($_POST['itertype'] == 'all' || !$_POST['itertype']) echo "checked";
	echo ">";
	echo "Upload all iterations<br/>";
	echo "\n";
	echo "<input type='radio' name='itertype' value='one' ";
	if ($_POST['itertype'] == 'one') echo "checked";
	echo ">";
	echo "Upload only iteration ";
	echo "<input type='text' name='iteration' value='$iteration' size='4'/><br />";
	echo "\n";
	echo "<input type='radio' name='itertype' value='range' ";
	if ($_POST['itertype'] == 'range') echo "checked";
	echo ">";
	echo "Start with iteration <input type='text' name='startiteration' value='$startiteration' size='4'/>";
	echo "End early with iteration </b><input type='text' name='enditeration' value='$enditeration' size='4'/><br/>";
	echo "\n";
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
		echo "$method<input type='hidden' name='package' value='$method'><br/>\n";
		echo "Type: '".$packages[$method]['description']."'<br/>\n";
		echo "<br/>\n";
	} else {
		echo "Process Used:
				<select name='package'> ";
		foreach ($packages as $p) {
			echo "<option value='$p[setting]'";
			// select previously set package on resubmit
			if ($p['setting']==$method) echo " SELECTED";
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

	// Our methods have been postpended with the word "recon"
	// remove it so our references show up correctly.
	$refType = str_replace("recon", "", $method);
	echo showReference( $refType );

	processing_footer();
	exit;
}

function runUploadRecon() {
	/* *******************
	PART 1: Get variables
	******************** */
	// parse params
	$jobId=$_GET['jobId'];
	$description=$_POST['description'];
	$contour=$_POST['contour'];
	$mass=$_POST['mass'];
	$zoom=$_POST['zoom'];
	$filter=$_POST['filter'];
	$itertype=$_POST['itertype'];
	$iteration=$_POST['iteration'];
	$startiteration=$_POST['startiteration'];
	$enditeration=$_POST['enditeration'];
	$runname=$_POST['runname'];
	$description=$_POST['description'];
	$method=$_POST['package'];
	$modelid = $_POST['modelid'];
	$boxsize = $_POST['boxsize'];
	$apix = $_POST['apix'];
	
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a recon run name was entered
	if (!$runname)
		createUploadReconForm("<B>ERROR:</B> Enter a name of the recon run");
	
	//make sure a stack was chosen
	if ($_POST['stackid'])
		$refinestackid = $_POST['stackid'];
	elseif ($_POST['stackval'])
		list($refinestackid, $apix, $boxsize) = preg_split('%\|--\|%',$_POST['stackval']);
	else
		createUploadReconForm("<B>ERROR:</B> Select the image stack used");

	//make sure a model was chosen
	if (!$modelid)
		createUploadReconForm("<B>ERROR:</B> Select the initial model used");
	
	//make sure a package was chosen
	if (!$method)
		createUploadReconForm("<B>ERROR:</B> Enter the reconstruction process used");

	//make sure a description was entered
	if (!$description)
		createUploadReconForm("<B>ERROR:</B> Enter a description of the reconstruction");

	//make sure a package was chosen
	if ($_POST['reconpath'] && $_POST['reconpath']!="./") {
		$reconpath = $_POST['reconpath'];
		if (substr($reconpath,-1,1)!='/') $reconpath.='/';
		//$runpath = $reconpath.$runname."";
		$runpath = $reconpath."recon/";
		// If this ran remotely, the recon folder may not exist because the tar file still needs to be unpacked.
		//if (!file_exists($runpath)) createUploadReconForm("<B>ERROR:</B> Could not find recon run directory: ".$runpath);
	}
	else {
		$runpath = "./";
	}
	

//	$particle = new particledata();
//	//make sure specific result file is present
//	if ($jobId) {
//		$jobinfo = $particle->getJobInfoFromId($jobId);
//		$fileerror = checkRequiredFileError($jobinfo['appath'],'resolution.txt'); 
//	} else {
//		$fileerror = checkRequiredFileError($runpath,'resolution.txt'); 
//	}
//	$fileerror = checkRequiredFileError($runpath,'resolution.txt');
//	if ($fileerror) createUploadReconForm($fileerror);

	//make sure the user only want one iteration to be uploaded
	if (is_numeric($iteration)) {
		if ($itertype!='one') createUploadReconForm("<B>ERROR:</B> Select the radio button if you really want to upload only one iteration");
		if ($iteration < 1) createUploadReconForm("<B>ERROR:</B> iteration number must be positive");
	}
	else {
		if ($itertype=='one') createUploadReconForm("<B>ERROR:</B> Enter the iteration number if you really want to upload only one iteration");
	}

	//make sure the user wants to start iteration from the middle
	if (is_numeric($startiteration)) {
		if ($itertype!='range') createUploadReconForm("<B>ERROR:</B> Select the radio button if you really want to upload a limited range of iteration");
		if ($startiteration < 1) createUploadReconForm("<B>ERROR:</B> Start iteration $startiteration must be positive integer");
	}

	//make sure the user wants to end iteration early
	if (is_numeric($enditeration)) {
		if ($itertype!='range') createUploadReconForm("<B>ERROR:</B> Select the radio button if you really want to upload a limited range of iteration");
		if ($enditeration < 1) createUploadReconForm("<B>ERROR:</B> End iteration $enditeration must be positive integer");
		if (is_numeric($startiteration) && $enditeration < $startiteration) createUploadReconForm("<B>ERROR:</B> Start Iteration must be smaller than or equal to End Iteration");
	}
	if ($itertype=='range' && !is_numeric($startiteration) && !is_numeric($enditeration)) {
		createUploadReconForm("<B>ERROR: </B> Enter either or both start/end iteration number if you really want to upload a limited range of iteration ");
	}
	
	/* *******************
	PART 3: Create program command
	******************** */

	switch ( $method ) {
		case "emanrecon":
			$command = "uploadEMANRefine.py ";
			// TODO: get Dmitry to fix this, should not be hardcoded.
			$command .= "--numberOfReferences=1 ";
			break;
		case "xmipprecon":
			$command = "uploadXmippRefine.py ";
			// TODO: get Dmitry to fix this, should not be hardcoded.
			$command .= "--numberOfReferences=1 ";
			break;
		case "xmippml3d":
			$command = "uploadXmippML3DRefine.py ";
			break;
		case "frealignrecon":
			$command = "uploadFrealignRefine.py ";
			break;
		case "relionrecon":
			$command = "uploadRelionRefine.py ";
			$command .= "--numberOfReferences=1 ";
			break;
		default:
			$command = "uploadExternalRefine.py ";
			break;
	}
	$command.="--runname=$runname ";
	$command.="--stackid=$refinestackid ";
	$command.="--modelid=$modelid ";
	// TODO: use the correct method
	//$command.="--package=$method ";
	//$command.="--package=EMAN ";
	//if (!$jobId) $command.="--rundir=$runpath ";
	//if ($jobId) $command.="--rundir=$runpath ";
	// The parameter --jobid is normally used for current job and will be stripped off by apAgent
	// Therefore, --refinejobid is used to keep it unique
	if ($jobId) $command.="--refinejobid=$jobId ";
	if ($contour) $command.="--contour=$contour ";
	if ($mass) $command.="--mass=$mass ";
	if ($zoom) $command.="--zoom=$zoom ";
	if ($filter) $command.="--snapfilter=$filter ";
	if ($itertype == 'range') {
		$numiter = ($enditeration-$startiteration)+1;
		$command.="--numiter=$numiter ";
		$iterlist = $startiteration;
		$iter = $startiteration;
		while ($iter < $enditeration) {
			$iter = $iter+1;
			$iterlist.=",$iter";
		}
		$command.="--uploadIterations=$iterlist ";
	}
	if ($itertype == 'one') {
		$command.="--numiter=1 ";
		$command.="--uploadIterations=$iteration ";
	}
	$command.="--description=\"$description\" ";
	$command.="--box=$boxsize ";
	$command.="--apix=$apix ";
	
	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	// Our methods have been postpended with the word "recon"
	// remove it so our references show up correctly.
	$refType = str_replace("recon", "", $method);
	$headinfo .= showReference( $refType );
	
	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'uploadrecon', 1);

	// if error display them
	if ($errors)
		createUploadReconForm($errors);
	exit;
}

?>
