<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Display results for each iteration of a refinement
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";
require_once "inc/movie.inc";

define (PARTICLE_DB, $_SESSION['processingdb']);

$alignerid = ($_GET['aId']);

$particle = new particledata();
$refinedata = $particle->getProtomoAlignmentInfo($alignerid);
$cycle = $refinedata[0]['cycle'];
if (!$refinedata) {
	$refinedata = $particle->getAlignerInfo($alignerid);
	$alignment = $particle->getTomoAlignmentInfo($refinedata[0]['alignrunid']);
}
$javascript = addFlashPlayerJS();

processing_header("Tomogram Report","Tomogram Report Page", $javascript);
if (!$alignerid) {
	processing_footer();
	exit;
}

// --- Display Flash Movie from flv --- //
@require_once('getid3/getid3.php');
function getflvsize($filename) {
	if (!class_exists('getID3')) {
		return false;
	}
	$getID3 = new getID3;
	$i = $getID3->analyze($filename);
	$w = $i['meta']['onMetaData']['width'];
	$h = $i['meta']['onMetaData']['height'];
	return array($w, $h);
}

if (!defined('FLASHPLAYER_URL')) {
	echo "<p style='color: #FF0000'>FLASHPLAYER_URL is not defined in config.php</p>";
}
if (!is_null($cycle)) {
	$flvfile = $refinedata[0]['path']."/align/minialign".sprintf('%02d',$cycle).".flv";
} else {
	if ($alignment['method'] == 'raptor'){
		$flvfile = $refinedata[0]['path']."/align/minialign.flv";
	} else {
		$flvfile = $refinedata[0]['path']."/minialign.flv";
	}
}	
if (file_exists($flvfile)) {
	echo "<table><tr><td>Alignment Stack:</td></tr>\n";
	echo "<tr><td>".$flvfile."</td></tr>\n";
	echo "<tr><td>";
	list($colwidth,$rowheight) =  getMovieSize($flvfile);
	echo getMovieHTML($flvfile,$colwidth,$rowheight,$subid=$axis);
	echo "</td></tr>";	
	echo "</table>";
}

echo $html;

processing_footer();
?>
