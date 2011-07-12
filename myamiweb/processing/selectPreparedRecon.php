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

// include each refinement type file
// todo: autodiscovery
require_once "inc/forms/xmippRefineForm.inc";
require_once "inc/forms/frealignRefineForm.inc";
require_once "inc/forms/emanRefineForm.inc";
require_once "inc/forms/xmippML3DRefineForm.inc";
require_once "inc/forms/runParametersForm.inc";
require_once "inc/forms/clusterParamsForm.inc";
require_once "inc/forms/stackPrepForm.inc";



$selectedcluster=$CLUSTER_CONFIGS[0];
if ($_POST['changecluster']) {
	$selectedcluster = $_POST['changecluster'];
} elseif ( $_POST['cluster'] ) {
	$selectedcluster = $_POST['cluster'];
}
$selectedcluster=strtolower($selectedcluster);
@include_once $selectedcluster.".php";

/*
******************************************
******************************************
******************************************
*/

if ($_POST['process'])
	createCommand(); // submit job
elseif ($_POST['jobid'])
	jobForm(); // fill out job form
else
	selectRefineJob(); // select a prepared frealign job

/*
******************************************
******************************************
******************************************
*/

function selectRefineJob($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	processing_header("Refinement Job Launcher","Refinement Job Launcher", $javafunc);
	if ($expId) {
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		exit;
	}
	$particle = new particledata();

	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='selectreconform' method='POST' ACTION='$formAction'>\n";

	// get prepared refine jobs
	$rawrefinejobs = $particle->getPreparedRefineJobs();
	
	// print jobs with radio button
	if (!$rawrefinejobs) {
		echo "<font color='#CC3333' size='+2'>No prepared refinement jobs found</font>\n";
		exit;
	} 

	// check if jobs have associated cluster jobs
	$refinejobs = array();
	foreach ($rawrefinejobs as $refinejob) {
		$refinerun = $particle->getClusterJobByTypeAndPath('runrefine', $refinejob['path']);
		if (!$refinerun)
			$refinejobs[] = $refinejob;
	}

	// print jobs with radio button
	if (!$refinejobs) {
		echo "<font color='#CC3333' size='+2'>No prepared refinement jobs available</font>\n";
		exit;
	} 

	echo "<table class='tableborder' border='1'>\n";
	foreach ($refinejobs as $refinejob) {
		echo "<tr><td>\n";
		$id = $refinejob['DEF_id'];
		if ($refinejob['hidden'] != 1) {
			echo "<input type='radio' NAME='jobid' value='$id' ";
			echo "><br/>\n";
			echo"Launch<br/>Job\n";
		}
		echo "</td><td>\n";

		echo prepRefineTable($refinejob['DEF_id']);

		echo "</td></tr>\n";
	}
	echo "</table>\n\n";

	echo "<P><input type='SUBMIT' NAME='submitprepared' VALUE='Use this prepared job'></FORM>\n";

	processing_footer();
	exit;
};

/*
******************************************
******************************************
******************************************
*/
// based on the type of refinement the user has selected,
// create the proper form type here. If a new type is added to
// Appion, it's form class should be included in this file
// and it should be added to this function. No other modifications
// to this file should be necessary.
function createSelectedRefineForm( $method, $stackId='', $modelArray='', $parentFormName=''  )
{
	// TODO: need to decide which naming convention to use.
	switch ( $method ) {
		case eman:
		case emanrecon:
			$selectedRefineForm = new EmanRefineForm( $method, $stackId, $modelArray, $parentFormName );
			break;
		case frealign:
		case frealignrecon:
			$selectedRefineForm = new FrealignRefineForm( $method, $stackId, $modelArray, $parentFormName );
			break;
		case xmipp:
		case xmipprecon:
			$selectedRefineForm = new XmippRefineForm( $method, $stackId, $modelArray, $parentFormName );
			break;
		case xmippml3d:
		case xmippml3drecon:
			$selectedRefineForm = new XmippML3DRefineForm( $method, $stackId, $modelArray, $parentFormName );
			break;
		default:
			Throw new Exception("Error: Not Implemented - There is no RefineForm class avaialable for method: $method"); 
	}		
	
	return $selectedRefineForm;
}

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

	if (!$jobid)
		selectRefineJob("ERROR: No prepared refine job id was selected");
	if (!($user && $pass))
		selectRefineJob("ERROR: You are not logged in");
	
	// Get the selected refinement job info from the database 
	$particle 	= new particledata();
	$jobdatas 		= $particle->getPreparedRefineJobs($jobid);
	$jobdata 		= $jobdatas[0];
	$refineID 		= $jobdata['DEF_id'];
	$method 		= $jobdata['method'];
	$rundir 		= $jobdata['path'];
	$runname 		= $jobdata['name'];
	$outdir 		= ereg_replace($runname."$", "", $rundir);
	$description 	= $jobdata['description'];

	// prepare stack values
	$refinestackid 		= $jobdata['REF|ApStackData|stack'];
	$refinestackdata 	= $particle->getStackParams($refinestackid);
	$numpart			= $particle->getNumStackParticles($refinestackid);
	$apix 				= $particle->getStackPixelSizeFromStackId($refinestackid)*1e10;
	$boxsize 			= $refinestackdata['boxsize'];
	$refinestackvals 	= "$refinestackid|--|$apix|--|$boxsize|--|$numpart|--|$refinestackdata[path]|--|$refinestackdata[name]";
	$reconstackid 		= $jobdata['REF|ApStackData|reconstack'];
	if ($reconstackid) {
		$reconstackdata = $particle->getStackParams($reconstackid);
		$reconstackvals = "$reconstackid|--|$apix|--|$boxsize|--|$numpart|--|$reconstackdata[path]|--|$reconstackdata[name]";
	}

	
	// prepare model values
	$models = $particle->getModelsFromRefineID( $refineID );
	
	foreach( $models as $model ) {
		$modelNames .= $model['name'].",";
		$modelIds .= $model['DEF_id'].",";
	}
	$modelNames = trim($modelNames, ",");
	$modelIds = trim($modelIds, ",");
	
	$modelid 	= $jobdata['REF|ApInitialModelData|model'];
	$modeldata 	= $particle->getInitModelInfo($modelid);
	$symdata 	= $particle->getSymInfo($modeldata['REF|ApSymmetryData|symmetry']);
	$modelvals 	= "$modelid|--|$modeldata[path]|--|$modeldata[name]|--|$modeldata[boxsize]|--|$symdata[symmetry]";
	// Hack: we must assign the POST values
	$_POST['model'] = $modelvals;
	$_POST['stackval'] = $refinestackvals;

	// set remote path
	$leginondata = new leginondata();
	$sessiondata = $leginondata->getSessionInfo($expId);
	$sessionpath = $sessiondata['Image path'];
	ereg("(.*)leginon(.*)rawdata", $sessionpath, $reg_match);
	$rootpath = "appion".$reg_match[2]."recon/";
	$sessionpath = $reg_match[1].$rootpath;
	// TODO: if error, check cluster config file name matches config.php
	$clusterdata->set_rootpath($rootpath);
	$clusterdata->post_data();
	
	// Instantiate the class that defines the forms for the selected method of refinement.
	$modelArray[] = array( 'name'=>"model_1", 'id'=>$modelid );
	$formName = "frealignjob";
	$selectedRefineForm = createSelectedRefineForm( $method, $refinestackid, $modelArray, $formName );

	$javafunc .= $selectedRefineForm->setDefaults();
	$javafunc .= $selectedRefineForm->additionalJavaScript();
	// TODO: does the order of these make a difference??
	$javafunc .= writeJavaPopupFunctions('appion');
	$javafunc .= writeJavaPopupFunctions('frealign');
	$javafunc .= writeJavaPopupFunctions('eman');
	
	processing_header("Refinement Job Launcher","Refinement Job Launcher", $javafunc);

	// write out errors, if any came up:
	if ($extra)
		$html.= "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
		
	// Begin Form
	$html.= "<form name='$formName' method='post' action='$formaction'><br />\n";
	
	// Post hidden values
	$html.= "<input type='hidden' name='clustermemo' value='$selectedcluster'>\n";
	$html.= "<input type='hidden' name='jobid' value='$jobid'>\n";
	$html.= "<input type='hidden' NAME='model' value='$modelvals'>\n";
	$html.= "<input type='hidden' NAME='refinestackvals' value='$refinestackvals'>\n";
	$html.= "<input type='hidden' NAME='stackval' value='$refinestackvals'>\n";
	$html.= "<input type='hidden' NAME='reconstackvals' value='$reconstackvals'>\n";
	$html.= "<input type='hidden' NAME='modelnames' value='$modelNames'>\n";
	$html.= "<input type='hidden' NAME='modelids' value='$modelIds'>\n";
	$html.= "<input type='hidden' NAME='method' value='$method'>\n";
	
	// Start Table
	$html.= "<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>";	
	
	// --- Row 1 --- 
	// Add processing run parameters
	$html.= "<tr>";
	$html.= "<td VALIGN='TOP' class='tablebg' COLSPAN='2'>";
	$runParamsForm = new RunParametersForm( $runname, $outdir, $description );
	$html.= $runParamsForm->generateReport();
	$html.= "</td>";
	$html.= "</tr>";
	
	// --- Row 2 ---   
	// Add cluster parameter form
	$html.= "<tr>";
	$html.= "<td VALIGN='TOP' COLSPAN='2' >";
	$html.= "<H4 style='align=\'center\' >Processing Host Parameters</H4><hr />";
	$clusterParamsForm = new ClusterParamsForm();
	$html.= $clusterParamsForm->generateForm();
	$html.= "</td>";
	$html.= "</tr>";
		
	// --- Row 3 ---  
	// Display the heading
	$html.= "<tr>";
	$html.= "<td COLSPAN='2'>";
	$html.= "<H4 style='align=\'center\' >Refinement Parameters</H4><hr />";
	$html.= "</td>";
	$html.= "</tr>";
	
	// --- Row 4 --- 
	// Add refinement parameters
	$html.= "<tr>";
	
	// Add the parameters that apply to all methods of reconstruction
	$html.= "<td>"; // row 4 column 1
	$html.= $selectedRefineForm->generalParamForm();	
	$html.= "</td>";
	
	// Add parameters specific to the refine method selected
	$html.= "<td class='tablebg'>\n"; // Row 4 col 2
	$html.= $selectedRefineForm->advancedParamForm();
	$html.= "</td>";
	
	// --- Row 5 --- 
	// Add submit button
	$html.= "<tr>";
	$html.= "<td COLSPAN='2' ALIGN='center'><hr>";
	$html.= "<br/>\n";
	$html.= getSubmitForm("Run Refinement");
	$html.= "</td>";
	$html.= "</tr>";
	
	// End Table
	$html.= "</table>\n";	
	
	$html.= "<br />";
	
	// Add stack and model summary tables
	//$html.= "StackID: $stackid -- ModelID: $modelid<br/>\n";
	$html.= "<table class='tablebubble'><tr>\n";
	// Add stack prep parameters
	$html.= "<td class='tablebg'>";
	// TODO: this may need to be modified if we have multiple stacks???
	// Get stack preparation parameters
	$stackdatas	= $particle->getPreparedRefineStackData($refineID);
	$lastPart 	= $stackdatas[0][last_part];
	$lp 		= $stackdatas[0][lowpass];
	$hp 		= $stackdatas[0][highpass];
	$bin 		= $stackdatas[0][bin];
	$stackPrepForm = new stackPrepForm( $lastPart,$lp,$hp,$bin );
	$html.= $stackPrepForm->generateReport( "Stack Prep Params", 544 );
	$html.= "</td>";
	
	$html.= "<td>";
	$html.= stacksummarytable($refinestackid, true);
	if ($reconstackid) {
		$html.= "</td></tr><tr><td>\n";
		$html.= stacksummarytable($reconstackid, true);
	}
	$html.= "</td></tr>";
	
	// Add each model to the table
	$models = explode(",", $modelIds);
	foreach ($models as $modelid) {
		$html.= "<tr><td class='tablebg'></td><td>\n";
		$html.= modelsummarytable($modelid, true);
		$html.= "</td></tr>";
	}
	
	// end stack/model summary table
	$html.= "</table>\n";

	// Add reference for selected refinement method
	$html.= showReference( $method );

	// end form
	$html.="</form><br/>\n";
	
	echo $html;
	
	processing_footer();
	exit;
}
/*
******************************************
******************************************
******************************************
*/
function createCommand ($extra=False) 
{
	/* ***********************************
	 PART 1: Get variables from POST array and validate
	 ************************************* */		
	// verify processing host parameters
	$clusterParamForm = new ClusterParamsForm();
	$errorMsg .= $clusterParamForm->validate( $_POST );
	
	// verify the parameters for the selected method of refinement.
	$method = $_POST['method'];
	$selectedRefineForm = createSelectedRefineForm( $method );
	$errorMsg .= $selectedRefineForm->validate( $_POST );
	
	// reload the form with the error messages
	if ( $errorMsg ) jobForm( $errorMsg );
	
	/* *******************
	 PART 2: Copy any needed files to the cluster
	 ******************** */
	copyFilesToCluster();	
	
	/* *******************
	 PART 3: Create program command
	 ******************** */
	// All jobs are sent to the cluster agent
	$command = "runjob.py ";
	
	// Instantiate the class that defines the forms for the selected method of refinement.
	$command .= $selectedRefineForm->buildCommand( $_POST );
	
	// Add the model filenames to the command
	$command .= "--modelnames=".$_POST['modelnames']." "; 
	
	// add the stack filename to the command
	$stackinfo 	= explode('|--|',$_POST['stackval']);
	$stackName	= $stackinfo[5];
	$command .= "--stackname=".$stackName." ";
	
	// collect processing run parameters
	$runParametersForm = new RunParametersForm();
	$command .= $runParametersForm->buildCommand( $_POST );
		
	// collect processing host parameters
	$command .= $clusterParamForm->buildCommand( $_POST );
	
	
	/* *******************
	 PART 4: Create header info, i.e., references
	 ******************** */
	// Add reference to top of the page
	$headinfo .= showReference( $method );

	/* *******************
	 PART 5: Show or Run Command
	 ******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'runrefine', $nproc);
	// if error display them
	if ($errors) $errorCallbackFunc($errors);
	
};

function copyFilesToCluster()
{
	global $clusterdata;
	$clusterdata->post_data();
	//var_dump($clusterdata);

	$host = $clusterdata->hostname;
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	if (!($user && $pass))
		jobForm("<B>ERROR:</B> Enter a user name and password");

	$clusterpath = $clusterdata->get_path();
	$clusterpath = formatEndPath($clusterpath);
	
	$runname = $_POST['runname'];
	$outdir = $_POST['outdir'].$runname;
	$clusterpath = $clusterpath.$runname;
	
	
	// create appion directory & copy list of files to copy
	// TODO: where exactly should files be copied to?
	$cmd = "mkdir -p $clusterpath;\n";
	
	$rvalue = exec_over_ssh($host, $user, $pass, $cmd, True);
	if ($rvalue === false ){
		$errMsg = "Error: Could not create run directory on $host: ";
		$errMsg .= pconnError();
		jobForm("<B>ERROR:</B> $errMsg");
		//echo "<hr>\n<font color='#CC3333' size='+1'>$errMsg</font>\n";
		exit;
	} else {
		// TODO: log this to a file
		//echo "<hr>\n<font color='#CC3333' size='+1'>Created run directory $clusterpath on $host.</font>\n";
	}
	
	// Get list of files to copy
	$files_to_remote_host = $outdir."/files_to_remote_host";
	$files = file_get_contents($files_to_remote_host);
	
	// copy each listed file to the cluster	
	// files are separated by a new line charachter
	$fileList = explode( "\n", $files );
	
	// add the files_to_remote_host file to this list to be copied
	$fileList[] = $files_to_remote_host;
	
	foreach ( $fileList as $filepath ) {
		
		if ( !$filePath ) {
			continue;
		}
		
		// get filename from path
	    $filename = basename($filepath);

	    // set path to copy the file to
	    $remoteFilePath = "$clusterpath/$filename";
	    	    
	    // copy the file to the cluster
	    if ( $filepath != $remoteFilePath ) {
			copyFile($host, $user, $pass, $filepath, $remoteFilePath);
	    } else {
	    	// TODO: log this to a file
			//echo "<hr>\n<font color='#CC3333' size='+1'>No need to copy file $filepath to $remoteFilePath.</font>\n";
	    }
	}	
}

function copyFile( $host, $user, $pass, $filepath, $remoteFilePath )
{	
	$rvalue = scp($host, $user, $pass, $filepath, $remoteFilePath);	
	if (!$rvalue) {
		$errMsg = "Error: Copying file ($filepath) to $remoteFilePath on $host failed: ";
		$errMsg .= pconnError();
		jobForm("<B>ERROR:</B> $errMsg");
		//echo "<hr>\n<font color='#CC3333' size='+1'>$errMsg</font>\n";
		//exit;
	} else {
		// TODO: log this to a file
		//echo "<hr>\n<font color='#CC3333' size='+1'>Copied $filepath to $remoteFilePath on $host.</font>\n";
	}
}

// TODO: this is here and in the cluster config file. Yuk.
function formatEndPath($path) {
	if (substr($path,-1,1)!='/')
		$path.='/';
	return $path;
}

?>
