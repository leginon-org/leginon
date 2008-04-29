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
require  "inc/viewer.inc";
require  "inc/project.inc";

if ($_POST['process']) { // Create command
	reRunNoRefAlign();
} else { // Create the form page
	createNoRefAlignSummary();
}


function createNoRefAlignSummary() {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=$_POST['projectId'];

	$javascript="<script src='../js/viewer.js'></script>\n";

	writeTop("NoRef Class Report","Reference-free Classification Summary Page", $javascript);

	echo"<form name='viewerform' method='POST' ACTION='$formAction'>
	<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	echo "</FORM>\n";

	// --- Get NoRef Data
	$particle = new particledata();

	# find each noref entry in database
	$norefIds = $particle->getNoRefIds($sessionId);
	$norefruns=count($norefIds);

	foreach ($norefIds as $norefid) {
		//print_r ($norefid);
		# get list of noref parameters from database
		$r = $particle->getNoRefParams($norefid['DEF_id']);
		$s = $particle->getStackParams($r['REF|ApStackData|stack']);
		echo divtitle("NOREF ALIGN: <FONT class='aptitle'>".$r['name']
		."</FONT> (ID: <FONT class='aptitle'>".$norefid[DEF_id]."</FONT>)");
		//echo divtitle("NoRef Id: $norefid[DEF_id]");
		echo"<FORM NAME='numclass' METHOD='POST' ACTION='$formAction'>\n";
		echo "<table border='0' >\n";

		$norefnum = $norefid['DEF_id'];
		if ($r['first_ring']) {
			echo "<tr><td bgcolor='#bbffbb'>";
			echo "<a href='runNoRefClassify.php?expId=$expId&norefId=$norefnum'>";
			echo "Average particles into classes</a>";
			echo"</td></tr>";	
		}

		//$display_keys['name']=$r['name'];
		$display_keys['description']=$r['description'];
		$display_keys['time']=$r['DEF_timestamp'];
		$display_keys['path']=$r['path'];
		$display_keys['# particles']=$r['num_particles'];
		$display_keys['lp filt']=$r['lp_filt'];
		$display_keys['particle & mask diam']=$r['particle_diam']." / ".$r['mask_diam'];
		$display_keys['stack run name']=$s['shownstackname'];

		foreach($display_keys as $k=>$v) {
			echo formatHtmlRow($k,$v);
		}
		$norefpath = $r[path]."/";

		$classIds = $particle->getNoRefClassRuns($norefid['DEF_id']);
		$classnum = count($classIds);
		foreach ($classIds as $classid) {
			$classfile = $norefpath.$classid[classFile].".img";
			$varfile = $norefpath.$classid[varFile].".img";
			$totimg = $classid[num_classes];
			$endimg = $classid[num_classes]-1;
			echo "
			<tr><td bgcolor='#ffcccc' colspan=2>
				Averaged into $totimg classes: &nbsp;&nbsp;&nbsp;
				<a target='stackview' href='viewstack.php?file=$classfile&endimg=$endimg&expId=$sessionId&norefId=$norefid[DEF_id]&norefClassId=$classid[DEF_id]'>View Class Averages</a>";
			if ($classid[varFile]) {
				echo "
				<font size=-1>&nbsp;
					<a target='stackview' href='viewstack.php?file=$varfile&endimg=$endimg&expId=$sessionId&norefId=$norefid[DEF_id]&norefClassId=$classid[DEF_id]'>[variance]</a>
				</font>";
			}
			echo"</td></tr>";
		
			//echo "<tr><td bgcolor='#ff4444'>"; print_r ($classid); echo "</td></tr>";
			//foreach($classid as $k=>$v) {
			//	echo formatHtmlRow($k,$v);
			//}
		}

		echo"</TABLE>\n";
		echo "</FORM>\n";
		echo"<P>\n";
	}
	writeBottom();
	exit;
};


?>
