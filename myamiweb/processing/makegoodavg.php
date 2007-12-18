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

function javaCommands () {
	$javafunc = "
<SCRIPT LANGUAGE='JavaScript'>
function infopopup(infoname){
	var newwindow=window.open('','name','height=250, width=400');
	newwindow.document.write('<HTML><BODY>');
	if (infoname=='eulers'){
		newwindow.document.write('Eulers assigned to the particles for this iteration will be used when creating class averages.');
	}
	if (infoname=='sigma'){
		newwindow.document.write('Standard deviation multiplier to determine the quality of particle to be used.  If no value is specified, only particles that have a quality factor equal to or greater than the mean quality factor will be used in making the class averages.  A larger sigma will result in fewer particles, but of higher \"quality\"');
	}
	if (infoname=='avg'){
		newwindow.document.write('Any particles that have a median euler jump greater than this value will not be used in the class averages');
	}
	if (infoname=='mask'){
		newwindow.document.write('Mask radius of the class averages (in pixels)');
	}
	if (infoname=='eotest'){
		newwindow.document.write('even and odd class averages will be created in addition to the new class averages, to be used for an even/odd test');
	}
	newwindow.document.write('</BODY></HTML>');
	newwindow.document.close();
}
</SCRIPT>\n";
	return $javafunc;

}

if ($_POST['run']) {
	$reconId=$_GET['reconId'];
	$refId=$_GET['refId'];
	$iter=$_GET['iter'];
	$mask=$_POST['mask'];
	$sigma=$_POST['sigma'];
	$avgjump=$_POST['avgjump'];
	$stackname=$_POST['avgname'];
	$outdir=$_POST['outdir'];
	$eotest=$_POST['eotest'];

	if (!$stackname) createform('<B>ERROR:</B> Enter a name for new class average stack file');
	if (!$mask) createform('<B>ERROR:</B> Enter a mask radius');
	if ($avgjump=='') createform('<B>ERROR:</B> Enter a median euler jump');

	$command = "makegoodaverages.py ";
	$command.= "-r $reconId ";
	$command.= "-i $iter ";
	$command.= "-m $mask ";
	$command.= "-n $stackname ";
	$command.= "-o $outdir ";
	if ($avgjump != '') $command.= "-j $avgjump ";
	if ($sigma) $command.= "-s $sigma ";
	if ($eotest=='on') $command.="--eotest ";

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
        <tr><td>sigma</td><td>$sigma</td></tr>
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

	$javascript=javaCommands();

	writeTop("Create New Class Averages", "Create New Class Averages",$javascript);

	// write out errors, if any came up:
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
		
	$particle = new particledata();
	$refinfo = $particle->getRefinementRunInfo($reconId);
	// get iteration parameters for specified iteration:
	$paraminfo = $particle->getParamsFromRefinementDataId($refId);

	$iter=($_POST['iter']) ? $_POST['iter'] : $iter;
	$mask=($_POST['mask']) ? $_POST['mask'] : $paraminfo['mask'];
	$sigma=($_POST['sigma']) ? $_POST['sigma'] : '';
	$avgjump=($_POST['avgjump']) ? $_POST['avgjump'] : '0';
	$avgname=($_POST['avgname']) ? $_POST['avgname'] : 'goodavgs.hed';
	$outdir=($_POST['outdir']) ? $_POST['outdir'] : $refinfo['path'].'/eulers';
	$eocheck=($_POST['eotest']=='on' || !$_POST['run']) ? 'checked' : '';

        echo "<P>\n";
	echo "<FORM NAME='postproc' METHOD='POST' ACTION='$formAction'>\n";
	echo "<TABLE cellpadding='5' BORDER=3 CLASS=tableborder>\n";
	echo "<TR>\n";
	echo "  <TD VALIGN='TOP'>\n";
	echo "	New classes stack file name:<br />\n";
	echo "  <input type='text' name='avgname' size='25' value='$avgname'>\n";
	echo "	<br />\n";
	echo "	Output directory:<br />\n";
	echo "  <input type='text' name='outdir' size='63' value='$outdir'>\n";
	echo " 	</td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "	<td class='tablebg'>\n";
	echo "	<a href=\"javascript:infopopup('eulers')\">Use final Eulers from iteration:</A> <input type='text' name='iter' size='3' value='$iter'>\n";
	echo "  <br />\n";
	echo "  <input type='text' name='sigma' size='4' value='$sigma'> <a href=\"javascript:infopopup('sigma')\">keep sigma level</a>\n";
	echo " 	<br />\n";
	echo " 	<input type='text' name='avgjump' size='4' value='$avgjump'> <a href=\"javascript:infopopup('avg')\">average jump</a>\n";
	echo " 	<br />\n";
	echo " 	<input type='text' name='mask' size='4' value='$mask'> <a href=\"javascript:infopopup('mask')\">mask radius (in pixels)</a>\n";
	echo " 	<br />\n";
	echo " 	<input type='checkbox' name='eotest' $eocheck> <a href=\"javascript:infopopup('eotest')\">create averages for eotest</a>\n";
	echo " 	</td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "	<td>\n";
	echo "  <center><INPUT type='submit' name='run' value='Create new class averages'></center>\n";
	echo "	</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</FORM>\n";
	writeBottom();
	exit();
}
?>
