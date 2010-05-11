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
require "inc/summarytables.inc";

// --- check if reconstruction is specified

if ($_POST['process']) {
	runPostProc();
} else {
	createform();
}

function createform($extra=False) {
	$expId = $_GET['expId'];
	$refIterId = $_GET['refineIter'];

	$appiondir = "/ami/sw/packages/Appion";

	$particle = new particledata();

	$info = $particle->getReconInfoFromRefinementId($refIterId);
	$modelid = $info['REF|ApInitialModelData|initialModel'];
	$stackid = $info['REF|ApStackData|stack'];
	$apix = ($particle->getStackPixelSizeFromStackId($stackid))*1e10;

	$refineIterParams = $particle->getParamsFromRefinementDataId($refIterId);
	$symid =$refineIterParams['REF|ApSymmetryData|symmetry'];
	$defmask = $refineIterParams['mask'] ? floor($refineIterParams['mask']*$apix) : '';
	$defimask = $refineIterParams['imask'] ? ceil($refineIterParams['imask']*$apix) : '';
	processing_header("Post Process Reconstructed Density", "Post Process Reconstructed Density");

	// write out errors, if any came up:
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
		


	// get symmetry of initial model if no symmetry saved for iteration
	if (!$symid) {
		$modeldata = $particle->getInitModelInfo($modelid);
		$symid = $modeldata['REF|ApSymmetryData|symmetry'];
	}
	$symdata = $particle->getSymInfo($symid);
	$symname = $symdata['eman_name'];
	$fscres = $particle->getResolutionInfo($info['REF|ApResolutionData|resolution']);
	$halfres = ($fscres) ? sprintf("%.2f",$fscres['half']) : "None" ;
	$rmeas = $particle->getRMeasureInfo($info['REF|ApRMeasureData|rMeasure']);
	$rmeasureres = ($rmeas) ? sprintf("%.2f",$rmeas['rMeasure']) : "None" ;
	$densityfile = $info['path']."/".$info['volumeDensity'];



	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&refineIter=$refIterId";

	$amplist = array();

	// runname is generated from density
	$timestr = getTimestring();
	$densityroot = substr($densityname, 0, -4);
	$runname = $timestr;
	$runname = "refine".$refIterId."_".$runname;
	
	$runname=($_POST['runname']) ? $_POST['runname'] : $runname;
	$lpval=($_POST['lp']) ? $_POST['lp'] : round($halfres*0.5,2);
	$maskval=($_POST['mask']) ? $_POST['mask'] : $defmask;
	$imaskval=($_POST['imask']) ? $_POST['imask'] : $defimask;
	$yflipcheck=($_POST['yflip']=='on') ? 'checked' : '';
	$invertcheck=($_POST['invert']=='on') ? 'checked' : '';
	$vipercheck=($_POST['viper']=='on') ? 'checked' : '';
	$normcheck=($_POST['norm']=='on' || !$_POST['run']) ? 'checked' : '';
	$bfactorcheck=($_POST['bfactor']=='on') ? 'checked' : '';

	$res = ($_POST['res']) ? $_POST['res'] : round($halfres,2);
	$maxfilt = ($_POST['maxfilt']) ? $_POST['maxfilt'] : '';
	$contour = ($_POST['contour']) ? $_POST['contour'] : '2.0';
	$mass = ($_POST['mass']) ? $_POST['mass'] : '';
	$zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.0';
	$median = ($_POST['median']) ? $_POST['median'] : '2';

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

	echo "<table class='tableborder' border='1' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo docpop('runname','Run Name:');
	echo "<br/>\n";
	echo "  <input type='text' name='runname' size='25' value='$runname'>\n";
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "<br/>\n";

	echo "Density File: $densityfile<br/>\n";
	echo "Pixel Size: ".round($apix,2)." &Aring/pixel<br/>\n";
	echo "<br/>\n";

	echo "<h4>Reported Resolution:</h4>\n";
	echo "FSC&frac12;: $halfres &Aring<br/>\n";
	echo "Rmeasure: $rmeasureres &Aring<br/>\n";
	echo "<br/>\n";

	echo "<table class='tableborder' border='1' width='600'>\n";
	// B-factor sharpening
	echo "<tr><td colspan='2'>\n";
	echo "<h3>B-factor sharpening:</h3>\n";
	echo "</td></tr>\n";
	echo "<tr><td>&nbsp;</td><td>\n";
	echo "<input type='checkbox' name='bfactor' $bfactorcheck>Apply sharpening "
		."using automated b-factor determination from FSC curve\n";
	echo "(<a href='http://www.ual.es/~jjfdez/SW/embfactor.html'>"
		."description&nbsp;<img src='img/external.png' border='0'></a>)\n";
	echo "</td></tr>\n";

	// Amplitude correction
	echo "<tr><td colspan='2'>\n";
	echo "<h3>Apply amplitude correction</h3>\n";
	echo "</td></tr>\n";
	echo "<tr><td>&nbsp;</td><td>\n";
	echo "<input type='radio' name='ampcor' value='0'> None\n";
	echo "</td></tr>\n";

	foreach ($amplist as $amp) {
		$ampfile = $appiondir.'/appionlib/data/'.$amp['name'];
		echo "<TR><td>\n";
		if (file_exists($ampfile)) {
			echo "<A HREF='ampcorplot.php?file=$ampfile&width=800&height=600'>";
			//echo $ampfile;
			echo "<img src='ampcorplot.php?file=$ampfile&width=150&height=75&nomargin=True'>\n";
		}	else {
			echo "&nbsp;";
		}
		echo "</TD><td>\n";
		echo "<B>Resolution limit:</B> $amp[maxfilt]<br/>\n";
		echo "<B>Source:</B> $amp[src]<br/>\n";
		echo "<INPUT TYPE='radio' name='ampcor' value='$amp[name]|~~|$amp[maxfilt]'> Use this amplitude curve\n";
		echo "</TD></tr>\n";
	}
	echo "</table>\n";
	echo "<br/>\n";

	echo "<h4>UCSF Chimera Snapshot Options:</h4>\n";
	echo "<input type'text' name='res' value='$res' size='4'> Resolution\n";
	echo "<br/>\n";
	echo "<input type'text' name='contour' value='$contour' size='4'> Contour Level\n";
	echo "<br/>\n";
	echo "<input type'text' name='mass' value='$mass' size='4'> Mass (in kDa)\n";
	echo "<br/>\n";
	echo "<input type='text' name='zoom' value='$zoom' size='4'> Zoom\n";
	echo "<hr />\n";
	echo "<P>\n";


	echo "<table class='tableborder' border='1' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo "Low-pass filter: \n";
	echo "</td><td>\n";
	echo "<input type='text' name='lp' size='3' value='$lpval'> &Aring;ngstroms<br/>\n";

	echo "</tr></td><tr><td>\n";
	echo "Median filter: \n";
	echo "</td><td>\n";
	echo "<input type='text' name='median' size='3' value='$median'> Pixels<br/>\n";

	echo "</tr></td><tr><td>\n";
	echo "Radius of outer mask: \n";
	echo "</td><td>\n";
	echo "<input type='text' name='mask' size='4' value='$maskval'> &Aring;ngstroms<br/>\n";

	echo "</tr></td><tr><td>\n";
	echo "Radius of inner mask: \n";
	echo "</td><td>\n";
	echo "<input type='text' name='imask' size='4' value='$imaskval'> &Aring;ngstroms<br/>\n";

	echo "</tr></td><tr><td colspan='2'>\n";
	echo "<input type='checkbox' name='yflip' $yflipcheck>Flip handedness of density<br/>\n";
	echo "</tr></td><tr><td colspan='2'>\n";
	echo "<input type='checkbox' name='invert' $invertcheck>Invert the magnitude of the density<br/>\n";
	if ($symname == 'icos') {
		echo "</tr></td><tr><td colspan='2'>\n";
		echo "<input type='checkbox' name='viper' $vipercheck>Rotate density from EMAN to Viper orientation<br/>\n";
	}
	echo "<input type='hidden' name='symname' value='$symname'>\n";
	echo "</tr></td><tr><td colspan='2'>\n";
	echo "<input type='checkbox' name='norm' $normcheck>Normalize the resulting density<br/>\n";
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "<P>\n";



	echo "<P>\n";
	echo "<INPUT TYPE='hidden' name='apix' value='$apix'>\n";
	echo "<INPUT TYPE='hidden' name='file' value='$info[volumeDensity]'>\n";
	echo "<INPUT TYPE='hidden' name='path' value='$info[path]'>\n";
	echo "<center>\n";
	echo getSubmitForm("Post Process");
	echo "</center>\n";
	echo "</form>\n";

	echo "<table class='tablebubble'><tr><td>\n";
	echo stacksummarytable($stackid, true);
	echo "</td></tr><tr><td>\n";
	echo modelsummarytable($modelid, true);
	echo "</td></tr></table>\n";

	processing_footer();
	exit();
}

function runPostProc() {
	$leginondata = new leginondata();

	$runname=$_POST['runname'];
	$expId = $_GET['expId'];
	$refIterId = $_GET['refineIter'];
	$ampcor=$_POST['ampcor'];
	$lp=$_POST['lp'];
	$yflip=$_POST['yflip'];
	$invert=$_POST['invert'];
	$viper=$_POST['viper'];
	$bfactor=$_POST['bfactor'];
	$file=$_POST['file'];
	$path=$_POST['path'];
	$apix=$_POST['apix'];
	$norm=$_POST['norm'];
	$mask=$_POST['mask'];
	$imask=$_POST['imask'];
	$symname=$_POST['symname'];
	$res = $_POST['res'];
	$zoom = $_POST['zoom'];
	$mass = $_POST['mass'];
	$median = $_POST['median'];
	$contour = $_POST['contour'];
	$densitypath=$path."/".$file;
	$outdir=$path."/postproc";
	$densityname = $_POST['densityname'];

	// make sure that an amplitude curve was selected
	if ($ampcor && $bfactor)
		createform('<B>ERROR:</B> Select only one of amplitude or b-factor correction');
	if (!$ampcor && !$bfactor)
		createform('<B>ERROR:</B> Select an amplitude adjustment curve or b-factor correction');
	if ($ampcor)
		list($ampfile, $maxfilt) = explode('|~~|',$ampcor);

	// get session name from expId
	$sessioninfo = $leginondata->getSessionInfo($expId);
	$sessname = $sessioninfo['Name'];

	$command = "postProc.py ";
	$command.= "--projectid=".getProjectId()." ";
	$command.= "--reconiterid=$refIterId ";
	$command.= "-s $sessname ";
	$command.= "--runname $runname ";
	$command.= "-f $densitypath ";
	if ($ampcor) {
		$command.= "--amp=$ampfile ";
		if ($maxfilt < $apix*2)
			$maxfilt = $apix*2.1;
		$command.= "--maxfilt=$maxfilt ";
	} else {
		$command.="--bfactor ";
	}
	$command.= "--apix=$apix ";
	$command.= "--res=$res ";
	$command.= "--sym=$symname ";
	if ($median) $command.= "--median=$median ";
	if ($zoom) $command.= "--zoom=$zoom ";
	if ($contour) $command.= "--contour=$contour ";
	if ($mass) $command.="--mass=$mass ";
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

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'postproc');
		// if errors:
		if ($sub)
			createform("<b>ERROR:</b> $sub");
		exit();
	}

	processing_header("Post Process Reconstructed Density", "Post Process Reconstructed Density");
	echo $status;
	echo "<br/>\n";
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


?>
