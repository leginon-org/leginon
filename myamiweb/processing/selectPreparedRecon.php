<?php
// compress this file if the browser accepts it.
if (substr_count($_SERVER['HTTP_ACCEPT_ENCODING'], 'gzip')) ob_start("ob_gzhandler"); else ob_start();
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
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";

// include each refinement type file
// todo: autodiscovery
require_once "inc/forms/xmippRefineForm.inc";
require_once "inc/forms/relionRefineForm.inc";
require_once "inc/forms/frealignRefineForm.inc";
require_once "inc/forms/emanRefineForm.inc";
require_once "inc/forms/xmippML3DRefineForm.inc";
require_once "inc/forms/runParametersForm.inc";
require_once "inc/forms/clusterParamsForm.inc";
require_once "inc/forms/stackPrepForm.inc";
require_once "inc/refineJobsSingleModel.inc";
require_once "inc/refineJobsMultiModel.inc";

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
		$type = $_GET['type'];
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId&type=$type";
	} else {
		exit;
	}
	
	// get prepared refine jobs
	if ( $type == "single" ) 
	{
		$refinementJobs = new RefineJobsSingleModel($expId);
	} else {
		$refinementJobs = new RefineJobsMultiModel($expId);
	}	
	$refinejobs = $refinementJobs->getRefinesReadyToRun();
	//echo "FINAL<br/>";
	//print_r($refinejobs);
	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='selectreconform' method='POST' ACTION='$formAction'>\n";

	// print jobs with radio button
	if (!$refinejobs) {
		echo "<font color='#CC3333' size='+2'>No prepared refinement jobs available</font>\n";
		exit;
	} 

	echo "<P><input type='SUBMIT' NAME='submitprepared' VALUE='Use this prepared job'>\n";
	
	echo "<table class='tableborder' border='1'>\n";
	foreach ($refinejobs as $refinejob) {
		echo "<tr><td>\n";
		//$id = $refinejob['DEF_id'];
		$id = $refinejob['REF|ApAppionJobData|job'];
		if ($refinejob['hidden'] != 1) {
			echo "<input type='radio' NAME='jobid' value='$id' ";
			echo "><br />\n";
			echo"Launch<br />Job\n";
		}
		echo "</td><td>\n";

		echo prepRefineTable($id);

		echo "</td></tr>\n";
	}
	echo "</table>\n\n";

	echo "<P><input type='SUBMIT' NAME='submitprepared' VALUE='Use this prepared job'></form>\n";

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
function createSelectedRefineForm( $method, $stacks='', $models='' )
{
	// TODO: need to decide which naming convention to use.
	switch ( $method ) {
		case eman:
		case emanrecon:
			$selectedRefineForm = new EmanRefineForm( $method, $stacks, $models );
			break;
		case frealign:
		case frealignrecon:
			$selectedRefineForm = new FrealignRefineForm( $method, $stacks, $models );
			break;
		case xmipp:
		case xmipprecon:
			$selectedRefineForm = new XmippRefineForm( $method, $stacks, $models );
			break;
		case relionrecon:
			$selectedRefineForm = new RelionRefineForm( $method, $stacks, $models );
			break;
		case xmippml3d:
		case xmippml3drecon:
			$selectedRefineForm = new XmippML3DRefineForm( $method, $stacks, $models );
			break;
		default:
			Throw new Exception("Error: Not Implemented - There is no RefineForm class avaialable for method: $method"); 
	}		
	
	return $selectedRefineForm;
}

function jobForm($extra=false) 
{	
	$expId = $_GET['expId'];
	if ($expId) {
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		exit;
	}
	
	$user 	= $_SESSION['username'];
	$pass 	= $_SESSION['password'];
	$jobid 	= $_POST['jobid'];

	if (!$jobid)
		selectRefineJob("ERROR: No prepared refine job id was selected");
	
	// Get the selected refinement job info from the database 
	$particle 		= new particledata();
	$jobdatas 		= $particle->getPreparedRefineJobs($jobid);
	$jobdata 		= $jobdatas[0];
	$refineID 		= $jobdata['DEF_id'];
	$method 		= $jobdata['method'];
	$rundir 		= $jobdata['path'];
	$runname 		= $jobdata['name'];
	$outdir 		= ereg_replace($runname."$", "", $rundir);
	$description 	= $jobdata['description'];
	$refinestackid 	= $jobdata['REF|ApStackData|stack'];
	$reconstackid 	= $jobdata['REF|ApStackData|reconstack'];

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
	$phaseflipped 	= $stacks[0][phaseflipped];	
	$stackfilename  = $stacks[0][filename]; 
	$pstackid = $stacks[0]['parent_id'];
	# camera physical pixel size is in meters, dstep is in micron	
	$cam_phys_psize = $particle->getStackCameraPhysicalPixelSize ($pstackid);
	$dstep = $cam_phys_psize*1e6;
	for ($i=0; $i < count($stacks); $i++) $stacks[$i]['dstep'] = $dstep;

	// Get the Kv, which is the high tension divided by 1000.
	$hightension = $particle->getHighTensionFromSessionId( $expId );
	$kv = $hightension/1000;
	
	// Get initial models
	$models = $particle->getModelsFromRefineID( $refineID );
	
	// Create lists of model names and ids for the summary tables and command
	foreach( $models as $model ) {
		$modelNames .= $model['filename'].",";
		$modelIds   .= $model['DEF_id'].",";
	}
	$modelNames = trim($modelNames, ",");
	$modelIds   = trim($modelIds, ",");
		
	// Instantiate the class that defines the forms for the selected method of refinement.
	$selectedRefineForm = createSelectedRefineForm( $method, $stacks, $models );

	$javafunc .= $selectedRefineForm->setDefaults();
	$javafunc .= $selectedRefineForm->additionalJavaScript();
	$javafunc .= writeJavaPopupFunctions();
	
	processing_header("Refinement Job Launcher","Refinement Job Launcher", $javafunc);

	// write out errors, if any came up:
	if ($extra)
		$html.= "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
		
	// Begin Form
	$html.= "<form name='frealignjob' method='post' action='$formaction'><br />\n";
	
	// Post hidden values
	$html.= "<input type='hidden' name='jobid' value='$jobid'>\n";
	$html.= "<input type='hidden' NAME='modelnames' value='$modelNames'>\n";
	$html.= "<input type='hidden' NAME='modelids' value='$modelIds'>\n";
	$html.= "<input type='hidden' NAME='method' value='$method'>\n";
	$html.= "<input type='hidden' NAME='stackfilename' value='".$stackfilename."'>\n";
	$html.= "<input type='hidden' NAME='apix' value='".$apix."'>\n";
	$html.= "<input type='hidden' NAME='cs' value='".$cs."'>\n";
	$html.= "<input type='hidden' NAME='boxsize' value='".$boxsize."'>\n";
	$html.= "<input type='hidden' NAME='phaseflipped' value='".$phaseflipped."'>\n";
	$html.= "<input type='hidden' NAME='lastpart' value='".$lastPart."'>\n";
	$html.= "<input type='hidden' NAME='kv' value='".$kv."'>\n";
	$html.= "<input type='hidden' NAME='dstep' value='".$dstep."'>\n";
	
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
	$clusterParamsForm = new ClusterParamsForm("recon");
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
	$html.= getSubmitForm("Run Refinement", false );
	$html.= "</td>";
	$html.= "</tr>";
	
	// End Table
	$html.= "</table>\n";	
	
	$html.= "<br />";
	
	// Add stack and model summary tables
	$html.= "<table class='tablebubble'><tr>\n";
	// Add stack prep parameters
	$html.= "<td class='tablebg'>";
	// TODO: this may need to be modified if we have multiple stacks???
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
	$html.= $selectedRefineForm->showReference();

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
	$stackName		= $_POST['stackfilename'];
	$apix 			= $_POST['apix'];	
	$cs 			= $_POST['cs'];	
	$kv 			= $_POST['kv'];	
	$boxsize 		= $_POST['boxsize'];	
	$phaseflipped 	= $_POST['phaseflipped'];	
	$totalPart  	= $_POST['lastpart'];
	// from the ClusterParamsForm
	$hostname   	= $_POST['processinghost'];
	$remoteoutdir	= $_POST['remoteoutdir'];
	
	// verify processing host parameters
	$clusterParamForm = new ClusterParamsForm("recon");
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
	$copyCommand = copyFilesToCluster( $hostname, $remoteoutdir );
	
	/* *******************
	 PART 3: Create program command
	 ******************** */
	// All jobs are sent to the cluster agent
	$command = "runJob.py ";
	
	// Add the jobtype to the command
	$command .= "--jobtype=".$method." ";
	
	// Instantiate the class that defines the forms for the selected method of refinement.
	$command .= $selectedRefineForm->buildCommand( $_POST );
	
	// Add the model filenames to the command
	$command .= "--modelnames=".$_POST['modelnames']." "; 
	
	// add the stack parameters to the command
	$command .= "--stackname=".$stackName." ";
	$command .= "--apix=".$apix." ";
	$command .= "--boxsize=".$boxsize." ";
	if ( $phaseflipped ) $command .= "--phaseflipped ";
	$command .= "--totalpart=".$totalPart." ";
	$command .= "--cs=".$cs." "; 
	$command .= "--kv=".$kv." "; 
	
	// collect processing run parameters
	$runParametersForm = new RunParametersForm();
	$command .= $runParametersForm->buildCommand( $_POST );
		
	// collect processing host parameters
	$command .= $clusterParamForm->buildCommand( $_POST );
	$command = $clusterParamForm->removeCommandFlag( $command, "processinghost" );
	$command = $clusterParamForm->removeCommandFlag( $command, "remoteoutdir" );
		
	/* *******************
	 PART 4: Create header info, i.e., references
	 ******************** */
	// Add reference to top of the page
	$headinfo .= $selectedRefineForm->showReference();
	$headinfo .= $copyCommand;
	$headinfo .= "<br />";

	/* *******************
	 PART 5: Show or Run Command
	 ******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, $method, $nproc);
	// if error display them
	if ($errors) jobForm($errors);
	
};

// TODO: the guts of this stuff should be moved 
// If the user is not logged in, or there is an error
// copying the files, this function returns a string with 
// directions for manual copy. If the copy is successful,
// this returns and empty string.
function copyFilesToCluster( $host, $directory )
{
	$copyNeededFlag		= false; // this becomes true if files actually need to be copied 
	$printCommandFlag 	= false; // this becomes true if we are unable to execute the copy
	$returnCmdString	= ""; // the commands the user needs to enter manually if auto copy fails
	$clusterpath		= $directory;
		
	// if the user is not logged in, we cannot execute the copy for them
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	if (!($user && $pass)) {
		$printCommandFlag = true;
	}

	$runname = $_POST['runname'];
	$rundir = $_POST['outdir'].$runname;
	$clusterpath = $clusterpath.$runname;
	
	// create appion directory & copy list of files to copy
	// TODO: where exactly should files be copied to?
	$mkdircmd = "mkdir -p $clusterpath;\n";
	
	if ( !$printCommandFlag ) {
		$rvalue = exec_over_ssh($host, $user, $pass, $mkdircmd, false);
		if ($rvalue === false ){
			// if the mkdir failed, display the commands to the user to run manually
			$printCommandFlag = true;
			$errMsg = "Error: Could not create run directory on $host: ";
			$errMsg .= pconnError();
			$returnCmdString .= "<B>ERROR</B> $errMsg <br /><br />";
			//echo "<hr>\n<font color='#CC3333' size='+1'>$errMsg</font>\n";
		} else {
			// TODO: log this to a file
			//echo "<hr>\n<font color='#CC3333' size='+1'>Created run directory $clusterpath on $host.</font>\n";
		}
	}
	
	// Get list of files to copy
	$files_to_remote_host = "files_to_remote_host";
	$files_to_remote_host_path = $rundir."/files_to_remote_host";
	if (!file_exists($files_to_remote_host_path)) {
		jobForm("<B>ERROR:</B> Failed to locate file ".$files_to_remote_host_path);
  	}
	
  	$files = file_get_contents($files_to_remote_host_path);
  	
  	if ( $files === false ) {
		jobForm("<B>ERROR:</B> Failed to read file ".$files_to_remote_host_path);
  	}
  		
	// copy each listed file to the cluster	
	// files are separated by a new line charachter
	$fileList = explode( "\n", $files );
	
	// add the files_to_remote_host file to this list to be copied
	$fileList[] = $files_to_remote_host;
	
	foreach ( $fileList as $filename ) {
		if ( !$filename ) {
			//echo "<hr>\n<font color='#CC3333' size='+1'>$filename not valid.</font>\n";
			continue;
		}
		
		// add the path to the current location of the file
		$filepath = $rundir."/".$filename;

	    // set path to copy the file to
	    $remoteFilePath = "$clusterpath/$filename";
	    	    
	    // copy the file to the cluster
	    if ( $filepath != $remoteFilePath ) {
	    	$copyNeededFlag = true;
	    	$cpycmd .= " cp $filepath $remoteFilePath; <br />";
	    	// if we have not had any errors above, try the copy
	    	if ( !$printCommandFlag ) {
	    		$rvalue = scp($host, $user, $pass, $filepath, $remoteFilePath);	
				if (!$rvalue) {
					// if there is an error with the copy, let the user know and display the manual commands
					$printCommandFlag = true;
					$errMsg = "Failed to copy file ($filepath) to $remoteFilePath on $host: ";
					$errMsg .= pconnError();
					$returnCmdString .= "<B>ERROR</B> $errMsg <br /><br />";
					//echo "<hr>\n<font color='#CC3333' size='+1'>$errMsg</font>\n";
				} else {
					// TODO: log this to a file
					//echo "<hr>\n<font color='#CC3333' size='+1'>Copied $filepath to $remoteFilePath on $host.</font>\n";
				}
	    	}
	    } else {
	    	// TODO: log this to a file
			//echo "<hr>\n<font color='#CC3333' size='+1'>No need to copy file $filepath to $remoteFilePath.</font>\n";
	    }
	}	
	
	// Build the return string if needed
	if ( $copyNeededFlag && $printCommandFlag ) {
		$returnCmdString .= "<b>You MUST manually execute the following commands (or similar) prior to running the refinement command:</b>";
		$returnCmdString .= "<br /><br />";
		$returnCmdString .= $mkdircmd;
		$returnCmdString .= "<br />";
		$returnCmdString .= $cpycmd;
	}
	
	return $returnCmdString;
}

?>
