<?php

/* 






*/


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
	// get session info and experiment info
	$expId=$_GET['expId'];
	$reclassId=$_GET['reclassId'];
	$norefId=$_GET['norefId'];
	$norefClassId=$_GET['norefClassId'];
	$clusterId=$_GET['clusterId'];
	$tsId=$_GET['templateStackId'];
//	$imagicClusterId=$_GET['imagicClusterId'];
	$projectId=getProjectId();
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$outdir=$sessioninfo['Image path'];
		$outdir=ereg_replace("leginon","appion",$outdir);
		$outdir=ereg_replace("rawdata","init_models",$outdir);
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='output_directory' value='$outdir'>\n";
	}

	if ($expId){
		$formaction=$_SERVER['PHP_SELF']."?expId=$expId";
	}

	$javafunc .= writeJavaPopupFunctions('appion');
	processing_header("IMAGIC 3d0 Model Generator","IMAGIC 3d0 Model Generator",$javafunc);

	// write out errors if any came up
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='imagic3d0' method='post' action='$formaction'><br />\n";

	// get session info and experiment info
	$expId=$_GET['expId'];
	$reclassId=$_GET['reclassId'];
	$norefId=$_GET['norefId'];
	$norefClassId=$_GET['norefClassId'];
	$projectId=getProjectId();
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$outdir=$sessioninfo['Image path'];
		$outdir=ereg_replace("leginon","appion",$outdir);
		$outdir=ereg_replace("rawdata","init_models",$outdir);
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='output_directory' value='$outdir'>\n";
	}

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
	// get reference-free classification parameters from the clusterId
	$clusterdata = $particle->getClusteringStacks($expId,"$projectId","False");
	//print_r($clusterdata);
	foreach ($clusterdata as $key => $clusterinfo) {
		if ($clusterinfo[DEF_id] == $clusterId) {
			$position = $key;
			$clusterparams = array();
			foreach ($clusterdata[$position] as $key => $param) {
				$clusterparams[$key] = $param;
			}     
		}
	}
	// get parameters from templateStackId
	$tsdata = $particle->getTemplateStacksFromSession($expId);
	if ($tsdata && count($tsdata)) {
		foreach ($tsdata as $key => $tsinfo) {
			if ($tsinfo[DEF_id] == $tsId) {
				$position = $key;
				$tsparams = array();
				foreach ($tsdata[$position] as $key => $param) {
					$tsparams[$key] = $param;
				}
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
		$projectiontable.= "</tr></table>\n<br>";
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
		$projectiontable.= "</tr></table>\n<br>";
		echo $projectiontable;
		$display_keys = array();
		//$display_keys['description']=$norefclassparams['description'];
		$display_keys['# class averages']=$norefclassparams['num_classes'];
		foreach($display_keys as $k=>$v) {
			echo formatHtmlRow($k,$v);
		}
	}
	// if coming from new alignment pipeline using clusterId 
	elseif ($clusterId) {
		$clusterpath = $clusterparams['path'];
		$clusterclassfile = $clusterparams['avg_imagicfile'];
		if (ereg(".img", $clusterclassfile)) $clusterclassfile = str_replace(".img", "", $clusterclassfile);
		if (ereg(".hed", $clusterclassfile)) $clusterclassfile = str_replace(".hed", "", $clusterclassfile);
		$clusterclassimgfile = $clusterpath."/".$clusterclassfile.".img";
		$clusterclasshedfile = $clusterpath."/".$clusterclassfile.".hed";
		$projectiontable.= "<table border='0', width='50'>";
		//$projectiontable.= "<tr>".apdivtitle("3 initial projections from run ".$runname." are:")."</tr>";
		$projectiontable.= "<tr>\n";
		foreach ($projections as $key => $image) {
			$num = $key + 1;
			$projectiontable.= "<td rowspan='30' align='center' valign='top'>";
			$projectiontable.= "<img src='getstackimg.php?hed=$clusterclasshedfile&img=$clusterclassimgfile&n=".$image."&t=80&b=1&uh=0'><br/>\n";
			$projectiontable.= "<i>projection $num</i></td>\n";
		}
		$projectiontable.= "</tr></table>\n<br>";
		echo $projectiontable;
		$display_keys = array();
		//$display_keys['description']=$norefclassparams['description'];
		$display_keys['# class averages']=$clusterparams['num_classes'];
		foreach($display_keys as $k=>$v) {
			echo formatHtmlRow($k,$v);
		}
	}
	// if coming from template stacks
	elseif ($tsId) {
		$tspath = $tsparams['path'];
		$tsfile = $tsparams['templatename'];
		if (ereg(".img", $tsfile)) $tsfile = str_replace(".img", "", $tsfile);
		if (ereg(".hed", $tsfile)) $tsfile = str_replace(".hed", "", $tsfile);
		$tsimgfile = $tspath."/".$tsfile.".img";
		$tshedfile = $tspath."/".$tsfile.".hed";
		$projectiontable.= "<table border='0', width='50'>";
		//$projectiontable.= "<tr>".apdivtitle("3 initial projections from run ".$runname." are:")."</tr>";
		$projectiontable.= "<tr>\n";
		foreach ($projections as $key => $image) {
			$num = $key + 1;
			$projectiontable.= "<td rowspan='30' align='center' valign='top'>";
			$projectiontable.= "<img src='getstackimg.php?hed=$tshedfile&img=$tsimgfile&n=".$image."&t=80&b=1&uh=0'><br/>\n";
			$projectiontable.= "<i>projection $num</i></td>\n";
		}
		$projectiontable.= "</tr></table>\n<br>";
		echo $projectiontable;
		$display_keys = array();
		$display_keys['# class averages']=$tsparams['numimages'];
		foreach($display_keys as $k=>$v) {
			echo formatHtmlRow($k,$v);
		}
	}

	else echo "error: there are no class average runs for the initial model determination";
	$default_num_classes = $display_keys['# class averages'];
//	$numrun = count($particle->getImagic3d0NoRefModelsFromSessionId($expId));
//	$numrun+= count($particle->getImagic3d0ReclassifiedModelsFromSessionId($expId));
//	$numrun+= count($particle->get3d0ClusterModelsFromSessionId($expId));
//	$numrun+= count($particle->get3d0ImagicClusterModelsFromSessionId($expId));

	$numrun = 1;
	while (file_exists($outdir."/model".$numrun))
		$numrun += 1;
	$newrun = $numrun;

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// define default variables
	$outdir = ($_POST[output_directory]) ? $_POST[output_directory] : $outdir;
	$runid = ($_POST[runid]) ? $_POST[runid] : "model".$newrun;
	$symmetry = ($_POST[symmetry]) ? $_POST[symmetry] : "c1";

	// define documentation
	$doc_runname = docpop('runid', '<t><b>Run Name:</b>');
	$doc_outdir = docpop('outdir', '<b>Output Directory:</b>');
	$doc_description = docpop('descr', '<b>Description of 3d Refinement:</b>');
	$doc_projections = docpop('choose_projections', 'Choose 3 projections:');
	$doc_symmetry = docpop('symmetry', 'Symmetry');
	$doc_num_classaverages = docpop('num_classaverages', 'Number of class averages to use');
	$doc_mass = docpop('mass', '<b>Approximate mass in Kd</b>');

	// form for output directory & runid
	echo "<TABLE cellspacing='10' cellpadding='10'><tr><td>";
	echo openRoundBorder();
	echo "	<b> $doc_outdir</b> <input type='text' name='output_directory' value='$outdir' size='50'><br /><br />\n
		<b> $doc_runname</b> <input type='text' name='runid' value='$runid' size='20'><br /><br />\n
		<b> $doc_description</b><br><textarea name='description' rows='3' cols='50'>$rundescrval</textarea>\n";
	echo closeRoundBorder();
	echo "</td></tr></table>";

	echo "<input type='text' name='choose_projections' value='$newprojections' size='10'> $nbsp $doc_projections\n";
	echo "<input type='hidden' name='fileorig' value=$noreffile>";
	echo "<input type='hidden' name='norefid' value=$norefId>";
	echo "<input type='hidden' name='norefClassId' value=$norefClassId>";
	echo "<input type='hidden' name='reclassid' value=$reclassId>";
	echo "<input type='hidden' name='clusterId' value=$clusterId>";
	echo "<input type='hidden' name='tsId' value=$tsId>";
//	echo "<input type='hidden' name='imagicClusterId' value=$imagicClusterId>";	

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
	echo "<br> <TABLE CLASS='tableborder' BORDER='1' CELLPADDING=4 CELLSPACING=4>
	<tr>\n";
	foreach ($display_keys as $k => $key) {
		$id = "$key";
		echo "	<td align='center' bgcolor='$bgcolor'> 
			<font class='sf'> 
			<a href='#' id=\"$id\" onMouseOver='popLayer(\"$key\", \"$id\")' onMouseOut='hideLayer()'>
			$key 
			</a></font></td>\n";
	}
	echo"  </tr><br>\n";

	// define default parameters for 0 iteration
	$symmetry = ($_POST['symmetryn']) ? $_POST['symmetryn'] : "";

	$syms = $particle->getSymmetries();

	$euler_ang_inc = ($_POST['euler_ang_incn']) ? $_POST['euler_ang_incn'] : "5";
	$num_classums = ($_POST['num_classumsn']) ?  $_POST['num_classumsn'] : $default_num_classes;
	$hamming_window = ($_POST['hamming_windown']) ?$_POST['hamming_windown'] : "0.8";
	$obj_size = ($_POST['obj_sizen']) ? $_POST['obj_sizen'] : "0.8";
	$repalignments = ($_POST['repalignmentsn']) ? $_POST['repalignmentsn'] : "1";
	$amask_dim = ($_POST['amask_dimn']) ? $_POST['amask_dimn'] : "0.04";
	$amask_lp = ($_POST['amask_lpn']) ? $_POST['amask_lpn'] : "0.5";
	$amask_sharp = ($_POST['amask_sharpn']) ? $_POST['amask_sharpn'] : "0.5";
	$amask_thresh = ($_POST['amask_threshn']) ? $_POST['amask_threshn'] : "15";
	$mrarefs_ang_inc = ($_POST['mrarefs_ang_incn']) ? $_POST['mrarefs_ang_incn'] : "25";
	$forw_ang_inc = ($_POST['forw_ang_incn']) ? $_POST['forw_ang_incn'] : "25";

	// print form with user input for all values
	echo "<tr>
      		<td bgcolor='$rcol'><b>0</b></td>
		<td bgcolor='$rcol'><SELECT NAME='symmetryn'><OPTION VALUE=''>Select One</OPTION>\n";
		foreach ($syms as $sym) {
			echo "<OPTION VALUE='$sym[DEF_id]'";
			if ($sym['DEF_id']==$_POST['symmetry']) echo " SELECTED";
			echo ">$sym[symmetry]";
			if ($sym['symmetry']=='C1') echo " (no symmetry)";
			echo "</OPTION>\n";
		}
		echo "</td>
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
	echo "</table><br>";

	echo "</b><input type='text' name='mass' value='$mass' size='4'> $doc_mass <br><br>";	
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "<br><br>";
	echo "<INPUT TYPE='hidden' NAME='projectId' VALUE='$projectId'>";
	echo getSubmitForm("run imagic");
	echo "</form>\n";

	processing_footer();
	exit;
}

function create3d0() {
	$expId = $_GET['expId'];
	$projectId = $_GET['projectId'];
	$fileorig = $_POST['fileorig'];
	$norefId = $_POST['norefid'];
	$norefClassId = $_POST['norefClassId'];
	$clusterId = $_POST['clusterId'];
	$tsId = $_POST['tsId'];
//	$imagicClusterId = $_POST['imagicClusterId'];
	$reclassId = $_POST['reclassid'];
	$outdir = $_POST['output_directory'];
	$runid = $_POST['runid'];
	$projections = $_POST['choose_projections'];
	$symmetry = $_POST['symmetryn'];
	$euler_ang_inc = $_POST['euler_ang_incn'];
	$num_classums = $_POST['num_classumsn'];
	$hamming_window = $_POST['hamming_windown'];
	$obj_size = $_POST['obj_sizen'];
	$repalignments = $_POST['repalignmentsn'];
	$amask_dim = $_POST['amask_dimn'];
	$amask_lp = $_POST['amask_lpn'];
	$amask_sharp = $_POST['amask_sharpn'];
	$amask_thresh = $_POST['amask_threshn'];
	$mrarefs_ang_inc = $_POST['mrarefs_ang_incn'];
	$forw_ang_inc = $_POST['forw_ang_incn'];
	$description = $_POST['description'];
	$mass = $_POST['mass'];
	$commit = ($_POST['commit']=="on") ? '--commit' : '';
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	// create python command that will launch job
	$command = "imagic3d0.py ";
	$command.="--projectid=".getProjectId();
	if ($reclassId) {
		$command.=" --reclassId=$reclassId";
	}
	elseif ($norefClassId) {
		$command.=" --norefClassId=$norefClassId";
	}
	elseif ($clusterId) {
		$command.=" --clusterId=$clusterId";
	}
	elseif ($tsId) {
		$command.=" --templateStackId=$tsId";
	}
/*	elseif ($imagicClusterId) {
		$command.=" --imagicClusterId=$imagicClusterId";
	}
*/	else jobform("error: there are no class average runs for the initial model determination");
	$command.= " --runname=$runid";
	$command.= " --rundir=$outdir/$runid";
	$command.= " --3_projections=$projections";
	$command.= " --symmetry=$symmetry";
	$command.= " --euler_ang_inc=$euler_ang_inc";
	$command.= " --num_classums=$num_classums";
	$command.= " --ham_win=$hamming_window";
	$command.= " --object_size=$obj_size";
	$command.= " --repalignments=$repalignments";
	$command.= " --amask_dim=$amask_dim";
	$command.= " --amask_lp=$amask_lp";
	$command.= " --amask_sharp=$amask_sharp";
	$command.= " --amask_thresh=$amask_thresh";
	$command.= " --mrarefs_ang_inc=$mrarefs_ang_inc";
	$command.= " --forw_ang_inc=$forw_ang_inc";
	$command.= " --description=\"$description\"";
	$command.= " --mass=$mass";
	if ($commit) $command.= " --commit";
	else $command.=" --no-commit";

	if ($_POST['process']=="run imagic") {
		if (!($user && $pass)) jobform("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'create3d0');
		// if errors:
		if ($sub) jobform("<b>ERROR:</b> $sub");
	}

	processing_header("IMAGIC 3d0 Job Generator","IMAGIC 3d0 Job Generator",$javafunc);

	echo"
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>Alignment Command:</B><br><br>
	$command<br><br>
	 </TD></tr>
	 </table>\n";

	processing_footer();
	exit;

}










?>
