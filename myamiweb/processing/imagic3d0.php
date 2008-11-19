<?php

/* 






*/
###########################################################
/*


MAY NEED TO CHANGE "norefId" to "classId" -- double check


*/
###########################################################

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";

// if you don't have stuff in the posts, go to generate3d0(); else jobform();
if ($_POST['process'])  {
	if (!$_POST['output_directory']) jobform("error: no output directory specified");
	// runid??
	if (!$_POST['symmetryn']) jobform("error: no symmetry specified");
	if (!$_POST['choose_projections']) jobform("error: 3 initial projections not specified for angular reconstitution");
	if (!$_POST['num_classumsn']) jobform("error: you did not specify which classums to use for the reconstruction");
	if (!$_POST['hamming_windown']) jobform("error: you did not specify a hamming window value");
	if (!$_POST['obj_sizen']) jobform("error: you did not specify the object size ");
	if (!$_POST['repalignmentsn']) jobform("error: you did not specify the number of reprojection alignments");
	if (!$_POST['amask_dimn']) jobform("error: you did not specify the automask dimension parameter");
	if (!$_POST['amask_lpn']) jobform("error: you did not specify the automask lp-filter parameter");
	if (!$_POST['amask_sharpn']) jobform("error: you did not specify the automask sharpness parameter");
	if (!$_POST['amask_threshn']) jobform("error: you did not specify the automask thresholding parameter");
	if (!$_POST['mrarefs_ang_incn']) jobform("error: you did not specify the angular increment of forward projections for MRA");
	if (!$_POST['forw_ang_incn']) jobform("error: you did not specify the angular increment of forward projections for euler angle refinement");
	create3d0();
}
else jobform();


function jobform($extra=false) {

	$javafunc .= writeJavaPopupFunctions('appion');
	processing_header("IMAGIC 3d0 Model Generator","IMAGIC 3d0 Model Generator",$javafunc);

	// write out errors if any came up
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";

	echo "<form name='imagic3d0' method='post' action='$formaction'><br />\n";

	// get session info and experiment info
	$expId=$_GET['expId'];
	$reclassId=$_GET['reclassId'];
	$norefId=$_GET['norefId'];
	$norefClassId=$_GET['norefClassId'];
	$projectId=getProjectFromExpId($expId);
	$sessiondata=displayExperimentForm($projectId,$expId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$outdir=$sessioninfo['Image path'];
		$outdir=ereg_replace("leginon","appion",$outdir);
		$outdir=ereg_replace("rawdata","init_models",$outdir);
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='output_directory' value='$outdir'>\n";
	}

############################

	// get reclassification parameters from reclassId & expId
	$particle = new particledata();
	$reclassData = $particle->getImagicReclassFromSessionId($expId);
	foreach ($reclassData as $key => $reclassinfo) {
		if ($reclassinfo[DEF_id] == $reclassId)	{
			$position = $key;
			$reclassparams = array();
			foreach ($reclassData[$position] as $key => $param) {
				$reclassparams[$key] = $param;
			}	
		}
	}
	// get reference-free classification parameters from the norefId
	$norefclassdata = $particle->getNoRefClassRuns($norefId);
	foreach ($norefclassdata as $key => $classinfo) {
		if ($classinfo[DEF_id] == $norefClassId) {
			$position = $key;
			$norefclassparams = array();
			foreach ($norefclassdata[$position] as $key => $param) {
				$norefclassparams[$key] = $param;			
			}
		}
	}


	// IMAGIC begins projections with [1] instead of [0]
	$projections=$_GET['projections'];
	$projections=explode(',', $projections);
	$projectionarray = array();
	foreach ($projections as $projection) {
		$newprojection = $projection + 1;
		$projectionarray[] = $newprojection;
	}
	$newprojections=implode(',', $projectionarray);

	// if coming from reclassification of reference-free run
	if ($reclassId) {
		// display results from reclassification
		$reclassimgfile = $reclassparams['path']."/".$reclassparams['runname']."/reclassified_classums_sorted.img";
		$reclasshedfile = $reclassparams['path']."/".$reclassparams['runname']."/reclassified_classums_sorted.hed";
		$runname = $reclassparams['runname'];
		$projectiontable.= "<table border='0', width='50'>";
		//$projectiontable.= "<tr>".apdivtitle("3 initial projections from run ".$runname." are:")."</tr>";
		$projectiontable.= "<tr>\n";
		foreach ($projections as $key => $image) {
			$num = $key + 1;
			$projectiontable.= "<td rowspan='30' align='center' valign='top'>";
			$projectiontable.= "<img src='getstackimg.php?hed=$reclasshedfile&img=$reclassimgfile&n=".$image."&t=80&b=1&uh=0'><br/>\n";
			$projectiontable.= "<i>projection $num</i></td>\n";
		}
		$projectiontable.= "</tr></table>\n<BR/>";
		echo $projectiontable;
		$display_keys = array();
		$display_keys['description']=$reclassparams['description'];
		$display_keys['# class averages']=$reclassparams['numaverages'];
		foreach($display_keys as $k=>$v) {
			echo formatHtmlRow($k,$v);
		}
	}
	// if coming from reference-free classification
	elseif ($norefClassId) {
		$norefparams = $particle->getNoRefParams($norefId);
		$norefpath = $norefparams['path'];
		$norefclassfile = $norefclassparams['classFile'];
		$norefclassimgfile = $norefpath."/".$norefclassfile.".img";
		$norefclasshedfile = $norefpath."/".$norefclassfile.".hed";
		
		$projectiontable.= "<table border='0', width='50'>";
		//$projectiontable.= "<tr>".apdivtitle("3 initial projections from run ".$runname." are:")."</tr>";
		$projectiontable.= "<tr>\n";
		foreach ($projections as $key => $image) {
			$num = $key + 1;
			$projectiontable.= "<td rowspan='30' align='center' valign='top'>";
			$projectiontable.= "<img src='getstackimg.php?hed=$norefclasshedfile&img=$norefclassimgfile&n=".$image."&t=80&b=1&uh=0'><br/>\n";
			$projectiontable.= "<i>projection $num</i></td>\n";
		}
		$projectiontable.= "</tr></table>\n<BR/>";
		echo $projectiontable;
		$display_keys = array();
		//$display_keys['description']=$norefclassparams['description'];
		$display_keys['# class averages']=$norefclassparams['num_classes'];
		foreach($display_keys as $k=>$v) {
			echo formatHtmlRow($k,$v);
		}
	}
	else echo "error: there are no class average runs for the initial model determination";

	$numrun = count($particle->getImagic3d0NoRefModelsFromSessionId($expId));
	$numrun+= count($particle->getImagic3d0ReclassifiedModelsFromSessionId($expId));
	$newrun = $numrun + 1;

	// define default variables
	$outdir = ($_POST[output_directory]) ? $_POST[output_directory] : $outdir;
	$runid = ($_POST[runid]) ? $_POST[runid] : "model".$newrun;
	$symmetry = ($_POST[symmetry]) ? $_POST[symmetry] : "c1";
	$num_classums = ($_POST[num_classums]) ? $_POST[num_classums] : "1-100";

	// define documentation
	$doc_runname = docpop('runid', '<t><b>Run Name:</b>');
	$doc_outdir = docpop('outdir', '<b>Output Directory:</b>');
	$doc_projections = docpop('choose_projections', 'Choose 3 projections:');
	$doc_symmetry = docpop('symmetry', 'Symmetry');
	$doc_num_classaverages = docpop('num_classaverages', 'Number of class averages to use');

	// form for output directory & runid
	echo "<TABLE cellspacing='10' cellpadding='10'><tr><td>";
	echo openRoundBorder();
	echo "<BR/><b> $doc_outdir</b> <input type='text' name='output_directory' value='$outdir' size='75'><br /><br />\n
		   <b> $doc_runname</b> <input type='text' name='runid' value='$runid' size='20'><br /><br />\n";
	echo closeRoundBorder();
	echo "</td></tr></TABLE><br />";

	echo "<input type='text' name='choose_projections' value='$newprojections' size='10'> $nbsp $doc_projections <br />\n";
	echo "<input type='hidden' name='fileorig' value=$noreffile>";
	echo "<input type='hidden' name='norefid' value=$norefId>";
	echo "<input type='hidden' name='norefClassId' value=$norefClassId>";
	echo "<input type='hidden' name='reclassid' value=$reclassId>";
	
	// keys and documentation for user input values
	$display_keys = array('itn', 
				'symmetry', 
				'euler_ang_inc', 
				'num_classums', 
				'ham_win', 
				'obj_size', 
				'repalignments', 
				'amask_dim', 
				'amask_lp', 
				'amask_sharp',
				'amask_thresh', 
				'mra_ang_inc', 
				'forw_ang_inc',);
	$bgcolor="#E8E8E8";
	echo "<BR/> <TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4>
	<tr>\n";
	foreach ($display_keys as $k => $key) {
		$id = "$key";
		echo "	<td align='center' bgcolor='$bgcolor'> 
			<font class='sf'> 
			<a href='#' id=\"$id\" onMouseOver='popLayer(\"$key\", \"$id\")' onMouseOut='hideLayer()'>
			$key 
			</a></font></td>\n";
	}
	echo"  </tr><BR/>\n";

	
	// define default parameters for 0 iteration
	$symmetry = ($_POST['symmetryn']) ? $_POST['symmetryn'] : "";
	$euler_ang_inc = ($_POST['euler_ang_incn']) ? $_POST['euler_ang_incn'] : "10";
	$num_classums = ($_POST['num_classumsn']) ? $_POST['num_classumsn'] : "";
	$hamming_window = ($_POST['hamming_windown']) ? $_POST['hamming_windown'] : "0.8";
	$obj_size = ($_POST['obj_sizen']) ? $_POST['obj_sizen'] : "0.8";
	$repalignments = ($_POST['repalignmentsn']) ? $_POST['repalignmentsn'] : "15";
	$amask_dim = ($_POST['amask_dimn']) ? $_POST['amask_dimn'] : "0.04";
	$amask_lp = ($_POST['amask_lpn']) ? $_POST['amask_lpn'] : "0.5";
	$amask_sharp = ($_POST['amask_sharpn']) ? $_POST['amask_sharpn'] : "0.5";
	$amask_thresh = ($_POST['amask_threshn']) ? $_POST['amask_threshn'] : "15";
	$mrarefs_ang_inc = ($_POST['mrarefs_ang_incn']) ? $_POST['mrarefs_ang_incn'] : "25";
	$forw_ang_inc = ($_POST['forw_ang_incn']) ? $_POST['forw_ang_incn'] : "25";

	// print form with user input for all values
	echo "<tr>
      		<td bgcolor='$rcol'><b>0</b></td>
			<td bgcolor='$rcol'><input type='text' NAME='symmetryn' SIZE='4' VALUE='$symmetry'></td>
       		<td bgcolor='$rcol'><input type='text' NAME='euler_ang_incn' SIZE='4' VALUE='$euler_ang_inc'></td>
       		<td bgcolor='$rcol'><input type='text' NAME='num_classumsn' SIZE='4' VALUE='$num_classums'></td>
        	<td bgcolor='$rcol'><input type='text' NAME='hamming_windown' SIZE='4' VALUE='$hamming_window'></td>
        	<td bgcolor='$rcol'><input type='text' NAME='obj_sizen' SIZE='4' VALUE='$obj_size'></td>
        	<td bgcolor='$rcol'><input type='text' NAME='repalignmentsn' SIZE='4' VALUE='$repalignments'></td>
        	<td bgcolor='$rcol'><input type='text' NAME='amask_dimn' SIZE='4' value='$amask_dim'>
        	<td bgcolor='$rcol'><input type='text' NAME='amask_lpn' SIZE='4' VALUE='$amask_lp'></td>
        	<td bgcolor='$rcol'><input type='text' NAME='amask_sharpn' SIZE='4' value='$amask_sharp'>
			<td bgcolor='$rcol'><input type='text' NAME='amask_threshn' SIZE='4' VALUE='$amask_thresh'>
        	<td bgcolor='$rcol'><input type='text' NAME='mrarefs_ang_incn' SIZE='4' VALUE='$mrarefs_ang_inc'></td>
        	<td bgcolor='$rcol'><input type='text' NAME='forw_ang_incn' SIZE='4' VALUE='$forw_ang_inc'></td>
     	  </tr>\n";
	echo "</table><BR/><BR/>";
	
	
	
	echo getSubmitForm("run imagic");
	echo "</form>\n";





	processing_footer();
	exit;
}

function create3d0() {
	$expId = $_GET['expid'];
	$fileorig = $_POST['fileorig'];
	$norefId = $_POST['norefid'];
	$norefClassId = $_POST['norefClassId'];
	$reclassId = $_POST['reclassid'];
	$outdir = $_POST['output_directory'];
	$runid = $_POST['runid'];
	$projections = $_POST['choose_projections'];
	$symmetry = $_POST['symmetryn'];
	$euler_ang_inc = $_POST['euler_ang_incn'];
	$num_classums = $_POST['num_classumsn'];
	$hamming_window = $_POST['hamming_windown'];
	$obj_size = $_POST['obj_sizen'];
	$repalignments = $_POST['repalignmentsn'] + 1;
	$amask_dim = $_POST['amask_dimn'];
	$amask_lp = $_POST['amask_lpn'];
	$amask_sharp = $_POST['amask_sharpn'];
	$amask_thresh = $_POST['amask_threshn'];
	$mrarefs_ang_inc = $_POST['mrarefs_ang_incn'];
	$forw_ang_inc = $_POST['forw_ang_incn'];
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	$command = "$outdir/$runid/{$runid}_imagic3d0.job";

	// create python command that will launch job
	$text = "";
	$text.= "imagic3d0.py";
	//$text.= " --fileorig=$fileorig";
	if ($reclassId) {
		$text.=" --reclassId=$reclassId";
	}
	elseif ($norefClassId) {
		$text.=" --norefClassId=$norefClassId";
	}
	else jobform("error: there are no class average runs for the initial model determination");
	$text.= " --runid=$runid --outdir=$outdir/$runid --3_projections=$projections --symmetry=$symmetry";
	$text.= " --euler_ang_inc=$euler_ang_inc --num_classums=$num_classums --ham_win=$hamming_window";
	$text.= " --object_size=$obj_size --repalignments=$repalignments --amask_dim=$amask_dim";
	$text.= " --amask_lp=$amask_lp --amask_sharp=$amask_sharp --amask_thresh=$amask_thresh";
	$text.= " --mrarefs_ang_inc=$mrarefs_ang_inc --forw_ang_inc=$forw_ang_inc";

	$jobfile = "{$runid}_imagic3d0.job";
	$tmpjobfile = "/tmp/$jobfile";
	$f = fopen($tmpjobfile,'w');
	fwrite($f,$text);
	fclose($f);

	// create appion directory & copy job file
	$cmd = "mkdir -p $outdir/$runid\n";
	$cmd.= "cp $tmpjobfile $outdir/$runid/$jobfile\n";
	$cmd.= "cd $outdir/$runid\n";
	$cmd.= "chmod 755 $jobfile\n";
	exec_over_ssh($_SERVER['HTTP_HOST'], $user, $pass, $cmd, True);

	if ($_POST['process']=="run imagic") {
		if (!($user && $pass)) jobform("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'create3d0');
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
