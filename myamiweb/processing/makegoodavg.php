<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Display results for each iteration of a refinement
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
  
// --- check if reconstruction is specified

if ($_POST['process']) {
	/* *******************
	PART 1: Get variables
	******************** */
	$reconId=$_GET['reconId'];
	$refId=$_GET['refId'];
	$iter=$_GET['iter'];
	$mask=$_POST['mask'];
	$hard=$_POST['hard'];
	$sigma=$_POST['sigma'];
	$avgjump=$_POST['avgjump'];
	$stackname=$_POST['avgname'];
	$bpname=$_POST['bpname'];
	$zoom=$_POST['zoom'];
	$mass=$_POST['mass'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	if (!$stackname) createform('<b>ERROR:</b> Enter a name for new class average stack file');
	if (!$bpname) createform('<b>ERROR:</b> Enter a name for new 3d density file');
	if (!$mask) createform('<b>ERROR:</b> Enter a mask radius');
	if (!$hard) createform('<b>ERROR:</b> Enter a hard value');
	if ($avgjump=='') createform('<B>ERROR:</b> Enter a median euler jump');
	if (!$zoom) createform('<b>ERROR:</b> Enter a zoom value for snapshot');
	if (!$mass) createform('<b>ERROR:</b> Enter the estimated mass for the density');

	/* *******************
	PART 3: Create program command
	******************** */
	$command = "makegoodaverages.py ";
	$command.= "--reconid=$reconId ";
	$command.= "--iter=$iter ";
	$command.= "--mask=$mask ";
	$command.= "--hard=$hard ";
	$command.= "--stackname=$stackname ";
	$command.= "--make3d=$bpname ";
	$command.= "--zoom=$zoom ";
	$command.= "--mass=$mass ";
	if ($avgjump != '') $command.= "--avgjump=$avgjump ";
	if ($sigma) $command.= "--sigma=$sigma ";
	if ($_POST['commit']!='on') $command.= "--no-commit ";
	$command.= "--eotest ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	// Add reference to top of the page
	$headinfo .= appionRef(); // main appion ref

	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'makegoodavg', $nproc);
	// if error display them
	if ($errors)
		createform($errors);
	exit;
}

else createform();

function createform($extra=False) {
	$expId = $_GET['expId'];
	$reconId = $_GET['reconId'];
	$refId = $_GET['refId'];
	$iter = $_GET['iter'];

	$javascript=writeJavaPopupFunctions('appion');

	processing_header("Remove Eulers Jumpers", "Remove Euler Jumpers",$javascript);

	// write out errors, if any came up:
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
		
	$particle = new particledata();
	$refinfo = $particle->getRefinementRunInfo($reconId);
	// get iteration parameters for specified iteration:
	$paraminfo = $particle->getParamsFromRefinementDataId($refId);
	// print_r($paraminfo);
	$runname = getTimestring();
	$runname = "refine".$refId."_".$runname;

	$mask=($_POST['mask']) ? $_POST['mask'] : $paraminfo['mask'];
	$hard=($_POST['hard']) ? $_POST['hard'] : $paraminfo['EMAN_hard'];
	$sigma=($_POST['sigma']) ? $_POST['sigma'] : '';
	$avgjump=($_POST['avgjump']) ? $_POST['avgjump'] : '0';
	$avgname=($_POST['avgname']) ? $_POST['avgname'] : 'goodavgs.hed';
	$bpname=($_POST['bpname']) ? $_POST['bpname'] : 'threed.mrc';
	$runname=($_POST['runname']) ? $_POST['runname'] : $runname;
	$outdir=($_POST['outdir']) ? $_POST['outdir'] : $refinfo['path'].'/eulers';
	$zoom=($_POST['zoom']) ? $_POST['zoom'] : '';
	$mass=($_POST['mass']) ? $_POST['mass'] : '';
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	echo "<FORM NAME='postproc' METHOD='POST' ACTION='$formAction'>\n";
	echo "<TABLE cellpadding='5' BORDER=3 CLASS=tableborder>\n";
	echo "<TR>\n";
	echo "  <TD VALIGN='TOP'>\n";
	echo docpop('runname','Run Name:');
	echo "<br />\n";
	echo "  <input type='text' name='runname' size='25' value='$runname'>\n";
	echo "	<br />\n";
	echo "	New classes stack file name:<br />\n";
	echo "  <input type='text' name='avgname' size='25' value='$avgname'>\n";
	echo "	<br />\n";
	echo "	New 3d density file name:<br />\n";
	echo "  <input type='text' name='bpname' size='25' value='$bpname'>\n";
	echo "	<br />\n";
	echo docpop('outdir','Output directory:');
	echo "<br />\n";
	echo "  <input type='text' name='outdir' size='63' value='$outdir'>\n";
	echo " 	</td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "	<td class='tablebg'>\n";
	echo "  <input type='text' name='sigma' size='4' value='$sigma'>\n";
	echo docpop('sigma',"keep sigma level");
	echo " 	<br />\n";
	echo " 	<input type='text' name='avgjump' size='4' value='$avgjump'>\n";
	echo docpop('keepavg',"average jump");
	echo " 	<br />\n";
	echo " 	<input type='text' name='mask' size='4' value='$mask'>\n";
	echo docpop('mask','mask radius (in pixels)');
	echo " 	<br />\n";
	echo " 	<input type='text' name='hard' size='4' value='$hard'>\n";
	echo docpop('hard','hard value for back projection');
	echo " 	<br><br>\n";
	echo "  For snapshot images:<br>\n";
	echo "<input type='text' name='mass' value='$mass' size='4'> Mass (in kDa)<br>\n";
	echo "<input type='text' name='zoom' value='$zoom' size='4'> ";
	echo docpop('snapzoom','Zoom');
	echo "  <br>\n";
	echo " 	<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit',"Commit to Database");
	echo " 	</td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "	<td>\n";
	echo "  <center>\n";
	echo getSubmitForm("Create new class averages");
	echo "  </center>\n";
	echo "	</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</FORM>\n";

	echo appionRef();

	processing_footer();
	exit();
}
?>
