<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Display results for each iteration of a refinement
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
  
// --- check if reconstruction is specified

if ($_POST['process']) {
	$expId = $_GET['expId'];
	$reconId=$_GET['reconId'];
	$refId=$_GET['refId'];
	$iter=$_GET['iter'];
	$mask=$_POST['mask'];
	$hard=$_POST['hard'];
	$sigma=$_POST['sigma'];
	$avgjump=$_POST['avgjump'];
	$stackname=$_POST['avgname'];
	$bpname=$_POST['bpname'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$rundir=$outdir."/".$runname;

	if (!$stackname) createform('<B>ERROR:</B> Enter a name for new class average stack file');
	if (!$bpname) createform('<B>ERROR:</B> Enter a name for new 3d density file');
	if (!$mask) createform('<B>ERROR:</B> Enter a mask radius');
	if (!$hard) createform('<B>ERROR:</B> Enter a hard value');
	if ($avgjump=='') createform('<B>ERROR:</B> Enter a median euler jump');

	$command = "makegoodaverages.py ";
	$command.= "--projectid=".$_SESSION['projectId']." ";
	$command.= "--reconid=$reconId ";
	$command.= "--iter=$iter ";
	$command.= "--mask=$mask ";
	$command.= "--hard=$hard ";
	$command.= "--stackname=$stackname ";
	$command.= "--make3d=$bpname ";
	$command.= "--runname=$runname ";
	$command.= "--rundir=$rundir ";
	if ($avgjump != '') $command.= "--avgjump=$avgjump ";
	if ($sigma) $command.= "--sigma=$sigma ";
	$command.= "--eotest ";

	// submit job to cluster
	if ($_POST['process']=='Create new class averages'){
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'removeJumpers',False,False);
		// if errors:
		if ($sub) createform("<b>ERROR:</b> $sub");
		exit;
	}

	processing_header("Create New Class Averages","Create New Class Averages");
	echo"
	<TABLE WIDTH='600' BORDER='1'>
	<tr><td colspan='2'>
	<B>Create Class Averages Command:</B><br>
	$command
	</td></tr>
	<tr><td>file</td><td>$stackname</td></tr>
	<tr><td>mask</td><td>$mask</td></tr>
	<tr><td>hard</td><td>$hard</td></tr>
	<tr><td>avgjump</td><td>$avgjump</td></tr>
	<tr><td>iter</td><td>$iter</td></tr>
	<tr><td>reconId</td><td>$reconId</td></tr>
	<tr><td>sigma</td><td>$sigma</td></tr>
	</table>\n";
	processing_footer();
	exit;
}

else createform();

function createform($extra=False) {
	$expId = $_GET['expId'];
	$reconId = $_GET['reconId'];
	$refId = $_GET['refId'];
	$iter = $_GET['iter'];

	$javascript=writeJavaPopupFunctions('appion');

	processing_header("Create New Class Averages", "Create New Class Averages",$javascript);

	// write out errors, if any came up:
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
		
	$particle = new particledata();
	$refinfo = $particle->getRefinementRunInfo($reconId);
	// get iteration parameters for specified iteration:
	$paraminfo = $particle->getParamsFromRefinementDataId($refId);
	// print_r($paraminfo);
	$runname = getTimestring();
	$runname = "refine".$refId."_".$runname;

	$iter=($_POST['iter']) ? $_POST['iter'] : $iter;
	$mask=($_POST['mask']) ? $_POST['mask'] : $paraminfo['mask'];
	$hard=($_POST['hard']) ? $_POST['hard'] : $paraminfo['EMAN_hard'];
	$sigma=($_POST['sigma']) ? $_POST['sigma'] : '';
	$avgjump=($_POST['avgjump']) ? $_POST['avgjump'] : '0';
	$avgname=($_POST['avgname']) ? $_POST['avgname'] : 'goodavgs.hed';
	$bpname=($_POST['bpname']) ? $_POST['bpname'] : 'threed.mrc';
	$runname=($_POST['runname']) ? $_POST['runname'] : $runname;
	$outdir=($_POST['outdir']) ? $_POST['outdir'] : $refinfo['path'].'/eulers';

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
	echo docpop('eulers', 'Use final Eulers from iteration:');
	echo "  <input type='text' name='iter' size='3' value='$iter'>\n";
	echo "  <br />\n";
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
	echo " 	<br />\n";
	echo " 	<input type='checkbox' name='make3d' $bpcheck>\n";
	echo docpop('commit',"Commit results to database");
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
	processing_footer();
	exit();
}
?>
