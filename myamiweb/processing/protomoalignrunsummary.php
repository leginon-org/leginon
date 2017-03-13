<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

$page = $_SERVER['REQUEST_URI'];
header("Refresh: 300; URL=$page");

//print "_POST:" . "<br>";
//var_dump($_POST);
//print "_GET:" . "<br>";
//var_dump($_GET);
//print "_SESSION:" . "<br>";
//var_dump($_SESSION);

$expId = $_GET['expId'];
$outdir = $_GET['outdir'];

processing_header("Protomo Alignment and Reconstruction Summary","Protomo Alignment Summary", $javascript);

$html = "<h4>Protomo Tilt-Series Alignment Runs</h4>";
$html .= "rundir: $outdir";
$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>";
$html .= "<TR>";
$display_keys = array ( '<center>runname</center>','<center>tilt-series #</center>','<center>last alignment<br>type</center>','<center># of refinement<br>iterations</center>','<center>best iteration<br>(all, bin 1 or 2)</center>','<center>alignment quality<br>(all, bin 1 or 2)</center>','<center>tilt azimuth<br>(all, bin 1 or 2)</center>','<center>tilt angle<br>range</center>','<center>recorded<br>defocus</center>','<center>dose<br>compensated</center>','<center># of reconstructions<br>available</center>','<center>suggested<br>next steps</center>','<center>summary<br>webpage</center>');
foreach($display_keys as $key) {
	$html .= "<td><span class='datafield0'>".$key."</span></TD> ";
}
$html .= "</TR>";
$tiltseries_runs = glob("$outdir/*/series[0-9][0-9][0-9][0-9].tlt");

$counter = 0;
foreach($tiltseries_runs as $tiltseries_run) {
	//Counter for repeating header
	$counter++;
	if ($counter % 15 == 0) {
		foreach($display_keys as $key) {
			$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
		}
		$html .= "</TR>";
	}
	$path_chunks = array_reverse(explode('/', $tiltseries_run));
	$tiltseriesnumber = explode('.',$path_chunks[0]);
	$tiltseriesnumber = (int)substr($tiltseriesnumber[0], 6, 10);
	$refine_iterations = glob("$outdir/$path_chunks[1]/series*.tlt");
	$coarse_iterations = glob("$outdir/$path_chunks[1]/coarse_series*.tlt");
	$html .= "<td>$path_chunks[1]</TD>";
	$html .= "<td>$tiltseriesnumber</TD>";
	
	//Quality lookup and tilt azimuth lookup
	if (count($refine_iterations) > 1){
		$iterations = count($refine_iterations)-1;
		$quality_assessment_file = glob("$outdir/$path_chunks[1]/media/quality_assessment/*.txt");
		$quality_assessment = file($quality_assessment_file[0]);
		$quality_assessment_best = $quality_assessment[0];
		$quality_assessment_best = array_reverse(explode(' ',$quality_assessment_best));
		$html .= "<td>Refinement</TD>";
		$html .= "<td>$iterations</TD>";
		$best_iteration = glob("$outdir/$path_chunks[1]/best.*");
		$best_bin1or2_iteration = glob("$outdir/$path_chunks[1]/best_bin1or2.*");
		if (count($best_iteration) > 0) {
			$best_iteration = array_reverse(explode('/',$best_iteration[0]));
			$best_iteration = explode('.',$best_iteration[0]);
			//$html .= '<td><a href="protomo2RefineIterationSummary.php?iter='.$best_iteration[1].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank">'.$best_iteration[1].'</a></TD>';
		}
		if (count($best_bin1or2_iteration) > 0) {
			$best_bin1or2_iteration = array_reverse(explode('/',$best_bin1or2_iteration[0]));
			$best_bin1or2_iteration = explode('.',$best_bin1or2_iteration[0]);
			//$html .= '<td><a href="protomo2RefineIterationSummary.php?iter='.$best_bin1or2_iteration[1].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank">'.$best_bin1or2_iteration[1].'</a></TD>';
		}
		if ((count($best_iteration) > 0) and (count($best_bin1or2_iteration) > 0)) {
			$html .= '<td><a href="protomo2RefineIterationSummary.php?iter='.$best_iteration[1].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank">'.$best_iteration[1].'</a>, ';
			$html .= '<a href="protomo2RefineIterationSummary.php?iter='.$best_bin1or2_iteration[1].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank">'.$best_bin1or2_iteration[1].'</a></TD>';
		} elseif (count($best_iteration) > 0) {
			$html .= '<td><a href="protomo2RefineIterationSummary.php?iter='.$best_iteration[1].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank">'.$best_iteration[1].'</a></TD>';
		} else {
			$html .= "<td>--</TD>";
		}
		if ((float)($quality_assessment_best[0]) > 0){
			if ($quality_assessment_best[0] < 0.005){
				$html .= "<td><font color='green'><b><i>Perfection!</i></b></font></TD>";
			} elseif ($quality_assessment_best[0] < 0.0075){
				$html .= "<td><font color='green'><b>Excellent</b></font></TD>";
			} elseif ($quality_assessment_best[0] < 0.0125){
				$html .= "<td><font color='green'>Very Good</font></TD>";
			} elseif ($quality_assessment_best[0] < 0.02){
				$html .= "<td><font color='green'>Good</font></TD>";
			} elseif ($quality_assessment_best[0] < 0.03){
				$html .= "<td>Okay</TD>";
			} else {
				$html .= "<td><font color='red'>Bad</font></TD>";
			}
		} else {
			$html .= "<td>--</TD>";
		}
		$best_tlt_file = "$outdir/$path_chunks[1]/series".sprintf('%04d',$tiltseriesnumber).sprintf('%03d',$best_iteration[1]-1).".tlt";
		$tlt_file = "$outdir/$path_chunks[1]/series".sprintf('%04d',$tiltseriesnumber).".tlt";
		if (file_exists($best_tlt_file)) {
			$best_tlt_file = file($best_tlt_file);
			foreach($best_tlt_file as $key) {
				if (strpos($key, 'AZIMUTH') !== false) {
					$tilt_azimuth = array_reverse(explode(' ',trim($key)));
				}
			}
			$html .= "<td>$tilt_azimuth[0]</TD>";
			$i=1;
			foreach($best_tlt_file as $key) {
				if (strpos($key, 'TILT ANGLE') !== false) {
					if ($i == 1) {
						$tilt_min = explode(' ',$key);
						$tilt_min = round($tilt_min[12]);
					}
					$i++;
				}
			}
			$j=1;
			foreach($best_tlt_file as $key) {
				if (strpos($key, 'TILT ANGLE') !== false) {
					if ($i-1 == $j) {
						$tilt_max = explode(' ',$key);
						$tilt_max = round($tilt_max[12]);
					}
					$j++;
				}
			}
		} elseif (file_exists($tlt_file)) {
			$tlt_file = file($tlt_file);
			foreach($tlt_file as $key) {
				if (strpos($key, 'AZIMUTH') !== false) {
					$tilt_azimuth = array_reverse(explode(' ',trim($key)));
				}
			}
			$html .= "<td>$tilt_azimuth[0]</TD>";
		} else {
			$html .= "<td>--</TD>";
		}
		$html .= "<td><center>[$tilt_min:$tilt_max]</center></TD>";
	} elseif (count($coarse_iterations) > 0){
		$html .= "<td>Coarse</TD>";
		$html .= "<td>--</TD>";
		$html .= "<td>--</TD>";
		$html .= "<td>--</TD>";
		$tlt_file = "$outdir/$path_chunks[1]/series".sprintf('%04d',$tiltseriesnumber).".tlt";
		if (file_exists($tlt_file)) {
			$tlt_file = file($tlt_file);
			foreach($tlt_file as $key) {
				if (strpos($key, 'AZIMUTH') !== false) {
					$tilt_azimuth = array_reverse(explode(' ',trim($key)));
				}
			}
			$html .= "<td>$tilt_azimuth[0]</TD>";
		} else {
			$html .= "<td>--</TD>";
		}
		$i=1;
		foreach($tlt_file as $key) {
			if (strpos($key, 'TILT ANGLE') !== false) {
				if ($i == 1) {
					$tilt_min = explode(' ',$key);
					$tilt_min = round($tilt_min[12]);
				}
				$i++;
			}
		}
		$j=1;
		foreach($tlt_file as $key) {
			if (strpos($key, 'TILT ANGLE') !== false) {
				if ($i-1 == $j) {
					$tilt_max = explode(' ',$key);
					$tilt_max = round($tilt_max[12]);
				}
				$j++;
			}
		}
	} else {
		$html .= "<td>None</TD>";
		$html .= "<td>--</TD>";
		$html .= "<td>--</TD>";
		$html .= "<td>--</TD>";
		$tlt_file = "$outdir/$path_chunks[1]/series".sprintf('%04d',$tiltseriesnumber).".tlt";
		if (file_exists($tlt_file)) {
			$tlt_file = file($tlt_file);
			foreach($tlt_file as $key) {
				if (strpos($key, 'AZIMUTH') !== false) {
					$tilt_azimuth = array_reverse(explode(' ',trim($key)));
				}
			}
			$html .= "<td>$tilt_azimuth[0]</TD>";
		} else {
			$html .= "<td>--</TD>";
		}
	}
	
	//Tilt angle range
	
	
	//Defocus record check
	$defocus_file = glob("$outdir/$path_chunks[1]/defocus_estimation/defocus_[0-9]*");
	if (count($defocus_file) > 0){
		$defocus_file = array_reverse(explode('/',$defocus_file[0]));
		$defocus = explode('_',$defocus_file[0]);
		$defocus = (float)$defocus[1];
		$html .= "<td>$defocus</TD>";
		$defocus_suggestion = '';
	} else {
		$html .= "<td>--</TD>";
		$defocus_suggestion = 'Estimate defocus,<br>';
	}
	
	//Dose compensation check
	$dose_comp_file = glob("$outdir/$path_chunks[1]/raw/dose_comp_*");
	if (count($dose_comp_file) > 0){
		$html .= "<td>Yes</TD>";
		$dose_suggestion = '';
	} else {
		$html .= "<td>No</TD>";
		$dose_suggestion = ',<br>Dose compensate';
	}
	
	//Number of reconstructions available
	$recon_files = glob("$outdir/$path_chunks[1]/recons_*/*.mrc",GLOB_BRACE);
	$recon_number = count($recon_files);
	$html .= "<td>$recon_number</TD>";
	
	//Suggested next steps
	$suggestion = '';
	if (count($refine_iterations) > 1){
		if ((float)($quality_assessment_best[0]) > 0){
			if ($quality_assessment_best[0] < 0.0125){
				$suggestion .= '<center>'.$defocus_suggestion.'CTF correct'.$dose_suggestion.',<br>Reconstruct,<br>SPT/Segment,<br>Publish! (and cite)</center>';
			} elseif ($quality_assessment_best[0] < 0.02){
				$suggestion .= '<center>Optimize alignment'.$dose_suggestion.'</center>';
			} else {
				$suggestion .= '<center>Check/Fix tilt-series,<br>Optimize alignment'.$dose_suggestion.'</center>';
			}
		} else {
			$suggestion .= '<center>Check/Fix tilt-series,<br>Optimize alignment'.$dose_suggestion.'</center>';
		}
	} elseif (count($coarse_iterations) > 0){
		$suggestion .= '<center>Full refinement'.$dose_suggestion.'</center>';
	} else {
		$suggestion .= '<center>Coarse/Manual<br>alignment,<br>Full refinement'.$dose_suggestion.'</center>';
	}
	$html .= "<td>$suggestion</TD>";
	
	//Summary webpages
	if (count($refine_iterations) > 1){
		$html .= '<td><a href="protomo2TiltSummary.php?outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank"><center>Refinement<br>Summary</center></a></TD>';
	} elseif (count($coarse_iterations) > 0){
		$html .= '<td><a href="protomo2CoarseTiltSummary.php?outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank"><center>Coarse Alignment<br>Summary</center></a></TD>';
	} else {
		$html .= "<td><center>--</center></TD>";
	}
	$html .= "</TR>";
}

$html .= "</table>";
$html .= "<br>";
$html .= "<b>To continue processing a tilt-series, <a href='runAppionLoop.php?expId=$expId&form=Protomo2CoarseAlignForm' target='_blank'>click here</a>, change the runname & output directory, and select the appropriate tilt-series, then continue on to the desired processing step.</b>";
echo $html;

?>
