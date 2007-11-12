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
	$ampcor=$_POST['ampcor'];
	$lp=$_POST['lp'];
	$yflip=$_POST['yflip'];
	// make sure that an amplitude curve was selected
	if (!$ampcor) createform('<B>ERROR:</B> Select an amplitude adjustment curve');
	//echo "
}

else createform();

function createform($extra=False) {
	$expId = $_GET['expId'];
	$refid = $_GET['refinement'];
	writeTop("Amplitude Adjustment","Amplitude Adjustment");

	// write out errors, if any came up:
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
		
	$particle = new particledata();
	$info = $particle->getReconInfoFromRefinementId($refid);
	$fscres = $particle->getResolutionInfo($info['REF|ApResolutionData|resolution']);
	$halfres = ($fscres) ? sprintf("%.2f",$fscres['half']) : "None" ;
	$rmeas = $particle->getRMeasureInfo($info['REF|ApRMeasureData|rMeasure']);
	$rmeasureres = ($rmeas) ? sprintf("%.2f",$rmeas['rMeasure']) : "None" ;
	$appiondir = "/ami/sw/packages/pyappion/recon/";
	$densityfile = $info['path']."/".$info['volumeDensity'];

	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&refinement=$refid";

	echo "<P>\n";
	echo "Density File: $densityfile<br />\n";
	echo "Resolution (FSC = 0.5): $halfres<br />\n";
	echo "Resolution (Rmeasure): $rmeasureres<br />\n";
	echo "<HR>\n";
	echo "<FORM NAME='postproc' METHOD='POST' ACTION='$formAction'>\n";
	echo "<center><INPUT type='submit' name='run' value='Perform amplitude adjustment'></center>\n";
	echo "<TABLE CLASS='tableborder' BORDER='1' WIDTH='600'>\n";
	echo "<TR><TD>\n";
	echo "<A HREF='ampcorplot.php?file=/home/glander/pyappion/recon/ampcor.5.txt&width=800&height=600'><IMG SRC='ampcorplot.php?file=/home/glander/pyappion/recon/ampcor.5.txt&width=200&height=150&nomargin=TRUE'>\n";
	echo "</TD><TD>\n";
	echo "<B>Resolution limit:</B> 4.6<br />\n";
	echo "<B>Source:</B> GroEL SAXS data<br />\n";
	echo "<INPUT TYPE='radio' name='ampcor' value='1'> Use this amplitude curve\n";
	echo "</TD></TR>\n";
	echo "<TR><TD>\n";
	echo "<A HREF='ampcorplot.php?file=/home/glander/pyappion/recon/ampcor.RNAvirus.5.txt&width=800&height=600'><IMG SRC='ampcorplot.php?file=/home/glander/pyappion/recon/ampcor.RNAvirus.5.txt&width=200&height=150&nomargin=TRUE'>\n";
	echo "</TD><TD>\n";
	echo "<B>Resolution limit:</B>4.808<br />\n";
	echo "<B>Source:</B> Wild type CCMV Virus SAXS data collected by Kelly Lee (closed form, RNA-filled)<br />\n";
	echo "<INPUT TYPE='radio' name='ampcor' value=2> Use this amplitude curve\n";
	echo "</TD></TR>\n";
	echo "<TR><TD>\n";
	echo "<A HREF='ampcorplot.php?file=/home/glander/pyappion/recon/ampcor.8.txt&width=800&height=600'><IMG SRC='ampcorplot.php?file=/home/glander/pyappion/recon/ampcor.8.txt&width=200&height=150&nomargin=TRUE'>\n";
	echo "</TD><TD>\n";
	echo "<B>Resolution limit:</B> 7.854<br />\n";
	echo "<B>Source:</B> Experimental X-ray curve, smoothed by Dmitri Svergun<br />\n";
	echo "<INPUT TYPE='radio' name='ampcor' value=3> Use this amplitude curve\n";
	echo "</TD></TR>\n";
	echo "<TR><TD>\n";
	echo "<A HREF='ampcorplot.php?file=/home/glander/pyappion/recon/ampcor.11.txt&width=800&height=600'><IMG SRC='ampcorplot.php?file=/home/glander/pyappion/recon/ampcor.11.txt&width=200&height=150&nomargin=TRUE'>\n";
	echo "</TD><TD>\n";
	echo "<B>Resolution limit:</B>11.519<br />\n";
	echo "<B>Source:</B> Experimental X-ray curve, smoothed by Dmitri Svergun<br />\n";
	echo "<INPUT TYPE='radio' name='ampcor' value=4> Use this amplitude curve\n";
	echo "</TD></TR>\n";
	echo "</TABLE>\n";
	echo "<P>\n";
	echo "<table class='1' border='1' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo "Low-pass filter results to: \n";
	echo "<input type='text' name='lp' size=3> &Aring;/pixel<br />\n";
	echo "<input type='checkbox' name='yflip'>Flip handedness of density<br />\n";
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "<center><INPUT type='submit' name='run' value='Perform amplitude adjustment'></center>\n";
	echo "</FORM>\n";
	writeBottom();
	exit();
}
?>
