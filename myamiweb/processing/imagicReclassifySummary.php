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

createReclassifySummary();


function createReclassifySummary() {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$javascript.= editTextJava();

	processing_header("Reclassification Report","Reference-free Reclassification Summary Page", $javascript);

	// --- Create class instance
	$particle = new particledata();

	# find each reclassification entry in database
	$reclassData = $particle->getImagicReclassFromSessionId($expId);
	$numreresults=count($particle->getImagicReclassFromSessionId($expId));

	if ($reclassData) {
		$shown = array();
		foreach($reclassData as $reclassinfo) { 
			if (is_array($reclassinfo)) {
				$shown[]=$reclassinfo;
			}
		}
		$reclasstable="<form name='reclassform' method='post' action='$formAction'>\n";
		foreach ($shown as $r) {
			$reclasstable.=reclassEntry($r,$particle);
		}
		$reclasstable.="</form>\n";
	}

	if ($shown) echo $reclasstable;
	else echo "<B>Project does not contain any Reclassifications.</B>\n";
	processing_footer();
	exit;
}

function reclassEntry($reclassId, $particle, $hidden=False) {
	$expId = $_GET['expId'];
	$reclassnum = $reclassId['DEF_id'];

	// update description
	if ($_POST['updateDesc'.$reclassnum])
		updateDescription('ApImagicReclassifyData',$reclassnum,$_POST['newdescription'.$reclassnum]);

	$i = $reclassId;

	// get file path and filename
	$reclassfile = $i['path']."/".$i['runname']."/reclassified_classums_sorted.img";
	$reclassfilepath = $i['runname']."/reclassified_classums_sorted.img";

	// table formatting & link to viewstack
	$j = "Ref-free Run: <font class='aptitle'>";
	$j.= $i['runname'];
	$j.= "</font> (ID: <font class='aptitle'>$reclassnum</font>)";
	$j.= " <input class='edit' type='submit' name='hideReclassification".$reclassnum."' value='hide'>";
	$reclasstable.= apdivtitle($j);
	$reclasstable.= "<table border='0' width='600'>\n";
	$reclasstable.= "<tr><td colspan='2' bgcolor='#bbffbb'>";
	$reclasstable.= "<a href='viewstack.php?file=$reclassfile&expId=$expId&reclassId=$reclassnum'>";
	$reclasstable.= "View reclassification results & choose projections for 3d0 initial model</a>";
	$reclasstable.="</td></tr>";

	// get reference-free alignment data from which reclassification occured
	$norefclassnum = $i['REF|ApNoRefClassRunData|norefclass'];
	$norefclassparams = $particle->getNoRefClassRunData($norefclassnum);
	$norefid = $norefclassparams['REF|ApNoRefRunData|norefRun'];
	$norefparams = $particle->getNoRefParams($norefid);
	$norefpath = $norefparams['path'];
	$filepath = $norefclassparams['classFile'];
	$file = $norefpath.'/'.$filepath;

	# add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($reclassnum,$i['description']) : $i['description'];
	
	$display_keys = array();
	$display_keys['description']=$descDiv;
	$display_keys['time']=$i['DEF_timestamp'];
	$display_keys['path']=$i['path'];
	$display_keys['# class averages']=$i['numaverages'];
	if ($i['lowpass']) $display_keys['lp filt']=$i['lowpass'];
	if ($i['highpass']) $display_keys['hp filt']=$i['highpass'];
	if ($i['maskradius'] & $i['maskdropoff']) $display_keys['mask radius & dropoff']=$i['maskradius'].' / '.$i['maskdropoff'];
	$norefstr = "<a href='viewstack.php?file=$file".".img"."&expId=$expId&norefid=$norefid&norefClassId=$norefclassnum"."'>".$filepath."</a>";
	$display_keys['Reference-free class run'] = $norefstr;
			
	foreach($display_keys as $k=>$v) {
		$reclasstable.= formatHtmlRow($k,$v);
	}

	$reclasstable.="</table>\n";
	$reclasstable.="<p>\n";
	return $reclasstable;
}

?>
