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
	if (!is_numeric($_POST['lpfilt'])) jobform("error: no high-frequency cut-off specified");
	if (!is_numeric($_POST['hpfilt'])) jobform("error: no low-frequency cut-off specified");
	if (!is_numeric($_POST['mask_radius'])) jobform("error: no mask radius specified");
	if (!is_numeric($_POST['mask_dropoff'])) jobform("error: no mask drop-off specified");
	if (!is_numeric($_POST['transalign_iter'])) jobform("error: number of iterations not specified for translational alignment");
	// if (!is_numeric($_POST['box_size'])) jobform("error: box dimensions not specified");
	generateProcessedClasses();
}

else jobForm();

function jobForm($extra=false) {

	$javafunc .= writeJavaPopupFunctions('appion');
	$particle = new particledata();

	processing_header("IMAGIC New-Classum Generator","IMAGIC New-Classum Generator",$javafunc);

	// write out errors, if any came up:
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";

	// get session info
	echo "<form name='imagicReclassifyClassums' method='post' action='$formaction'><br />\n";
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$sessiondata=displayExperimentForm($projectId,$expId,$expId);
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

	// fill in default parameters
	$classums = ($_POST[classums]) ? $_POST[classums] : "classums";
	$outdir = ($_POST[outdir]) ? $_POST[outdir] : $outdir;
	$runid = ($_POST[runid]) ? $_POST[runid] : "reclass".$newrun;
	$lpfilt = ($_POST[lpfilt]) ? $_POST[lpfilt] : "0.8";
	$hpfilt = ($_POST[hpfilt]) ? $_POST[hpfilt] : "0.05";
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
			$opvals = "$stackparams[boxSize]|--|$id|--|$filename|--|$number_particles|--|$noref_binning";
			echo "<option value='$opvals'>$name; ID=$id; $description; $num_classes classes; $number_particles particles in stack; $method </option>\n";
		}
	}
	echo "</select><BR/><BR/>\n";


	// javascript documentation in help.js
	$doc_runname = docpop('runid', '<t><b>Run Name:</b>');
	$doc_outdir = docpop('outdir', '<b>Output Directory:</b>');
	$doc_lpfilt = ""; // need something here
	$doc_hpfilt = ""; // need something here
	$doc_maskr = docpop('mask_radius', 'mask radius:');
	$doc_maskd = docpop('mask_dropoff', 'mask drop-off:');
	$doc_transiter = docpop('transalign_iter', 'translational alignment iterations');
	$doc_newclassums = docpop('new_classums', 'new classums');

	// fill in actual job form
	echo "<center><TABLE cellspacing='10' cellpadding='10'>";
	echo "<tr><td>";
	echo openRoundBorder();
	echo 	"<br />\n $doc_runname &nbsp <input type='text' name='runid' value='$runid'><br /><br />\n";
	echo 	"$doc_outdir &nbsp <input type='text' name='outdir' value='$outdir' size='50'><br /><br />\n";
	echo closeRoundBorder();
	echo 	"</td></tr></table></center>";

	// should either specify the filtering parameters or write some funtion to convert
	
	echo 	"<center><br /><TABLE border=1 class=table cellspacing='10' cellpadding='10'><tr><td valign='top'>";
	echo 	"<br /><b> Filtering & Masking Parameters </b><br /><br />\n";
	echo openRoundBorder();
	echo "	<input type='text' name='lpfilt' value='$lpfilt' size='5'>&nbsp&nbsp high-frequency cut-off:\n<br />\n 
		<input type='text' name='hpfilt' value='$hpfilt' size='5'>&nbsp&nbsp low-frequency cut-off:\n<br /><br />\n 
		<input type='text' name='mask_radius' value='$mask_radius' size='5'>&nbsp&nbsp\n $doc_maskr <br />
		<input type='text' name='mask_dropoff' value='$mask_dropoff' size='5'>&nbsp&nbsp\n $doc_maskd";
	echo closeRoundBorder();
	echo 	"</td>";
	echo 	"<td><br /><b> Particle Centering </b><br /><br />\n";
	echo openRoundBorder();
	echo 	"<input type='text' name='transalign_iter' value='$niter' size='5'>&nbsp&nbsp\n number of $doc_transiter"; 
	echo closeRoundBorder();	
	echo 	"<br /><b> Reclassification </b><br /><br />\n";
	echo openRoundBorder();
	echo 	"<input type='text' name='new_classums' size='5'>&nbsp&nbsp\n How many $doc_newclassums do you want?";
	echo closeRoundBorder();
	echo 	"</td></tr></table></center><br /><br />\n";
	echo 	"<center";
	echo getSubmitForm("run imagic");
	echo 	"</center></form>\n";
	processing_footer();
	exit;
}

function generateProcessedClasses() {		

	// get posted values
	$expId = $_GET['expId'];
	$lpfilt = ($_POST['lpfilt']) ? $_POST['lpfilt'] : '1';
	$hpfilt = ($_POST['hpfilt']) ? $_POST['hpfilt'] : '0';
	$mask_radius = ($_POST['mask_radius']) ? $_POST['mask_radius'] : '1';
	$mask_dropoff = ($_POST['mask_dropoff']) ? $_POST['mask_dropoff'] : '0';
	$niter = $_POST['transalign_iter'];
	$new_classums = $_POST['new_classums'];
	$outdir = $_POST['outdir'];
	$runid = $_POST['runid'];
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	$command = "$outdir/$runid/{$runid}_imagicReclassifyClassums.job";

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
	$text = "";
	$text .= "imagicReclassifyClassums.py";
	$text .= " --norefclassid=$classid --runid=$runid --oldstack=$filename --lp=$lpfilt";
	$text .= " --hp=$hpfilt --mask=$mask_radius --mask_d=$mask_dropoff --niter=$niter --numaverages=$new_classums";

	// write to jobfile
	$jobfile = "{$runid}_imagicReclassifyClassums.job";
	$tmpjobfile = "/tmp/$jobfile";
	$f = fopen($tmpjobfile,'w');
	fwrite($f,$text);
	fclose($f);	

	// create appion directory & copy job & batch files
	$cmd = "mkdir -p $outdir/$runid\n";
	$cmd.= "cp $tmpjobfile $outdir/$runid/$jobfile\n";
	$cmd.= "cd $outdir/$runid\n";
	$cmd.= "chmod 755 $jobfile\n";
	exec_over_ssh($_SERVER['HTTP_HOST'], $user, $pass, $cmd, True);

	if ($_POST['process']=="run imagic") {
		if (!($user && $pass)) jobform("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'generateNewClassums');
		// if errors:
		if ($sub) jobform("<b>ERROR:</b> $sub");
	}

	processing_header("IMAGIC Job Generator","IMAGIC Job Generator",$javafunc);

	echo "<pre>";
	echo htmlspecialchars($text);
	echo "</pre>";

	processing_footer();
	exit;
}

?>
