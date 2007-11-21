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
	$invert=$_POST['invert'];
	$viper=$_POST['viper'];
	$file=$_POST['file'];
	$path=$_POST['path'];
	$apix=$_POST['apix'];
	$densitypath=$path."/".$file;
	// make sure that an amplitude curve was selected
	if (!$ampcor) createform('<B>ERROR:</B> Select an amplitude adjustment curve');
	list($ampfile, $res) = explode('|~~|',$ampcor);

	$command = "postProc.py ";
	$command.= "-f $densitypath ";
	$command.= "--amp=$ampfile ";
	$command.= "--maxres=$res ";
	$command.= "--apix=$apix ";
	$command.= "--outdir=$path ";
	if ($lp) $command.="--lp=$lp ";
	if ($yflip=='on') $command.="--yflip ";
	if ($invert=='on') $command.="--invert ";
	if ($viper=='on') $command.="--viper ";

	writeTop("Post Process Reconstructed Density", "Post Process Reconstructed Density");
	echo"
	<P>
	<TABLE WIDTH='600' BORDER='1'>
	<tr><td colspan='2'>
	<B>PostProc Command:</B><BR>
	$command
	</td></tr>
        <tr><td>file</td><td>$densitypath</td></tr>
        <tr><td>ampcor curve</td><td>$ampfile</td></tr>
        <tr><td>max res</td><td>$res</td></tr>
        <tr><td>apix</td><td>$apix</td></tr>
        <tr><td>outdir</td><td>$path</td></tr>
        <tr><td>lp</td><td>$lp</td></tr>
        <tr><td>yflip</td><td>$yflip</td></tr>
        <tr><td>invert</td><td>$invert</td></tr>
        <tr><td>viper</td><td>$viper</td></tr>
        </table>\n";
	writeBottom();
	exit;
}

else createform();

function createform($extra=False) {
	$expId = $_GET['expId'];
	$refid = $_GET['refinement'];
	writeTop("Post Process Reconstructed Density", "Post Process Reconstructed Density");

	// write out errors, if any came up:
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
		
	$particle = new particledata();
	$info = $particle->getReconInfoFromRefinementId($refid);

	// get symmetry of initial model
	$init = $particle->getInitModelInfo($info['REF|ApInitialModelData|initialModel']);
	$fscres = $particle->getResolutionInfo($info['REF|ApResolutionData|resolution']);
	$halfres = ($fscres) ? sprintf("%.2f",$fscres['half']) : "None" ;
	$rmeas = $particle->getRMeasureInfo($info['REF|ApRMeasureData|rMeasure']);
	$rmeasureres = ($rmeas) ? sprintf("%.2f",$rmeas['rMeasure']) : "None" ;
	$appiondir = "/ami/sw/packages/pyappion/lib/";
	$densityfile = $info['path']."/".$info['volumeDensity'];
	$apix = ($particle->getStackPixelSizeFromStackId($info['REF|ApStackData|stack']))*1e10;

	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&refinement=$refid";

	$amplist = array();

	$lpval=($_POST['lp']) ? $_POST['lp'] : '';
	$yflipcheck=($_POST['yflip']=='on') ? 'checked' : '';
	$invertcheck=($_POST['invert']=='on') ? 'checked' : '';
	$vipercheck=($_POST['viper']=='on') ? 'checked' : '';

	// manually create list of the amplitude adjustment files
	$amplist[0]['name']="ampcor5.spi";
	$amplist[0]['res']=4.6;
	$amplist[0]['src']="GroEL SAXS data";
	$amplist[1]['name']="ampcorRNAvirus5.spi";
	$amplist[1]['res']=4.808;
	$amplist[1]['src']="Wild type CCMV Virus SAXS data collected by Kelly Lee (closed form, RNA-filled)";
	$amplist[2]['name']="ampcor8.spi";
	$amplist[2]['res']=7.854;
	$amplist[2]['src']="Experimental X-ray curve, smoothed by Dmitri Svergun";
	$amplist[3]['name']="ampcor11.spi";
	$amplist[3]['res']=11.519;
	$amplist[3]['src']="Experimental X-ray curve, smoothed by Dmitri Svergun";

	echo "<P>\n";
	echo "Density File: $densityfile<br />\n";
	echo "Resolution (FSC = 0.5): $halfres<br />\n";
	echo "Resolution (Rmeasure): $rmeasureres<br />\n";
	echo "Pixel Size: $apix ang/pix<br />\n";
	echo "<HR>\n";
	echo "<FORM NAME='postproc' METHOD='POST' ACTION='$formAction'>\n";
	echo "<center><INPUT type='submit' name='run' value='Perform amplitude adjustment'></center>\n";
	echo "<table class='1' border='1' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo "Low-pass filter results to: \n";
	echo "<input type='text' name='lp' size='3' value='$lpval'> &Aring;/pixel<br />\n";
	echo "<input type='checkbox' name='yflip' $yflipcheck>Flip handedness of density<br />\n";
	echo "<input type='checkbox' name='invert' $invertcheck>Invert the magnitude of the density<br />\n";
	if ($init['REF|ApSymmetryData|symmetry']< 3) {
	  echo "<input type='checkbox' name='viper' $vipercheck>Rotate density from EMAN to Viper orientation<br />\n";
	}
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "<P>\n";
	echo "<TABLE CLASS='tableborder' BORDER='1' WIDTH='600'>\n";
	foreach ($amplist as $amp) {
	  $ampfile = $appiondir.$amp['name'];
	  echo "<TR><TD>\n";
	  echo "<A HREF='ampcorplot.php?file=$ampfile&width=800&height=600'><IMG SRC='ampcorplot.php?file=$ampfile&width=200&height=150&nomargin=TRUE'>\n";
	  echo "</TD><TD>\n";
	  echo "<B>Resolution limit:</B> $amp[res]<br />\n";
	  echo "<B>Source:</B> $amp[src]<br />\n";
	  echo "<INPUT TYPE='radio' name='ampcor' value='$amp[name]|~~|$amp[res]'> Use this amplitude curve\n";
	  echo "</TD></TR>\n";
	}
	echo "</TABLE>\n";
	echo "<P>\n";
	echo "<INPUT TYPE='hidden' name='apix' value='$apix'>\n";
	echo "<INPUT TYPE='hidden' name='file' value='$info[volumeDensity]'>\n";
	echo "<INPUT TYPE='hidden' name='path' value='$info[path]'>\n";
	echo "<center><INPUT type='submit' name='run' value='Perform amplitude adjustment'></center>\n";
	echo "</FORM>\n";
	writeBottom();
	exit();
}
?>
