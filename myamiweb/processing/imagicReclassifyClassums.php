<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an IMAGIC Reclassification Job initiating a 3d0 model generation
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";


// check for errors in submission form
if ($_POST['process']) {
	$stackinfo = explode('|--|', $_POST['opvals']);
	$num_classes = $stackinfo[5];
	if (!is_numeric($_POST['lpfilt'])) jobform("error: no high-frequency cut-off specified");
	if (!is_numeric($_POST['hpfilt'])) jobform("error: no low-frequency cut-off specified");
	if (!is_numeric($_POST['mask_radius'])) jobform("error: no mask radius specified");
	if (!is_numeric($_POST['mask_dropoff'])) jobform("error: no mask drop-off specified");
	if (!is_numeric($_POST['transalign_iter'])) jobform("error: number of iterations not specified for translational alignment");
	if (!is_numeric($_POST['new_classums'])) jobform("error: number of new class averages not specified");
	if ($_POST['new_classums'] > $num_classes) {
		echo "greater than";
		jobform("error: number of new class averages specified exceeds the number of old averages");
	}

	

	generateProcessedClasses();
}

else jobForm();

function jobForm($extra=false) {

	$javafunc .= writeJavaPopupFunctions('appion');
	$particle = new particledata();

	processing_header("IMAGIC New-Classum Generator","IMAGIC New-Classum Generator",$javafunc);

	// write out errors, if any came up:
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	// get session info
	echo "<form name='imagicReclassifyClassums' method='post' action='$formaction'><br />\n";
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get number of reclassification runs
	$reclassnum = count($particle->getImagicReclassFromSessionId($expId));
	$newrun = $reclassnum + 1; 
	
	
	// specify output directory and replace output directory with data00
	if (!empty($sessioninfo)) {
		$outdir=$sessioninfo['Image path'];
		$outdir=ereg_replace("leginon","appion",$outdir);
		$outdir=ereg_replace("rawdata","clsavgstacks",$outdir);
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// fill in default parameters
	$outdir = ($_POST[outdir]) ? $_POST[outdir] : $outdir;
	$runid = ($_POST[runid]) ? $_POST[runid] : "reclass".$newrun;
	$description = ($_POST[description]) ? $_POST[description] : "";
	$lpfilt = ($_POST[lpfilt]) ? $_POST[lpfilt] : "5";
	$hpfilt = ($_POST[hpfilt]) ? $_POST[hpfilt] : "200";
	$mask_radius = ($_POST[mask_radius]) ? $_POST[mask_radius] : "0.8";
	$mask_dropoff = ($_POST[mask_dropoff]) ? $_POST[mask_dropoff] : "0";
	$niter = ($_POST[transalign_iter]) ? $_POST[transalign_iter] : "5";
	
	// find each noref entry in database and allow user to select
	echo "<select name='opvals'>\n";
	$filenames = array();
	$norefData = $particle->getNoRefIds($expId, True);
	$norefruns=count($norefData);

	// get parameters for each noref entry
	foreach ($norefData as $norefid) {
		$norefnum = $norefid['DEF_id'];
		$stackid = $norefid['REF|ApStackData|stack'];
		$number_particles = $particle -> getNumStackParticles($stackid);
		$r = $particle->getNoRefParams($norefnum);
		$norefpath = $r['path']."/";
		$noref_binning = $r['bin'];
		$name = $norefid['name'];
		$description = $norefid['description'];
		$classIds = $particle->getNoRefClassRuns($norefnum);
		$classnum = count($classIds);
		foreach ($classIds as $classId) {
			$id = $classId['DEF_id'];
			$filename = $norefpath;
			$filename.= $classId['classFile'];
			$filenames[] = $filename;
			$num_classes = $classId['num_classes'];
			$method = $classId['method'];	
			$nump=commafy($particle->getNumStackParticles($classId['stackid']));
			$stackparams = $particle->getStackParams($stackid);
			$opvals = "$stackparams[boxSize]|--|$id|--|$filename|--|$number_particles|--|$noref_binning|--|$num_classes";
			echo "<option value='$opvals'>$name; ID=$id; $description; $num_classes classes; $number_particles particles in stack; $method </option>\n";
		}
	}
	echo "</select><br><br>\n";


	// javascript documentation in help.js
	$doc_runname = docpop('runid', '<b>Reclassification Run Name:</b>');
	$doc_outdir = docpop('outdir', '<b>Output Directory:</b>');
	$doc_lpfilt = docpop('lpfilt', 'low-pass filter class averages before reclassifying'); 
	$doc_hpfilt = docpop('hpfilt', 'high-pass filter class averages before reclassifying'); 
	$doc_maskr = docpop('mask_radius', 'mask radius');
	$doc_maskd = docpop('mask_dropoff', 'mask drop-off');
	$doc_transiter = docpop('transalign_iter', 'translational alignment iterations');
	$doc_newclassums = docpop('new_classums', 'new classums');

###################################


	echo"
	<table border='0' class='tableborder'>
	<tr>
		<td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo $doc_runname;
	echo "<input type='text' name='runid' value='$runid'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo $doc_outdir;
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$outdir' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of Reclassification:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='36'>$description</textarea>\n";
	echo closeRoundBorder();
	echo "</td>
		</tr>\n";
	echo "<tr>
			<td>\n";


	echo "</TD></tr><TR>\n";
	echo "<TD VALIGN='TOP'>\n";

	echo "</TD></tr>\n";
	echo "<TR>\n";
	echo "<TD VALIGN='TOP'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<br></TD></tr>\n</table>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE CELLPADDING='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";

	// filtering and masking parameters
	echo "<b>Filtering and Masking Parameters</b>\n";
	echo "<br />\n";
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='lpfilt' SIZE='4' VALUE='$lpfilt'>\n";
	echo $doc_lpfilt;
	echo "<font size='-2'> (&Aring;ngstroms)</font>\n";
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='hpfilt' SIZE='4' VALUE='$hpfilt'>\n";
	echo $doc_hpfilt;
	echo "<font size='-2'> (&Aring;ngstroms)</font>\n";
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='mask_radius' VALUE='$mask_radius' SIZE='4'>\n";
	echo $doc_maskr;
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='mask_dropoff' VALUE='$mask_dropoff' SIZE='4'>\n";
	echo $doc_maskd;
	echo "<br>\n";
	echo "<br>\n";

	// particle centering
	echo "<b>Particle Centering</b>\n";
	echo "<br />\n";
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='transalign_iter' VALUE='$niter' SIZE='4'>\n";
	echo "number of $doc_transiter";
	echo "<br>\n";
	echo "<br>\n";

	// Reclassification
	echo "<b>Reclassification</b>\n";
	echo "<br />\n";
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='new_classums' SIZE='4'>\n";
	echo "How many $doc_newclassums do you want?";
	echo "<br>\n";

	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo getSubmitForm("Run Imagic");
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";



	processing_footer();
	exit;
}

function generateProcessedClasses() {		

	// get posted values
	$expId = $_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$lpfilt = ($_POST['lpfilt']) ? $_POST['lpfilt'] : '1';
	$hpfilt = ($_POST['hpfilt']) ? $_POST['hpfilt'] : '0';
	$mask_radius = ($_POST['mask_radius']) ? $_POST['mask_radius'] : '1';
	$mask_dropoff = ($_POST['mask_dropoff']) ? $_POST['mask_dropoff'] : '0';
	$niter = $_POST['transalign_iter'];
	$new_classums = $_POST['new_classums'];
	$outdir = $_POST['outdir'];
	$runid = $_POST['runid'];
	$description = $_POST['description'];
	$commit = ($_POST['commit']=="on") ? '--commit' : '';
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	// get stack values
	$stackinfo = explode('|--|', $_POST['opvals']);
	$stack_box_size = $stackinfo[0];
	$filename = $stackinfo[2];
	$classid = $stackinfo[1];
	if (strstr($classid, "/")) {
		$position = strpos($classid, "/");
		$start = $position + strlen("/");
		$classid = substr($classid, $start);
	}
	$bin = is_numeric($stackinfo[4]) ? $stackinfo[4] : "1";
	$box_size = $stack_box_size / $bin;
	
	// create python command for executing imagic job file	
	$command .= "imagicReclassifyClassums.py";
	$command .= " --projectid=".$_SESSION['projectId'];	
	$command .= " --norefclassid=$classid --runname=$runid --rundir=$outdir/$runid --oldstack=$filename --lp=$lpfilt";
	$command .= " --hp=$hpfilt --mask=$mask_radius --mask_d=$mask_dropoff --niter=$niter";
	$command .= " --numaverages=$new_classums --description=\"$description\"";
	if ($commit) $command .= " --commit";
	else $command.=" --no-commit";
/*
	// write to jobfile
	$jobfile = "{$runid}_imagicReclassifyClassums.job";
	$tmpjobfile = "/tmp/$jobfile";
	$f = fopen($tmpjobfile,'w');
	fwrite($f,$command);
	fclose($f);	

	// create appion directory & copy job & batch files
	$cmd = "mkdir -p $outdir/$runid\n";
	$cmd.= "cp $tmpjobfile $outdir/$runid/$jobfile\n";
	$cmd.= "cd $outdir/$runid\n";
	$cmd.= "chmod 755 $jobfile\n";
	exec_over_ssh($_SERVER['HTTP_HOST'], $user, $pass, $cmd, True);
*/
	if ($_POST['process']=="Run Imagic") {
		if (!($user && $pass)) jobform("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'generateProcessedClasses');
		// if errors:
		if ($sub) jobform("<b>ERROR:</b> $sub");
	}

	processing_header("IMAGIC Job Generator","IMAGIC Job Generator",$javafunc);

	echo "<pre>";
	echo htmlspecialchars($command);
	echo "</pre>";

	processing_footer();
	exit;
}

?>
