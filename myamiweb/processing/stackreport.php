<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/summarytables.inc";

$expId = $_GET['expId'];
$sessionId= $_GET['Id'];
$stackId = $_GET['sId'];

processing_header('Particle Stack Report','Particle Stack Report');

$particle = new particledata();
	$s=$particle->getStackParams($stackId);
	# get list of stack parameters from database
	$nump=commafy($particle->getNumStackParticles($stackId));
	# get pixel size of stack
	$mpix=($particle->getStackPixelSizeFromStackId($stackId));
	$apix=format_angstrom_number($mpix)."/pixel";
	$s['pixelsize']=$apix;
	$boxsize= $s['boxsize'];
	$s['boxsize']=$boxsize;

	echo openRoundBorder();
	echo "<table border='0' cellspacing='8' cellpading='8'><tr><td>\n";
	echo stacksummarytable($stackId);
	echo "</td></tr></table>\n";
	echo closeRoundBorder();

	echo "<table cellspacing='1' cellpadding='2'><tr><td>";
	echo "<span class='datafield0'>Total particles for $runparams[stackRunName]: </span></td><td>$nump</td></tr></table>\n";

	$stackfile=$s['path']."/".$s['name'];
	echo '<span style="font-size:18px">View Stack: <a target="stackview" href="viewstack.php?stackId='.$stackId.'&file='.$stackfile.'">'.$s['name'].'</a></span><br>'."\n";	

//Report stack parameters
	$exclude_fields = array('DEF_id','DEF_timestamp','count','REF|ApPathData|path','boxSize','selectionstacks');
	for ($i=1;$i < $s[count]; $i++) $exclude_fields[]=$i;
	$title = "stack parameters";
	$particle->displayParameters($title,$s,$exclude_fields,$expId);

//Report parent (old) stack run parameters if a substack
	while ($s['REF|ApStackData|oldstack']) {
		$s0 = $s;
		$stackId = $s['REF|ApStackData|oldstack'];
		$s=$particle->getStackParams($stackId);
		#for ($i=1;$i < $s[count]; $i++) $exclude_fields[]=$i;
		$title = "parent stack parameters";
		$particle->displayParameters($title,$s,$exclude_fields,$expId);
	}
//Report individual stack run parameters if combined
//This need rework along with getStackParams to handle multiple layers----AC
	if ($s['count'] > 1) {
		for ($i=0; $i < $s[count]; $i++) {
			$selectionstackId = $s['selectionstacks'][$i];
			$sr=$particle->getStackParams($selectionstackId);
			#for ($i=1;$i < $sr[count]; $i++) $exclude_fields[]=$i;
			$title = "combining stack run parameters";
			$particle->displayParameters($title,$sr,$exclude_fields,$expId);
		}
	}
//Report stack run particle picking parameters
	echo "<table><tr><td>";
	for ($i=0; $i < $s[count]; $i++) {
		$selectionstackId = $s['selectionstacks'][$i];
		$selectionruninfo=$particle->getStackSelectionRun($selectionstackId);
		$a = array('stackId'=>$selectionstackId);
		$a = array_merge($a,$selectionruninfo[0]);
		$a['particleSelection']=array('display'=>$a['name'], 'link'=>$a['selectionid']);
		$exclude_fields = array('DEF_id','DEF_timestamp','REF|ApPathData|path','name');
		$title = "particle selection";
		$particle->displayParameters($title,$a,$exclude_fields,$a['sessionId']);
		echo "</td><td>";
	}
	echo "</td><tr></table>";




processing_footer();






