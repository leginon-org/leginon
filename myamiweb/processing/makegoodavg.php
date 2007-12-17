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

if ($_POST['run']) {
	$reconId=$_GET['reconId'];
	$refId=$_GET['refId'];
	$iter=$_GET['iter'];
	$mask=$_POST['mask'];
	$nsig=$_POST['nsig'];
	$avgjump=$_POST['avgjump'];
	$stackname=$_POST['avgname'];
	$eotest=$_POST['eotest'];

	if (!$stackname) createform('<B>ERROR:</B> Enter a name for new class average stack file');
	if (!$mask) createform('<B>ERROR:</B> Enter a mask radius');
	if ($avgjump=='') createform('<B>ERROR:</B> Enter a median euler jump');

	$command = "makegoodaverages.py ";
	$command.= "reconid=$reconId ";
	$command.= "iter=$iter ";
	$command.= "mask=$mask ";
	$command.= "avgjump=$avgjump ";
	$command.= "stackname=$stackname ";
	if ($nsig) $command.= "nsig=$nsig ";
	if ($eotest=='on') $command.="eotest ";

	writeTop("Create New Class Averages","Create New Class Averages");
	echo"
	<P>
	<TABLE WIDTH='600' BORDER='1'>
	<tr><td colspan='2'>
	<B>Create Class Averages Command:</B><BR>
	$command
	</td></tr>
        <tr><td>file</td><td>$stackname</td></tr>
        <tr><td>mask</td><td>$mask</td></tr>
        <tr><td>avgjump</td><td>$avgjump</td></tr>
        <tr><td>iter</td><td>$iter</td></tr>
        <tr><td>reconId</td><td>$reconId</td></tr>
        <tr><td>nsig</td><td>$nsig</td></tr>
        <tr><td>eotest</td><td>$eotest</td></tr>
        </table>\n";
	writeBottom();
	exit;
}

else createform();

function createform($extra=False) {
	$expId = $_GET['expId'];
	$reconId = $_GET['reconId'];
	$refId = $_GET['refId'];
	$iter = $_GET['iter'];
	writeTop("Create New Class Averages", "Create New Class Averages");

	// write out errors, if any came up:
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
		
	$particle = new particledata();
	$refinfo = $particle->getRefinementRunInfo($reconId);
	// get iteration parameters for specified iteration:
	$paraminfo = $particle->getParamsFromRefinementDataId($refId);

	$iter=($_POST['iter']) ? $_POST['iter'] : $iter;
	$mask=($_POST['mask']) ? $_POST['mask'] : $paraminfo['mask'];
	$nsig=($_POST['nsig']) ? $_POST['nsig'] : $paraminfo['EMAN_classkeep'];
	$avgjump=($_POST['avgjump']) ? $_POST['avgjump'] : '0';
	$avgname=($_POST['avgname']) ? $_POST['avgname'] : $refinfo['path'].'/eulers/classes.new.hed';
	$eocheck=($_POST['eotest']=='on' || !$_POST['run']) ? 'checked' : '';

        echo "<P>\n";
	echo "<FORM NAME='postproc' METHOD='POST' ACTION='$formAction'>\n";
	echo "<TABLE cellpadding='5' BORDER=3 CLASS=tableborder>\n";
	echo "<TR>\n";
	echo "  <TD VALIGN='TOP'>\n";
	echo "	New classes stack file name:<br />\n";
	echo "  <input type='text' name='avgname' size='63' value='$avgname'>\n";
	echo " 	<p>\n";
	echo "	Use final Eulers from iteration: <input type='text' name='iter' size='3' value='$iter'>\n";
	echo "  <br />\n";
	echo "  <input type='text' name='nsig' size='4' value='$nsig'> keep sigma\n";
	echo " 	<br />\n";
	echo " 	<input type='text' name='avgjump' size='4' value='$avgjump'> average jump\n";
	echo " 	<br />\n";
	echo " 	<input type='text' name='mask' size='4' value='$mask'> mask radius (in pixels)\n";
	echo " 	<br />\n";
	echo " 	<input type='checkbox' name='eotest' $eocheck> create averages for eotest\n";
	echo "  <center><INPUT type='submit' name='run' value='Create new class averages'></center>\n";
	echo "</TD>\n";
	echo "</TR>\n";
	echo "</table>\n";
	echo "</FORM>\n";
	writeBottom();
	exit();
}
?>
