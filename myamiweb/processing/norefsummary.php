<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require  "inc/particledata.inc";
require  "inc/processing.inc";
require  "inc/leginon.inc";
require  "inc/project.inc";

if ($_POST['process']) { // Create command
	reRunNoRefAlign();
} 
else { // Create the form page
	createNoRefAlignSummary();
}


function createNoRefAlignSummary() {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	if ($_GET['showHidden']) $formAction.="&showHidden=True";

	$javascript.= editTextJava();

	processing_header("NoRef Class Report","Reference-free Classification Summary Page", $javascript);

	// --- Get NoRef Data
	$particle = new particledata();

	# find each noref entry in database
	$norefData = $particle->getNoRefIds($expId, True);
	$norefruns=count($norefData);

	if ($norefData) {
		// separate hidden from shown;
		$shown = array();
		$hidden = array();
		foreach($norefData as $norefinfo) { 
			if (is_array($norefinfo)) {
				$norefId=$norefinfo['DEF_id'];
				// first update hide value
				if ($_POST['hideNoref'.$norefId]) {
					$particle->updateHide('ApNoRefRunData',$norefId,1);
					$norefinfo['hidden']=1;
				}
				elseif ($_POST['unhideNoref'.$norefId]) {
					$particle->updateHide('ApNoRefRunData',$norefId,0);
					$norefinfo['hidden']='';
				}
				if ($norefinfo['hidden']==1) $hidden[]=$norefinfo;
				else $shown[]=$norefinfo;
			}
		}
		$noreftable="<form name='norefform' method='post' action='$formAction'>\n";
		foreach ($shown as $nr) $noreftable.=norefEntry($nr,$particle);
		// show hidden norefs
		if ($_GET['showHidden'] && $hidden) {
			if ($shown) $noreftable.="<hr />\n";
			$noreftable.="<b>Hidden Norefs</b> ";
			$noreftable.="<a href='".$_SERVER['PHP_SELF']."?expId=$expId'>[hide]</a><br />\n";
			foreach ($hidden as $nr) $noreftable.= norefEntry($nr,$particle,True);
		}
		$noreftable.="</form>\n";
	}

	if ($hidden && !$_GET['showHidden']) echo "<a href='".$formAction."&showHidden=True'>[Show Hidden Alignments]</a><br />\n";

	if ($shown || $hidden) echo $noreftable;
	else echo "<B>Project does not contain any Alignments.</B>\n";
	processing_footer();
	exit;
}

function norefEntry($norefid, $particle, $hidden=False) {
	//print_r ($norefid);
	$expId = $_GET['expId'];
	$norefnum = $norefid['DEF_id'];

	// update description
	if ($_POST['updateDesc'.$norefnum])
		updateDescription('ApNoRefRunData',$norefnum,$_POST['newdescription'.$norefnum]);
	# get list of noref parameters from database
	$r = $particle->getNoRefParams($norefnum);
	$s = $particle->getStackParams($r['REF|ApStackData|stack']);
	$j = "Ref-free Run: <font class='aptitle'>";
	$j.= $r['name'];
	$j.= "</font> (ID: <font class='aptitle'>$norefnum</font>)";
	if ($hidden) $j.= " <input class='edit' type='submit' name='unhideNoref".$norefnum."' value='unhide'>";
	else $j.= " <input class='edit' type='submit' name='hideNoref".$norefnum."' value='hide'>";
	$noreftable.= apdivtitle($j);
	$noreftable.= "<table border='0' width='600'>\n";
	if ($r['first_ring']) {
		$noreftable.= "<tr><td colspan='2' bgcolor='#bbffbb'>";
		$noreftable.= "<a href='runNoRefClassify.php?expId=$expId&norefId=$norefnum'>";
		$noreftable.= "Average particles into classes</a>";
		$noreftable.="</td></tr>";	
	}

	# add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($norefnum,$r['description']) : $r['description'];
	
	$display_keys = array();
	$display_keys['description']=$descDiv;
	$display_keys['time']=$r['DEF_timestamp'];
	$display_keys['path']=$r['path'];
	$display_keys['# particles']=$r['num_particles'];
	if ($r['lp_filt']) $display_keys['lp filt']=$r['lp_filt'];
	$display_keys['particle & mask diam']=$r['particle_diam']." / ".$r['mask_diam'];
	$stackstr = "<a href='stackreport.php?expId=$expId&sId=".$s['stackId']."'>".$s['shownstackname']."</a>";
	$display_keys['stack run name'] = $stackstr;
			
	$dendrofile = $r['path']."/dendrogram.png";
	if(file_exists($dendrofile)) {
		$dendrotext = "<a href='loadimg.php?filename=$dendrofile'>dendrogram.png</a>";
		$display_keys['dendrogram']=$dendrotext;
	}
	foreach($display_keys as $k=>$v) $noreftable.= formatHtmlRow($k,$v);

	$classIds = $particle->getNoRefClassRuns($norefnum);
	$classnum = count($classIds);
	foreach ($classIds as $classid) {
		$norefpath = $r['path']."/";
		$classfile = $norefpath.$classid[classFile].".img";
		if(!file_exists($classfile)) {
			$norefpath = $r['path']."/".$r['name']."/";
			$classfile = $norefpath."/".$classid[classFile].".img";
		}
		if(!file_exists($classfile)) continue;
		$varfile = $norefpath.$classid[varFile].".img";
		$totimg = $classid[num_classes];
		$endimg = $classid[num_classes]-1;
		$noreftable.= "<tr><td bgcolor='#ffcccc' colspan=2>";
		$noreftable.= "<b>$totimg</b> classes: &nbsp;&nbsp;&nbsp;";
		$noreftable.= "<a target='stackview' href='viewstack.php?file=$classfile&endimg=$endimg&expId=$expId&";
		$noreftable.= "norefId=$norefid[DEF_id]&norefClassId=$classid[DEF_id]'>View Class Averages</a>";
		if ($classid[varFile] && file_exists($varfile)) {
			$noreftable.= "<font size=-1>&nbsp;";
			$noreftable.= " <a target='stackview' href='viewstack.php?file=$varfile&endimg=$endimg&expId=$expId&";
			$noreftable.= "norefId=$norefid[DEF_id]&norefClassId=$classid[DEF_id]'>[variance]</a>";
			$noreftable.= "</font>";
		}
		$noreftable.= "<font size=-2>&nbsp;&nbsp;(factor list: ".$classid[factor_list].")</font>";;	
		$noreftable.="</td></tr>";
	}
	$noreftable.="</table>\n";
	$noreftable.="<p>\n";
	return $noreftable;
}
?>
