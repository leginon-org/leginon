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

$imageid = ($_GET['imgId']);
$movierunid = ($_GET['mId']);

$particle = new particledata();

$javascript = addFlashPlayerJS();

processing_header("Particle Movie Report","Particel Movie Page", $javascript);
if (!$imageid || !$movierunid) {
	processing_footer();
	exit;
}

$movierun = $particle->getParticleMovieRunFromId($movierunid);
$movie_basepath = $movierun['path'];

$imageinfo = $leginondata->getImageInfo($imageid);
$imagename = substr($imageinfo['filename'],0,-4);

$html = '<p>'.$imagename.'</p>'."\n";
$display_positions = array(
		array('5'=>2),
		array('4'=>1,'6'=>3),
		array('3'=>0,'7'=>4),
		array('2'=>1,'8'=>3),
		array('1'=>2),
);

$colwidth = 128;
$rowheight = $colwidth;
// --- Display Flash Movie from flv --- //
$html .= "<table>\n";
foreach ($display_positions as $p_array) {
	$html .= "<tr>";
	$i = 0;
	foreach ($p_array as $p_number=>$p) {
		# empty columns
		while ($i < $p) {
			$html .="<td>".$i."</td>";
			$i += 1;
		}

		# movie position
		$html .= "<td>";
		$p_number_str = sprintf('%03d', $p_number-1);
		$flvfile = $movie_basepath.'/'.$imagename.'_'.$p_number_str.'.flv';

		if (file_exists($flvfile)) {
			$html .= getMovieHTML($flvfile,$colwidth,$rowheight,$p_number_str);
		} else {
			$html .= $flvfile;
		}
		$html .= "</td>";
		$i += 1;

	}
	while ($i < 5) {
		$html .="<td>".$i."</td>";
		$i += 1;
	}
	if ($i > 5) break;
	$html .= "</tr>";
}
$html .= "</table>";
echo $html;

processing_footer();
?>
