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
	$leginon = new leginondata();

	$runname=$_POST['runname'];
	$expId = $_GET['expId'];
	$refId = $_GET['refinement'];
	$ampcor=$_POST['ampcor'];
	$lp=$_POST['lp'];
	$yflip=$_POST['yflip'];
	$invert=$_POST['invert'];
	$viper=$_POST['viper'];
	$file=$_POST['file'];
	$path=$_POST['path'];
	$apix=$_POST['apix'];
	$norm=$_POST['norm'];
	$mask=$_POST['mask'];
	$imask=$_POST['imask'];
	$sym=$_POST['sym'];
	$res = $_POST['res'];
	$zoom = $_POST['zoom'];
	$contour = $_POST['contour'];
	$densitypath=$path."/".$file;
	$outdir=$path."/postproc";
	$densityname = $_POST['densityname'];

	// make sure that an amplitude curve was selected
	if (!$ampcor) createform('<B>ERROR:</B> Select an amplitude adjustment curve');
	list($ampfile, $maxfilt) = explode('|~~|',$ampcor);

	// get session name from expId
	$sessioninfo = $leginondata->getSessionInfo($expId);
	$sessname = $sessioninfo['Name'];

	$command = "postProc.py ";
	$command.= "--projectid=".$_SESSION['projectId']." ";
	$command.= "-s $sessname ";
	$command.= "--runname $runname ";
	$command.= "-f $densitypath ";
	$command.= "--amp=/ami/sw/packages/pyappion/lib/$ampfile ";
	if ($maxfilt < $apix*2)
		$maxfilt = $apix*2.1;
	$command.= "--maxfilt=$maxfilt ";
	$command.= "--apix=$apix ";
	$command.= "--res=$res ";
	$command.= "--sym=$sym ";
	$command.= "--reconid=$refId ";
	$command.= "-z $zoom ";
	$command.= "--contour=$contour ";
	if ($mask) $command.="--mask=$mask ";
	if ($imask) $command.="--imask=$imask ";
	if ($lp) $command.="--lp=$lp ";
	if ($norm=='on') $command.="--norm ";
	if ($yflip=='on') $command.="--yflip ";
	if ($invert=='on') $command.="--invert ";
	if ($viper=='on') $command.="--viper ";


	// submit job to cluster
	if ($_POST['process']=='Post Process') {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'uploaddensity',True);
		// if errors:
		if ($sub) createform("<b>ERROR:</b> $sub");

		// check that upload finished properly
		$jobf = $outdir.'/'.$runname.'/'.$runname.'.appionsub.log';
		$status = "Filtered and amplitude-corrected density uploaded";
		if (file_exists($jobf)) {
			$jf = file($jobf);
			$jfnum = count($jf);
			for ($i=$jfnum-5; $i<$jfnum-1; $i++) {
			  // if anything is red, it's not good
				if (preg_match("/red/",$jf[$i])) {
					$status = "<font class='apcomment'>Error while uploading, check the log file:<br />$jobf</font>";
					continue;
				}
			}
		}
		else $status = "Job did not run, contact the appion team";
	}

	processing_header("Post Process Reconstructed Density", "Post Process Reconstructed Density");
	echo $status;
	echo "<br />\n";
	echo"
	<TABLE WIDTH='600' BORDER='1'>
	<tr><td colspan='2'>
	<B>PostProc Command:</B><br>
	$command
	</td></tr>
        <tr><td>runname</td><td>$runname</td></tr>
        <tr><td>file</td><td>$densitypath</td></tr>
        <tr><td>ampcor curve</td><td>$ampfile</td></tr>
        <tr><td>max filt</td><td>$maxfilt</td></tr>
        <tr><td>mask</td><td>$mask</td></tr>
        <tr><td>imask</td><td>$imask</td></tr>
        <tr><td>norm</td><td>$norm</td></tr>
        <tr><td>apix</td><td>$apix</td></tr>
        <tr><td>lp</td><td>$lp</td></tr>
        <tr><td>yflip</td><td>$yflip</td></tr>
        <tr><td>invert</td><td>$invert</td></tr>
        <tr><td>viper</td><td>$viper</td></tr>
        </table>\n";
	processing_footer();
	exit;
}

else createform();

function createform($extra=False) {
	$expId = $_GET['expId'];
	$refId = $_GET['refinement'];

	$particle = new particledata();

	$refinementParams = $particle->getParamsFromRefinementDataId($refId);
	$sym=$refinementParams['REF|ApSymmetryData|symmetry'];
	processing_header("Post Process Reconstructed Density", "Post Process Reconstructed Density");

	// write out errors, if any came up:
	if ($extra) echo "<font color='red'>$extra</font>\n<hr />\n";
		
	$info = $particle->getReconInfoFromRefinementId($refId);

	// get symmetry of initial model if no symmetry saved for iteration
	if (!$sym) {
		$init = $particle->getInitModelInfo($info['REF|ApInitialModelData|initialModel']);
		$sym=$init['REF|ApSymmetryData|symmetry'];
	}
	$fscres = $particle->getResolutionInfo($info['REF|ApResolutionData|resolution']);
	$halfres = ($fscres) ? sprintf("%.2f",$fscres['half']) : "None" ;
	$rmeas = $particle->getRMeasureInfo($info['REF|ApRMeasureData|rMeasure']);
	$rmeasureres = ($rmeas) ? sprintf("%.2f",$rmeas['rMeasure']) : "None" ;
	$appiondir = "/ami/sw/packages/pyappion/lib/";
	$densityfile = $info['path']."/".$info['volumeDensity'];
	$apix = ($particle->getStackPixelSizeFromStackId($info['REF|ApStackData|stack']))*1e10;

	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&refinement=$refId";

	$amplist = array();

	// runname is generated from density
	$timestr = getTimestring();
	$densityroot = substr($densityname, 0, -4);
	$runname = $timestr;
	$runname = "refine".$refId."_".$runname;
	
	$runname=($_POST['runname']) ? $_POST['runname'] : $runname;
	$lpval=($_POST['lp']) ? $_POST['lp'] : '';
	$maskval=($_POST['mask']) ? $_POST['mask'] : '';
	$imaskval=($_POST['imask']) ? $_POST['imask'] : '';
	$yflipcheck=($_POST['yflip']=='on') ? 'checked' : '';
	$invertcheck=($_POST['invert']=='on') ? 'checked' : '';
	$vipercheck=($_POST['viper']=='on') ? 'checked' : '';
	$normcheck=($_POST['norm']=='on' || !$_POST['run']) ? 'checked' : '';
	$res = ($_POST['res']) ? $_POST['res'] : $halfres;
	$maxfilt = ($_POST['maxfilt']) ? $_POST['maxfilt'] : '';
	$contour = ($_POST['contour']) ? $_POST['contour'] : '1.5';
	$zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.5';

	// manually create list of the amplitude adjustment files
	$amplist[0]['name']="ampcor5.spi";
	$amplist[0]['maxfilt']=4.6;
	$amplist[0]['src']="GroEL SAXS data";
	$amplist[1]['name']="ampcorRNAvirus5.spi";
	$amplist[1]['maxfilt']=4.808;
	$amplist[1]['src']="Wild type CCMV Virus SAXS data collected by Kelly Lee (closed form, RNA-filled)";
	$amplist[2]['name']="ampcor8.spi";
	$amplist[2]['maxfilt']=7.854;
	$amplist[2]['src']="Experimental X-ray curve, smoothed by Dmitri Svergun";
	$amplist[3]['name']="ampcor11.spi";
	$amplist[3]['maxfilt']=11.519;
	$amplist[3]['src']="Experimental X-ray curve, smoothed by Dmitri Svergun";
	echo "<form name='postproc' method='post' action='$formAction'>\n";
	echo "<input type='hidden' name='densityname' value='".$info['volumeDensity']."'>";
	echo docpop('runname','Run Name:');
	echo "<br />\n";
	echo "  <input type='text' name='runname' size='25' value='$runname'>\n";
	echo "<br />\n";
	echo "Density File: $densityfile<br />\n";
	echo "Pixel Size: $apix ang/pix<br />\n";
	echo "<b>Reported Resolution:</b><br />\n";
	echo "FSC = 0.5: $halfres<br />\n";
	echo "Rmeasure: $rmeasureres<br />\n";
	echo "<b>Snapshot Options:</b>\n";
	echo "<br />\n";
	echo "<input type'text' name='res' value='$res' size='5'> Resolution\n";	echo "<br />\n";
	echo "<input type'text' name='contour' value='$contour' size='5'> Contour Level\n";
	echo "<br />\n";
	echo "<input type='text' name='zoom' value='$zoom' size='5'> Zoom\n";
	echo "<hr />\n";
	echo "<P>\n";
	echo "<table class='tableborder' border='1' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo "Low-pass filter results to: \n";
	echo "<input type='text' name='lp' size='3' value='$lpval'> &Aring;/pixel<br />\n";
	echo "Radius of outer mask: \n";
	echo "<input type='text' name='mask' size='4' value='$maskval'> &Aring;ngstroms<br />\n";
	echo "Radius of inner mask: \n";
	echo "<input type='text' name='imask' size='4' value='$imaskval'> &Aring;ngstroms<br />\n";
	echo "<input type='checkbox' name='yflip' $yflipcheck>Flip handedness of density<br />\n";
	echo "<input type='checkbox' name='invert' $invertcheck>Invert the magnitude of the density<br />\n";
	if ($sym< 3) {
		echo "<input type='checkbox' name='viper' $vipercheck>Rotate density from EMAN to Viper orientation<br />\n";
	}
	echo "<input type='hidden' name='sym' value='$sym'>\n";
	echo "<input type='checkbox' name='norm' $normcheck>Normalize the resulting density<br />\n";
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "<P>\n";
	echo "<TABLE CLASS='tableborder' BORDER='1' WIDTH='600'>\n";
	foreach ($amplist as $amp) {
		$ampfile = $appiondir.$amp['name'];
		echo "<TR><td>\n";
		echo "<A HREF='ampcorplot.php?file=$ampfile&width=800&height=600'><img src='ampcorplot.php?file=$ampfile&width=200&height=150&nomargin=TRUE'>\n";
		echo "</TD><td>\n";
		echo "<B>Resolution limit:</B> $amp[maxfilt]<br />\n";
		echo "<B>Source:</B> $amp[src]<br />\n";
		echo "<INPUT TYPE='radio' name='ampcor' value='$amp[name]|~~|$amp[maxfilt]'> Use this amplitude curve\n";
		echo "</TD></tr>\n";
	}
	echo "</table>\n";
	echo "<P>\n";
	echo "<INPUT TYPE='hidden' name='apix' value='$apix'>\n";
	echo "<INPUT TYPE='hidden' name='file' value='$info[volumeDensity]'>\n";
	echo "<INPUT TYPE='hidden' name='path' value='$info[path]'>\n";
	echo "<center>\n";
	echo getSubmitForm("Post Process");
	echo "</center>\n";
	echo "</form>\n";
	processing_footer();
	exit();
}
?>
