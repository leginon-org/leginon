<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an Eman Job for submission to a cluster
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
		$outdir=ereg_replace("data..","data00",$outdir);
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}

	// fill in default parameters
	$classums = ($_POST[classums]) ? $_POST[classums] : "classums";
	$indir = ($_POST[indir]) ? $_POST[indir] : "/ami/data00/appion";
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

	//echo "<TABLE BORDER=0 table width='100' CLASS=tableborder CELLPADDING=15>";
	echo "</select>\n";
	echo "<br /><br />";
	







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
	//echo docpop('classums', 'class averages:');
	//echo "<input type='text' name='classums' value='$classums' size='50'>\n<br />\n";
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

	$expId = $_GET['expId'];
	$lpfilt = ($_POST['lpfilt']) ? $_POST['lpfilt'] : '1';
	$hpfilt = ($_POST['hpfilt']) ? $_POST['hpfilt'] : '0';
	$mask_radius = ($_POST['mask_radius']) ? $_POST['mask_radius'] : '1';
	$mask_dropoff = ($_POST['mask_dropoff']) ? $_POST['mask_dropoff'] : '0';
	$niter = $_POST['transalign_iter'];
	//$classums = $_POST['classums'];
	$new_classums = $_POST['new_classums'];
	$outdir = $_POST['outdir'];
	$runid = $_POST['runid'];
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	$command = "csh $outdir/$runid/{$runid}_imagicReclassifyClassums.job";

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
	
	
		
	$text = "";
	$text .= "imagicReclassifyClassums.py";
	$text .= " --classid=$classid --runid=$runid --oldstack=$filename --lp=$lpfilt";
	$text .= " --hp=$hpfilt --mask=$mask_radius --mask_d=$mask_dropoff --niter=$niter --numaverages=$new_classums";

	/*// generate the jobfile that will call the imagic batch file
	$jobtext = "";
	$jobtext.= "#PBS -l nodes=1:ppn=1\n";
	$jobtext.= "#PBS -l walltime=240:00:00\n";
	$jobtext.= "#PBS -l cput=240:00:00\n";
	$jobtext.= "#PBS -m e\n";
	$jobtext.= "#PBS -r n\n\n";
	$jobtext.= "cd $outdir/$runid\n";
	$jobtext.= "chmod 755 imagicReclassifyClassums.batch\n";
	$jobtext.= "./imagicReclassifyClassums.batch\n";
	*/

	/*
	// output the actual batch file that will be inputted into IMAGIC
	$text = "";
	$text .= "#!/bin/csh -f\n";	
	$text .= "setenv IMAGIC_BATCH 1\n";
	$text .= "cd $outdir/$runid\n";
	if (substr($indir,-1,1)!='/') {
		$indir.='/';
	}
	if (substr($filename,-4,4)==".img") {
		$filename = ereg_replace(".img","",$filename); 
	}
	if (substr($filename,-4,4)==".hed") {
		$filename = ereg_replace(".hed","",$filename); 
	}
	$text .= "ln -s $filename.img start_stack.img\n";
	$text .= "ln -s $filename.hed start_stack.hed\n";
	$text .= "/usr/local/IMAGIC/stand/copyim.e <<EOF > imagicReclassifyClassums.log\n";
	$text .= "start_stack\n";
	$text .= "classums\n";
	$text .= "EOF\n";
	$text .= "/usr/local/IMAGIC/stand/headers.e <<EOF >> imagicReclassifyClassums.log\n";
	$text .= "classums\n";
	$text .= "write\n";
	$text .= "wipe\n";
	$text .= "all\n";
	$text .= "EOF\n";
	$text .= "/usr/local/IMAGIC/incore/incprep.e <<EOF >> imagicReclassifyClassums.log\n"; 
	$text .= "NO\n";
	$text .= "classums\n";
	$text .= "classums_filt\n";
	$text .= "$hpfilt\n";
	$text .= "0.0\n";
	$text .= "$lpfilt\n";
	$text .= "$mask_radius,$mask_dropoff\n";
	$text .= "10.0\n";
	$text .= "NO\n";
	$text .= "EOF\n";
	$text .= "/usr/local/IMAGIC/align/alimass.e <<EOF >> imagicReclassifyClassums.log\n"; 
	$text .= "NO\n";
	$text .= "classums_filt\n";
	$text .= "classums_filt_cent\n";
	$text .= "TOTSUM\n";
	$text .= "CCF\n";
	$text .= "0.2\n";
	$text .= "$niter\n";
	$text .= "EOF\n";
	$text .= "/usr/local/IMAGIC/stand/testim.e <<EOF >> imagicReclassifyClassums.log\n";
	$text .= "msamask\n";
	$text .= "$box_size,$box_size\n";
	$text .= "Real\n";
	$text .= "disc\n";
	$text .= "$mask_radius\n";
	$text .= "EOF\n";
	$text .= "/usr/local/IMAGIC/msa/msa.e <<EOF >> imagicReclassifyClassums.log\n";
	$text .= "fresh_msa\n";
	$text .= "modulation\n";
	$text .= "classums_filt_cent\n";
	$text .= "NO\n";
	$text .= "msamask\n";
	$text .= "eigenimages\n";
	$text .= "pixel_coordinates\n";
	$text .= "eigen_pixels\n";
	$text .= "50\n";
	$text .= "69\n";
	$text .= "0.8\n";
	$text .= "msa\n";
	$text .= "EOF\n";
	$text .= "/usr/local/IMAGIC/msa/classify.e <<EOF >> imagicReclassifyClassums.log\n";
	$text .= "images/volumes\n";
	$text .= "classums_filt_cent\n";
	$text .= "0\n";
	$text .= "69\n";
	$text .= "yes\n";
	$text .= "$new_classums\n";
	$text .= "classification\n";
	$text .= "EOF\n";
	$text .= "/usr/local/IMAGIC/msa/classum.e <<EOF >> imagicReclassifyClassums.log\n";
	$text .= "classums_filt_cent\n";
	$text .= "classification\n";
	$text .= "reclassified_classums\n";
	$text .= "no\n";
	$text .= "none\n";
	$text .= "0\n";
	$text .= "EOF\n";
	$text .= "/usr/local/IMAGIC/incore/excopy.e <<EOF >> imagicReclassifyClassums.log\n";
	$text .= "sort\n";
	$text .= "reclassified_classums\n";
	$text .= "reclassified_classums_sorted\n";
	$text .= "index\n";
	$text .= "114\n";
	$text .= "down\n";
	$text .= "0\n";
	$text .= "EOF\n\n";
	$text .= "rm reclassified_classums.*\n";
	$text .= "rm classums.*\n";
	*/

	// write to jobfile
	$jobfile = "{$runid}_imagicReclassifyClassums.job";
	$tmpjobfile = "/tmp/$jobfile";
	$f = fopen($tmpjobfile,'w');
	fwrite($f,$text);
	fclose($f);

	/*// write batchfile
	$batchfile = "imagicReclassifyClassums.batch";
	$tmpbatchfile = "/tmp/$batchfile";
	$f = fopen($tmpbatchfile, 'w');
	fwrite($f,$text);
	fclose($f);
	*/
	// create appion directory & copy job & batch files
	$cmd = "mkdir -p $outdir/$runid;\n";
	$cmd.= "cp $tmpjobfile $outdir/$runid/$jobfile;\n";
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

/*function generateAnchorSet() {		// use 3 class averages to generate a model and an anchor-set of projections
					// also, this can be merged together with the processClasses() function

}

function generateBatchRefinement() {
	$expId = $_GET['expId'];
	processing_header("IMAGIC Job Generator","IMAGIC Job Generator",$javafunc);

	$header.= "#PBS -l nodes=1:ppn=1\n";
	$header.= "#PBS -l walltime=".$_POST['walltime'].":00:00\n";
	$header.= "#PBS -l cput=".$_POST['cput'].":00:00\n";
	$header.= "#PBS -m e\n";
	$header.= "#PBS -r n\n\n";
	$clusterjob = "# stackId: $stackidval\n";
	$stackId=$_POST['stackId']; // need to specify classes, manual picking should probably be employed prior to reconstruction
	echo "your classes are $classes";
	// change directory to working directory
	// call the first file to be executed
	// call the second file to be executed
	// ... etc. 
	processing_footer();
	exit;
}

function generateIteration() {
	// #!/bin/csh -f
	// setenv IMAGIC_BATCH 1
	// set i=$startIteration
	// while (i<$endIteration_1
}
*/
?>
