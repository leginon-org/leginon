<?php
/**
 *	The Leginon software is Copyright 2007 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see http://ami.scripps.edu/software/leginon-license
 *
 *	compare particle alignment for 2 iterations
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";

$reconId = $_REQUEST['reconId'];
$iter1 = $_REQUEST['iter1'];
$iter2 = $_REQUEST['iter2'];
$comp_param = $_REQUEST['comp_param'];
$download= $_REQUEST['dwd'];

if (!$_REQUEST) {
	// --- testing values --- //
	$comp_param = "Eulers";
	$iter1 = 1;
	$iter2 = 2;
	$reconId = 1;
}

// --- Get Reconstruction Data
$particle = new particledata();
$ref = $particle->getRefinementData($reconId,$iter1);
$refine1=$ref[0];
$ref = $particle->getRefinementData($reconId,$iter2);
$refine2=$ref[0];
$commonprtls = $particle->getCommonParticles($refine1['DEF_id'], $refine2['DEF_id']);
$sep=" ";
$nl="\n";

foreach ($commonprtls as $prtl) {
	$data .= $prtl['particleNumber']." ";
	if ($comp_param=='Eulers') {
		$data .= $prtl['euler1_1'].$sep.$prtl['euler1_2'].$sep.$prtl['rot1'].$sep;
		$data .= $prtl['euler2_1'].$sep.$prtl['euler2_2'].$sep.$prtl['rot2'].$nl;
	}
	elseif ($comp_param=='Inplane Rotation') {
		$data .= $prtl['rot1'].$sep.$prtl['rot2'].$nl;
	}
	elseif ($comp_param=='Shifts') {
		$data .= "shiftx:".$sep.$prtl['shiftx1'].$sep.$prtl['shiftx2'].$sep;
		$data .= "shifty:".$sep.$prtl['shifty1'].$sep.$prtl['shifty2'].$nl;
	}
	elseif ($comp_param=='Quality Factor') {
		$data .= $prtl['qf1'].$sep.$prtl['qf2'].$nl;
	} 
}

header("Content-type: text/plain");
if ($download) {
	$filename="compare_".$comp_param."_iter".$iter1."_iter".$iter2.".txt";
	header("Content-Type: application/octet-stream");
	header("Content-Type: application/force-download");
	header("Content-Type: application/download");
	header("Content-Length: ".strlen($data));
	header("Content-Disposition: attachment; filename=".$filename);
}
echo $data;
?>
