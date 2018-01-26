<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
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
$videos = $_GET['videos'];

processing_header("Protomo Alignment and Reconstruction Summary","Protomo Alignment Summary", $javascript);

$html = "<h4>Protomo Tilt-Series Alignment Runs</h4>";

$tiltseries_runs = glob("$outdir/*/series[0-9][0-9][0-9][0-9].tlt");
$all_recon_files = array();   // initialization

$html .= "rundir: $outdir";
if ($videos == 'off'){
$html .= "<br><a href='protomoalignrunsummary.php?expId=$expId&outdir=$outdir&videos=on'>Turn videos on</a>";
}else{
$html .= "<br><a href='protomoalignrunsummary.php?expId=$expId&outdir=$outdir&videos=off'>Turn videos off</a>";
}
if (count($tiltseries_runs) > 12) {
$html .= "<br><br><b>To continue processing a tilt-series, <a href='runAppionLoop.php?expId=$expId&form=Protomo2CoarseAlignForm' target='_blank'>Click Here</a>, change the runname & output directory, and select the appropriate tilt-series, then continue on to the desired processing step.</b><br>";
//$html .= "<b>Estimate defocus or dose compensate existing tilt-series by continuing to Batch or to More Tilt-Series Processing.</b>";
}
$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>";
$html .= "<TR>";
$display_keys = array ( 'runname,<br>run date','tilt-series<br>#','last alignment<br>type','# of<br>iterations','best iteration<br>(all, bin 1 or 2)','alignment quality<br>(all, bin 1 or 2)','tilt azimuth<br>(all, bin 1 or 2)','tilt angle<br>range','recorded<br>defocus (Å)','dose<br>compensated','# of recons<br>available','suggested<br>next steps','preview of best/<br>coarse iteration','additional<br>information','summary<br>webpage');
foreach($display_keys as $key) {
	$html .= "<td><span class='datafield0'><center>".$key."</center></span></TD> ";
}
$html .= "</TR>";
$counter = 0;
foreach($tiltseries_runs as $tiltseries_run) {
	//Counter for repeating header
	$counter++;
	if ($counter % 12 == 0) {
		foreach($display_keys as $key) {
			$html .= "<td><span class='datafield0'><center>".$key."</center></span></TD>";
		}
		$html .= "</TR>";
	}
	$path_chunks = array_reverse(explode('/', $tiltseries_run));
	$tiltseriesnumber = explode('.',$path_chunks[0]);
	$tiltseriesnumber = (int)substr($tiltseriesnumber[0], 6, 10);
	$refine_iterations = glob("$outdir/$path_chunks[1]/series*.tlt");
	$coarse_iterations = glob("$outdir/$path_chunks[1]/coarse_series*.tlt");
	$protomo2aligner_logs = glob("$outdir/$path_chunks[1]/protomo2aligner_*.log");
	$protomo2aligner_logs = array_reverse($protomo2aligner_logs);
	$protomo2aligner_logs = array_reverse(explode('/',$protomo2aligner_logs[0]));
	$protomo2aligner_logs = explode('_',$protomo2aligner_logs[0]);
	$protomo2aligner_logs = explode('.',$protomo2aligner_logs[1]);
	$protomo2aligner_logs = explode('-',$protomo2aligner_logs[0]);
	$date_yr = explode('yr',$protomo2aligner_logs[0]);
	$date_m = explode('m',$date_yr[1]);
	$date_d = explode('d',$date_m[1]);
	$time_hr = explode('hr',$protomo2aligner_logs[1]);
	$time_m = explode('m',$time_hr[1]);
	if ($protomo2aligner_logs[0] != '') {
		$html .= "<td><center><b>$path_chunks[1]</b><br>$date_m[0]-$date_d[0]-$date_yr[0]<br>@ $time_hr[0]:$time_m[0]<br><input type='checkbox' onclick='return writeTo(this)' name='check_list' value='$outdir/$path_chunks[1]/'><sup>remove?</sup></center></TD>";
	}else{
		$html .= "<td><center><b>$path_chunks[1]</b><br><input type='checkbox' onclick='return writeTo(this)' name='check_list' value='$outdir/$path_chunks[1]/'><sup>remove?</sup></center></TD>";
	}
	$html .= '<script>
				function writeTo(object) {
					  var container = document.getElementById("container");
					  if (object.checked) {
						 container.innerHTML = container.innerHTML + "rm -rf " + object.value + " <br />";   
					  }
					}
				</script>';
						// else {
						// container.innerHTML = container.innerHTML - "rm -rf " - object.value + " <br />";   
					 // }
	$html .= "<td><center>$tiltseriesnumber</center></TD>";

	
	//Quality lookup and tilt azimuth lookup
	if (count($refine_iterations) > 1){
		$iterations = count($refine_iterations)-1;
		$quality_assessment_file = glob("$outdir/$path_chunks[1]/media/quality_assessment/*.txt");
		$quality_assessment = file($quality_assessment_file[0]);
		$quality_assessment_best = $quality_assessment[0];
		$quality_assessment_best = array_reverse(explode(' ',$quality_assessment_best));
		$html .= "<td><center>Refinement</center></TD>";
		$html .= "<td><center>$iterations</center></TD>";
		$best_iteration = glob("$outdir/$path_chunks[1]/best.*");
		$best_bin1or2_iteration = glob("$outdir/$path_chunks[1]/best_bin1or2.*");
		if (count($best_iteration) > 0) {
			$best_iteration = array_reverse(explode('/',$best_iteration[0]));
			$best_iteration = explode('.',$best_iteration[0]);
		}
		if (count($best_bin1or2_iteration) > 0) {
			$best_bin1or2_iteration = array_reverse(explode('/',$best_bin1or2_iteration[0]));
			$best_bin1or2_iteration = explode('.',$best_bin1or2_iteration[0]);
		}
		if ((count($best_iteration) > 0) and (count($best_bin1or2_iteration) > 0)) {
			$html .= '<td><a href="protomo2RefineIterationSummary.php?iter='.$best_iteration[1].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank"><center>'.$best_iteration[1].'</a>, ';
			$html .= '<a href="protomo2RefineIterationSummary.php?iter='.$best_bin1or2_iteration[1].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank">'.$best_bin1or2_iteration[1].'</center></a></TD>';
		} elseif (count($best_iteration) > 0) {
			$html .= '<td><a href="protomo2RefineIterationSummary.php?iter='.$best_iteration[1].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank"><center>'.$best_iteration[1].'</center></a></TD>';
		} else {
			$html .= "<td><center>--</center></TD>";
		}
		
		if (count($best_iteration) > 0) {
			foreach($quality_assessment as $key) {
				$iteration = explode(' ',$key);
				$iteration = $iteration[0];
				if ((int)$iteration == (int)$best_iteration[1]) {
					$CCMS = array_reverse(explode(' ',$key));
					$CCMS = (float)$CCMS[0];
					if ($CCMS < 0.0025){
						$best_quality = "<font color='green'><b><i>Suspiciously<br>Perfect...</i></b><br></font>";
					}elseif ($CCMS < 0.005){
						$best_quality = "<font color='green'><b><i>Perfection!</i></b><br></font>";
					} elseif ($CCMS < 0.0075){
						$best_quality = "<font color='green'><b>Excellent</b><br></font>";
					} elseif ($CCMS < 0.0125){
						$best_quality = "<font color='green'>Very Good<br></font>";
					} elseif ($CCMS < 0.02){
						$best_quality = "<font color='green'>Good<br></font>";
					} elseif ($CCMS < 0.03){
						$best_quality = "Okay<br>";
					} else {
						if (count($refine_iterations) == 2) {
							$best_quality = "<font color='red'>Bad</font><br>(1st iteration is<br>always bad)<br>";
						}else{
							$best_quality = "<font color='red'>Bad<br></font>";
						}
					}
				}
			}
		} else {
			$best_quality = '';
		}
		if (count($best_bin1or2_iteration) > 0) {
			foreach($quality_assessment as $key) {
				$iteration = explode(' ',$key);
				$iteration = $iteration[0];
				if ((int)$iteration == (int)$best_bin1or2_iteration[1]) {
					$CCMS = array_reverse(explode(' ',$key));
					$CCMS = (float)$CCMS[0];
					if ($CCMS < 0.0025){
						$best_bin1or2_quality = "<font color='green'><b><i>Suspiciously<br>Perfect...</i></b></font>";
					}elseif ($CCMS < 0.005){
						$best_bin1or2_quality = "<font color='green'><b><i>Perfection!</i></b></font>";
					} elseif ($CCMS < 0.0075){
						$best_bin1or2_quality = "<font color='green'><b>Excellent</b></font>";
					} elseif ($CCMS < 0.0125){
						$best_bin1or2_quality = "<font color='green'>Very Good</font>";
					} elseif ($CCMS < 0.02){
						$best_bin1or2_quality = "<font color='green'>Good</font>";
					} elseif ($CCMS < 0.03){
						$best_bin1or2_quality = "Okay";
					} else {
						if (count($refine_iterations) == 2) {
							$best_bin1or2_quality = "<font color='red'>Bad</font><br>(1st iteration is<br>always bad)";
						}else{
							$best_bin1or2_quality = "<font color='red'>Bad</font>";
						}
					}
				}
			}
		} else {
			$best_bin1or2_quality = '';
		}
		if (($best_quality == '') and ($best_bin1or2_quality == '')) {
			$html .= "<td><center>--</center></TD>";
		}elseif (($best_quality == '') and ($best_bin1or2_quality !== '')) {
			$html .= "<td><center>--<br>$best_bin1or2_quality</center></TD>";
		}elseif (($best_quality !== '') and ($best_bin1or2_quality == '')) {
			$html .= "<td><center>$best_quality</center></TD>";
		}elseif (($best_quality !== '') and ($best_bin1or2_quality !== '')) {
			if ($best_bin1or2_iteration[1] == $best_iteration[1]) {
				$html .= "<td><center>$best_bin1or2_quality</center></TD>";
			}else{
				$html .= "<td><center>$best_quality$best_bin1or2_quality</center></TD>";
			}
		}
		
		//Tilt angle range too
		$best_tlt_file = "$outdir/$path_chunks[1]/series".sprintf('%04d',$tiltseriesnumber).sprintf('%03d',$best_iteration[1]-1).".tlt";
		$best_bin1or2_tlt_file = "$outdir/$path_chunks[1]/series".sprintf('%04d',$tiltseriesnumber).sprintf('%03d',$best_bin1or2_iteration[1]-1).".tlt";
		$tlt_file = "$outdir/$path_chunks[1]/series".sprintf('%04d',$tiltseriesnumber).".tlt";
		if (file_exists($best_tlt_file)) {
			$best_tlt_file = file($best_tlt_file);
			foreach($best_tlt_file as $key) {
				if (strpos($key, 'AZIMUTH') !== false) {
					$tilt_azimuth = array_reverse(explode(' ',trim($key)));
				}
			}
			if (file_exists($best_bin1or2_tlt_file) and ($best_iteration[1] !== $best_bin1or2_iteration[1])) {
				$best_bin1or2_tlt_file = file($best_bin1or2_tlt_file);
				foreach($best_bin1or2_tlt_file as $key) {
					if (strpos($key, 'AZIMUTH') !== false) {
						$tilt_azimuth2 = array_reverse(explode(' ',trim($key)));
					}
				}
				$html .= "<td><center>$tilt_azimuth[0],<br>$tilt_azimuth2[0]</center></TD>";
			}else{
				$html .= "<td><center>$tilt_azimuth[0]</center></TD>";
			}
			$i=1;
			foreach($best_tlt_file as $key) {
				if (strpos($key, 'TILT ANGLE') !== false) {
					if ($i == 1) {   //First image in the .tlt file
						$tilt_min = explode(' ',$key);
						$z=0;
						foreach($tilt_min as $key2) {
							if ($tilt_min[$z] == 'ANGLE') {
								$tilt_min_location = $z+2;
								if (is_float(floatval($tilt_min[$tilt_min_location]))) {}
								else{$tilt_min_location = $z+3;}
								$tilt_min = round($tilt_min[$tilt_min_location]);
							}
							$z++;
						}
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
			$html .= "<td><center>$tilt_azimuth[0]</center></TD>";
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
			$html .= "<td><center>--</center></TD>";
			$tilt_min = 0;
			$tilt_max = 0;
		}
		if (($tilt_min == 0) and ($tilt_max == 0)) {
			$html .= "<td><center>--</center></TD>";
		}else {
			$html .= "<td><center>[$tilt_min:$tilt_max]</center></TD>";
		}
	} elseif (count($coarse_iterations) > 0){
		$html .= "<td><center>Coarse</center></TD>";
		$html .= "<td><center>--</center></TD>";
		$html .= "<td><center>--</center></TD>";
		$html .= "<td><center>--</center></TD>";
		$tlt_file = "$outdir/$path_chunks[1]/series".sprintf('%04d',$tiltseriesnumber).".tlt";
		if (file_exists($tlt_file)) {
			$tlt_file = file($tlt_file);
			foreach($tlt_file as $key) {
				if (strpos($key, 'AZIMUTH') !== false) {
					$tilt_azimuth = array_reverse(explode(' ',trim($key)));
				}
			}
			$html .= "<td><center>$tilt_azimuth[0]</center></TD>";
		} else {
			$html .= "<td><center>--</center></TD>";
		}
		$tlt_file = "$outdir/$path_chunks[1]/series".sprintf('%04d',$tiltseriesnumber).".tlt";
		if (file_exists($tlt_file)) {
			$tlt_file = file($tlt_file);
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
			$tilt_min = 0;
			$tilt_max = 0;
		}
		if (($tilt_min == 0) and ($tilt_max == 0)) {
			$html .= "<td><center>--</center></TD>";
		}else {
			$html .= "<td><center>[$tilt_min:$tilt_max]</center></TD>";
		}
	} else {
		$html .= "<td><center>None</center></TD>";
		$html .= "<td><center>--</center></TD>";
		$html .= "<td><center>--</center></TD>";
		$html .= "<td><center>--</center></TD>";
		$tlt_file = "$outdir/$path_chunks[1]/series".sprintf('%04d',$tiltseriesnumber).".tlt";
		if (file_exists($tlt_file)) {
			$tlt_file = file($tlt_file);
			foreach($tlt_file as $key) {
				if (strpos($key, 'AZIMUTH') !== false) {
					$tilt_azimuth = array_reverse(explode(' ',trim($key)));
				}
			}
			$html .= "<td><center>$tilt_azimuth[0]</center></TD>";
			$html .= "<td><center>--</center></TD>";
		} else {
			$html .= "<td><center>--</center></TD>";
			$html .= "<td><center>--</center></TD>";
		}
	}
	
	//Defocus record check
	$defocus_file = glob("$outdir/$path_chunks[1]/defocus_estimation/defocus_[0-9]*");
	if (count($defocus_file) > 0){
		$defocus_file = array_reverse(explode('/',$defocus_file[0]));
		$defocus = explode('_',$defocus_file[0]);
		$defocus = (float)$defocus[1];
		$html .= "<td><center>$defocus</center></TD>";
		$defocus_suggestion = "<a href='runAppionLoop.php?expId=$expId&form=Protomo2TomoCTFEstimate&outdir=$outdir&runname=$path_chunks[1]' target='_blank'>Refine defocus</a>,<br>";
	} else {
		$html .= "<td><center>--</center></TD>";
		$defocus_suggestion = "<a href='runAppionLoop.php?expId=$expId&form=Protomo2TomoCTFEstimate&outdir=$outdir&runname=$path_chunks[1]' target='_blank'>Estimate defocus</a>,<br>";
	}
	
	//Dose compensation check
	$dose_comp_file = glob("$outdir/$path_chunks[1]/raw/dose_comp_*");
	if (count($dose_comp_file) > 0){
		$dose_comp_file = $dose_comp_file[0];
		$dose_comp_file = array_reverse(explode('/',$dose_comp_file));
		$dose_comp_file = $dose_comp_file[0];
		$dose_comp_file = explode('_',$dose_comp_file);
		$dose_a = explode('a',$dose_comp_file[2]);
		$dose_b = explode('b',$dose_comp_file[3]);
		$dose_c = explode('c',$dose_comp_file[4]);
		if (((float)$dose_a[1] == 0.245) and ((float)$dose_b[1] == -1.8) and ((float)$dose_c[1] == 12.)) {
			$dose_comp_type = "(Light)";
		} elseif (((float)$dose_a[1] == 0.245) and ((float)$dose_b[1] == -1.665) and ((float)$dose_c[1] == 2.81)) {
			$dose_comp_type = "(Moderate)";
		} elseif (((float)$dose_a[1] == 0.245) and ((float)$dose_b[1] == -1.4) and ((float)$dose_c[1] == 2.0)) {
			$dose_comp_type = "(Heavy)";
		} else {
			$dose_comp_type = "(Custom)";
		}
		$html .= "<td><center>Yes<br>$dose_comp_type</center></TD>";
		$dose_suggestion = '';
	} else {
		$html .= "<td><center>No</center></TD>";
		$dose_suggestion = ',<br>Dose compensate';
	}
	
	//Number of reconstructions available
	$recon_files = glob("$outdir/$path_chunks[1]/recons_*/*.mrc",GLOB_BRACE);
	$all_recon_files = array_merge($all_recon_files,$recon_files);
	$recon_number = count($recon_files);
	$html .= "<td><center>$recon_number</center></TD>";
	
	//Suggested next steps
	$suggestion = '';
	if (count($refine_iterations) > 1){
		if ((float)($quality_assessment_best[0]) > 0){
			if ($quality_assessment_best[0] < 0.0125){
				#$suggestion .= '<center>'.$defocus_suggestion.'CTF correct'.$dose_suggestion.',<br><a href="runAppionLoop.php?expId='.$expId.'&form=Protomo2ReconstructionForm&rundir='.$outdir.'&runname='.$path_chunks[1].'&iter='.$best_bin1or2_iteration[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank"><b>Reconstruct</b></a>,<br>SPT/Segment,<br>Publish! (and <a href="protomo2Citations.php" target="_blank">cite</a>)';
				$suggestion .= '<center>'.$defocus_suggestion.'CTF correct'.$dose_suggestion.',<br>Reconstruct,<br>SPT/Segment,<br>Publish! (and <a href="protomo2Citations.php" target="_blank">cite</a>)';
			} elseif ($quality_assessment_best[0] < 0.02){
				$suggestion .= '<center>'.$defocus_suggestion.'Optimize alignment'.$dose_suggestion.'</center>';
			} else {
				$suggestion .= '<center>'.$defocus_suggestion.'Check/Fix tilt-series,<br>Optimize alignment'.$dose_suggestion.'</center>';
			}
		} else {
			$suggestion .= '<center>'.$defocus_suggestion.'Check/Fix tilt-series,<br>Optimize alignment'.$dose_suggestion.'</center>';
		}
	} elseif (count($coarse_iterations) > 0){
		$suggestion .= '<center>'.$defocus_suggestion.'Check/Fix tilt-series,<br>Full refinement'.$dose_suggestion.'</center>';
	} else {
		$suggestion .= '<center>'.$defocus_suggestion.'Coarse/Manual<br>alignment,<br>Full refinement'.$dose_suggestion.'</center>';
	}
	$html .= "<td>$suggestion</TD>";
	
	//Tilt-series preview
	if ($videos == 'off'){
		$html .= "<td><center>--</center></TD>";
	}else{
		if (count($refine_iterations) > 1){
			$tilt_gif_files = glob("$outdir/$path_chunks[1]/media/tiltseries/s*.gif");
			$tilt_vid_files = glob("$outdir/$path_chunks[1]/media/tiltseries/series".sprintf('%04d',$tiltseriesnumber).sprintf('%03d',$best_iteration[1]-1).".{mp4,ogv,webm}",GLOB_BRACE);
			$tilt_gif = "loadimg.php?rawgif=1&filename=".$tilt_gif_files[$best_iteration[1]-1];
			$tilt_mp4 = "loadvid.php?filename=".$tilt_vid_files[0];
			$tilt_ogv = "loadvid.php?filename=".$tilt_vid_files[1];
			$tilt_webm = "loadvid.php?filename=".$tilt_vid_files[2];
			$html .= '<td><center><video id="tiltVideos" width="85" controls autoplay loop>
						  <source src="'.$tilt_mp4.'" type="video/mp4" loop>'.'<br />
						  <source src="'.$tilt_webm.'" type="video/webm" loop>'.'<br />
						  <source src="'.$tilt_ogv.'" type="video/ogg" loop>'.'<br />
						  HTML5 video is not supported by your browser.
						  </video></center></TD>';
		} elseif (count($coarse_iterations) > 0){
			$tilt_gif_files = glob("$outdir/$path_chunks[1]/media/tiltseries/c*.gif");
			$tilt_vid_files = glob("$outdir/$path_chunks[1]/media/tiltseries/c*.{mp4,ogv,webm}",GLOB_BRACE);
			$tilt_gif = "loadimg.php?rawgif=1&filename=".$tilt_gif_files[$best_iteration[1]-1];
			$tilt_mp4 = "loadvid.php?filename=".$tilt_vid_files[0];
			$tilt_ogv = "loadvid.php?filename=".$tilt_vid_files[1];
			$tilt_webm = "loadvid.php?filename=".$tilt_vid_files[2];
			$html .= '<td><center><video id="tiltVideos" width="85" controls autoplay loop>
						  <source src="'.$tilt_mp4.'" type="video/mp4" loop>'.'<br />
						  <source src="'.$tilt_webm.'" type="video/webm" loop>'.'<br />
						  <source src="'.$tilt_ogv.'" type="video/ogg" loop>'.'<br />
						  HTML5 video is not supported by your browser.
						  </video></center></TD>';
		}else{
			$html .= "<td><center>--</center></TD>";
		}
	}
	
	//Additional information
	$protomo2aligner_logs = glob("$outdir/$path_chunks[1]/protomo2aligner_*.log");
	$protomo2aligner_logs = array_reverse($protomo2aligner_logs);
	if (file_exists($protomo2aligner_logs[0])) {
		$html .= '<td><a href="protomo2Log.php?runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'&log='.$protomo2aligner_logs[0].'" target="_blank"><center>Description<br>and Log</center></a></TD>';
	}else{
		$html .= "<td><center>--</center></TD>";
	}
	
	//Summary webpages
	if (count($refine_iterations) > 1){
		if (count($coarse_iterations) > 0){
			$html .= '<td><a href="protomo2CoarseTiltSummary.php?expId='.$_GET['expId'].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank"><center>Coarse<br>Summary</center></a>';
			$html .= '<center>--------------</center>';
			$html .= '<a href="protomo2TiltSummary.php?expId='.$_GET['expId'].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank"><center>Refinement<br>Summary</center></a></TD>';
		}else{
			$html .= '<td><a href="protomo2TiltSummary.php?expId='.$_GET['expId'].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank"><center>Refinement<br>Summary</center></a></TD>';
		}
	} elseif (count($coarse_iterations) > 0){
		$html .= '<td><a href="protomo2CoarseTiltSummary.php?expId='.$_GET['expId'].'&outdir='.$outdir.'&runname='.$path_chunks[1].'&tiltseries='.$tiltseriesnumber.'" target="_blank"><center>Coarse<br>Alignment<br>Summary</center></a></TD>';
	} else {
		$html .= "<td><center>--</center></TD>";
	}
	$html .= "</TR>";
}

$html .= "</table>";
$html .= "<br>";
$html .= "<b>To continue processing a tilt-series, <a href='runAppionLoop.php?expId=$expId&form=Protomo2CoarseAlignForm' target='_blank'>Click Here</a>, change the runname & output directory, and select the appropriate tilt-series, then continue on to the desired processing step.</b><br>";
//$html .= "<b>Estimate defocus or dose compensate existing tilt-series by continuing to Batch or to More Tilt-Series Processing.</b>";

if (count($all_recon_files) > 0) {
	$html .= "
	<hr />
	<H4><b>Available Reconstructions</b></H4>
	<hr />";
	
	foreach ($all_recon_files as $item) {
		$html .= '<br>'.$item;
	}
	$html .= '<br>';

}

$html .= "<br><hr /><b>Remove selected runs by <font color='green' size=4>(<u>carefully!!</u>)</font> running the following commands <font color='red' size=4>(checkboxes aren't meant to be unchecked!)</font>:</b><hr /><br>";
$html .= "<br><div id='container'></div><br>";
echo $html;

?>