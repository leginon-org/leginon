<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');

if ($_POST['process']) { // Create command
	reRunClassifier();
} else { // Create the form page
	createClassifierSummary();
}


function createClassifierSummary() {
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

	$javascript="<script src='js/viewer.js'></script>\n";

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
		echo divtitle("NoRef Id: $norefid[DEF_id]");
		echo"<FORM NAME='numclass' METHOD='POST' ACTION='$formAction'>\n";
		# get list of noref parameters from database
		$r = $particle->getNoRefParams($norefid['DEF_id']);
		$s = $particle->getStackParams($r['REF|ApStackData|stack']);
		
		echo "<table border='0' >\n";

		$display_keys['name']=$r['name'];
		$display_keys['description']=$r['description'];
		$display_keys['time']=$r['DEF_timestamp'];
		$display_keys['path']=$r['norefPath'];
		$display_keys['lp filt']=$r['lp_filt'];
		$display_keys['particle diameter']=$r['particle_diam'];
		$display_keys['mask diameter']=$r['mask_diam'];
		$display_keys['stack run name']=$s['stackRunName'];

		foreach($display_keys as $k=>$v) {
			echo formatHtmlRow($k,$v);
		}
		$norefpath = $r[norefPath].$r[name]."/";

		$classIds = $particle->getNoRefClassRuns($norefid['DEF_id']);
		$classnum = count($classIds);
		foreach ($classIds as $classid) {
			$classfile = $norefpath.$classid[classFile].".img";
			$totimg = $classid[num_classes];
			$endimg = $classid[num_classes]-1;
			echo "
			<tr><td bgcolor='#ffcccc' colspan=2>
				Averaged into $totimg classes: &nbsp;&nbsp;&nbsp;
				<a href='viewstack.php?file=$classfile&endimg=$endimg'>View Class Averages</a>
			</td></tr>";
		
			//echo "<tr><td bgcolor='#ff4444'>"; print_r ($classid); echo "</td></tr>";
			//foreach($classid as $k=>$v) {
			//	echo formatHtmlRow($k,$v);
			//}
		}
		$norefnum = $norefid['DEF_id'];
		echo "
		<tr><td bgcolor='#ffcccc' colspan=2>
			Quickly re-average particles into
			<INPUT TYPE='text' NAME='numclass' VALUE='$numclass' SIZE='4'> classes: &nbsp;&nbsp;&nbsp;
			<INPUT TYPE='submit' NAME='process' VALUE='Re-average classes'>
			<INPUT TYPE='hidden' NAME='norefnum' VALUE=$norefnum>
		</td></tr>";	
		echo"</TABLE>\n";
		echo "</FORM>\n";
		echo"<P>\n";
	}
	writeBottom();
	exit;
};

function reRunClassifier() {
	$norefnum=$_POST['norefnum'];
	$numclass=$_POST['numclass'];

	$particle = new particledata();
	$r = $particle->getNoRefParams($norefnum);
	$runid = $r['name'];	
	$outdir = $r['norefPath'];
	$stackid = $r['REF|ApStackData|stack'];


	$command.="classifier.py ";
	$command.="runid=$runid ";
	$command.="stackid=$stackid ";
	$command.="outdir=$outdir ";
	$command.="numclass=$numclass ";
	$command.="classonly ";
	$command.="commit ";

	writeTop("Classifier Run","Classifier Params");

	echo"
	<P>
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>Classifier Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>runid</TD><TD>$runid</TD></TR>
	<TR><TD>stackid</TD><TD>$stackid</TD></TR>
	<TR><TD>outdir</TD><TD>$outdir</TD></TR>
	<TR><TD>numclass</TD><TD>$numclass</TD></TR>
	</TABLE>\n";
	writeBottom();
}

?>
