<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 *	Display results for each iteration of a refinement
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

showReport();

function getNumClassesFromFile ($imagicfile) {
	$hedfile = $imagicfile;
	//var_dump($hedfile);
	if (substr($imagicfile, -4) == ".img")
		$hedfile = substr($imagicfile, 0, -4).".hed";
	if (!file_exists($hedfile)) {
		echo "MISSING HED FILE: $hedfile<br/>";
		return 0;
	}
	$size = filesize($hedfile);
	//echo "SIZE $size<br/>";
	$numclass = ceil($size/1024.0/2.0);
	return $numclass;
}


function showReport () {
	// check if reconstruction is specified
	if (!$hipId = $_GET['hipId'])
		$hipId=false;
	$expId = $_GET['expId'];

	$projectId=$_GET['projectId'];
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	//print_r($sessioninfo);

	$formAction = $_SERVER['PHP_SELF']."?expId=$expId&hipId=$hipId";

	$javascript = "<script src='../js/viewer.js'></script>\n";
	$javascript.="<script language='JavaScript' type='text/javascript'>
	function displayPopup(avgfile, dekfile) {
		newwindow=window.open('', 'name','height=200, width=1200, scrollbars=1');
		newwindow.document.write('<html><body>');
		newwindow.document.write('To edit ');
		newwindow.document.write(dekfile);
		newwindow.document.write(',');
		newwindow.document.write('<br>Copy and Paste this command into a terminal:');
		newwindow.document.write('<p><pre>tkll -f ');
		newwindow.document.write(avgfile);
		newwindow.document.write(' -d ');
		newwindow.document.write(dekfile);
		newwindow.document.write(' -cut</pre>');
		newwindow.document.write('<p>Right click to remove points, ');
		newwindow.document.write('<br>Left click to select points.');
		newwindow.document.write('<br>Select desired ranges and Save Data for next Hip Run.');
		newwindow.document.write('&nbsp;<br></body></html>');
		newwindow.document.close();
	}
	</script>\n";

	#href='tkllCmd.php?filename=$avgfile&cutfit=$cutfit1'

	processing_header("HIP Report","Helical Reconstruction Report Page", $javascript);
	if (!$hipId) {
		processing_footer();
		exit;
	}

	// --- Get Reconstruction Data
	$particle = new particledata();
	$processhost = $_SESSION['processinghost'];
	$stackId = $particle->getStackIdFromHipId($hipId);
	$stackparams = $particle->getStackParams($stackId);
	// get pixel size
	$apix=($particle->getStackPixelSizeFromStackId($stackId))*1e10;
	$boxsz = $stackparams['boxsize'];
	$stackparticles= $particle->getNumStackParticles($stackId);
	$hiprun=$particle->getHipRunInfo($hipId);
	//var_dump($hiprun);

	$stackfile=$stackparams['path']."/".$stackparams['name'];
	$res = $particle->getHighestResForHip($hiprun['DEF_id']);

	$title = "Recon Info";
	$reconinfo = array(
		'id'=>"<A HREF='hipsummary.php?expId=$expId'>$hiprun[DEF_id]</A>",
		'name'=>$hiprun['runname'],
		'description'=>$hiprun['description'],
		'path'=>$hiprun['path'],
		'refine package'=>$hiprun['package'],
		'best resolution'=>	sprintf("% 2.2f / % 2.2f &Aring; (%d)", $res[half],$res[rmeas],$res[iter]),
	);

	$particle->displayParameters($title,$reconinfo,array(),$expId);
	//var_dump($particle);

	// use summarytables.inc
	echo "<br></br>";
	echo ministacksummarytable($stackId);
	$mpix = $particle->getStackPixelSizeFromStackId($stackId);

	$hipParams = $particle->getHipParamsInfo($hipId);

	if ($hipParams) {
		$html .= "<form name='alignments' method='post' action='$formAction'>\n";
		$html .= "<br>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
		$html .= "<TR>\n";
		$display_keys = array ( 'Layer Line/<br>Bessel Order', 'Strong LL', 'Ranges', 'Aligned Stack');
		$numcols = count($display_keys);
		foreach($display_keys as $key) {
	 	       $html .= "<td><center><span class='datafield0'>".$key."</span> </TD> ";
		}
		$html .= "</tr>\n";

		// GET INFO
		$path = $hiprun['path'];
		$llbo = $hipParams['llbo'];
		$strong = $hipParams['strong'];
		$range= $hipParams['range'];
		$rescut= $hipParams['rescut'];
		$finalstack = $hipParams['final_stack'];
		$html .= "<h4>Alignment Info</h4>\n";
		$html .= "<tr>\n";
		#$html .= "<td><center>$path</center></td>\n";
		$html .= "<td><a href='loadtxt.php?filename=$llbo'>\n"
			."<center>llbo.sa</center></td>\n";
		$html .= "<td><a href='loadtxt.php?filename=$strong'>\n"
			."<center>strong.sa</center></td>\n";
		$html .= "<td><a href='loadtxt.php?filename=$range'>\n"
			."<center>range.sa</center></td>\n";
		$html .= "<td><a href='viewstack.php?file=$finalstack' target='Final Stack'>\n"
			."<center>start.hed</center></td>\n";
		$html .= "</table>\n";
	}

	$html .= "<form name='averaging' method='post' action='$formAction'>\n";
	$html .= "<br>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'Iter', 'Path', '', 'Res', 'cutfit.dek', 'chop.dek', 'List', 'Num Part', 'Num Sub', 'Layer Lines', 'Overplots', '', 'Snapshots of Map');
	$numcols = count($display_keys);
	foreach($display_keys as $key) {
		$html .= "<td><center><span class='datafield0'>".$key."</span> </TD> ";
	}
	$html .= "</tr>\n";

	$html .= "<h4>Averaging Info</h4>\n";
	$html .= "<tr>\n";
	$iterations = $particle->getHipIterInfo($hipId);
	//print_r($iterations);


	//************************
	//************************
	// show info for each iteration
	foreach ($iterations as $iteration){

		// GET INFO
		$iternum = $iteration['iteration'];
		$ref=$particle->getHipRefinementData($hiprun['DEF_id'], $iternum);
		$refineIterData=$ref[0];
		$refineIterId = $refineIterData['DEF_id'];
		$iterpath = $iteration['iterpath'];
		if (!$iterpath) {
			if ($iternum == 1) {
				$iterpath = ($path.'/avgsnif1');
			} elseif ($iternum == 2) {
				$iterpath = ($path.'/avgsnif1/avgsnif2');
			} elseif ($iternum == 3) {
				$iterpath = ($path.'/avgsnif1/avgsnif2/avg3');
			}
		}
		$cutfit1 = $iteration['cutfit1'];
		$cutfit2 = $iteration['cutfit2'];
		$cutfit3 = $iteration['cutfit3'];
		$chop1 = $iteration['chop1'];
		$chop2 = $iteration['chop2'];
		$listfile = $iteration['avglist_file'];
		$fnumpart = $iteration['final_numpart'];
		$asymsu = $iteration['asymsu'];
		$avgfile = $iteration['avg_file'];	
		$mapfile = $iteration['map_file'];
		$mrcfile = $iteration['mrc_file'];
		$llfile = $iteration['ll_file'];
		$opfile = $iteration['op_file'];
		$outfile = $iteration['output_file'];
		$res = $particle->getResolutionInfo($iteration['REF|ApResolutionData|resolution']);
		$fscid = ($res) ? $refineIterId : False;
		$fscfile = ($res) ? $res['fscfile'] : "None" ;
		$halfres = ($res) ? sprintf("%.2f",$res['half']) : "None" ;
		$rmeasId = $iteration['REF|ApRMeasureData|rMeasure'];
		$rmeas = $particle->getRMeasureInfo($rmeasId);
		$rmeasureres = ($rmeas) ? sprintf("%.2f",$rmeas['rMeasure']) : "None" ;
		$pngimages = getPngList($iterpath);
		$llsnapfile = ($iterpath.'/avglist3_'.$rescut.'pll-01.png');
		$opsnapfile = ($iterpath.'/avglist3_'.$rescut.'pop-01.png');

		$html .= "<tr>\n";
		$html .= "<td><font size=+1>$iternum</font></td>\n";
		$html .= "<td width='10%'><center>$iterpath</center></td>\n";
		$html .= "<td bgcolor='#dddddd'></td>\n";
		if ($halfres!='None' && $fscfile) {
			$html .= "<td bgcolor='$bg'><a href='fscplot.php?expId=$expId&fscfile=$fscfile&width=800&height=600&apix=$apix&box=$boxsz'"
				." target='snapshot'><img src='fscplot.php?expId=$expId&fscfile=$fscfile&width=100&height=80&nomargin=TRUE'></a><br />\n";
		} else {
			$html .= "<td bgcolor='$bg'>\n";
		}
		$html .= "<center><I>FSC&frac12;:</I><br />$halfres &Aring;</center><br />\n";
		if ($rmeasureres!='None') {
			$html .= "<center><I>Rmeas:</I><br>$rmeasureres &Aring;</center>\n";
		}
		$html .= "</TD>";
		$html .= "<td/><center><a href='loadtxt.php?filename=$cutfit1'>\n"
			."<br>cutfit1.dek</a>\n"
			."<input type='button' name='Edit Dek' value='Edit' onclick='displayPopup(\"$avgfile\", \"$cutfit1\")'>\n"
			."<br><a href='loadtxt.php?filename=$cutfit2'>\n"
			#."<center><input type='button' onclick='openTkll.php?filename=$avgfile&cutfit=$cutfit1&expId=$expId&rundir=$path' value='Edit'/></center>\n"
			#."<br><a href='openTkll.php?filename=$avgfile&cutfit=$cutfit1&expId=$expId&rundir=$path'>\n"
			#."<br>CLICK ME</a>\n"
			."<br>cutfit2.dek</a>\n"
			."<input type='button' name='Edit Dek' value='Edit' onclick='displayPopup(\"$avgfile\", \"$cutfit2\")'>\n"
			."<br><a href='loadtxt.php?filename=$cutfit3'>\n"
			."<br>cutfit3.dek</a>\n"
			."<input type='button' name='Edit Dek' value='Edit' onclick='displayPopup(\"$avgfile\", \"$cutfit3\")'></center></td>\n";
		if ($iternum == 1) {
			$html .= "<td><center><a href='loadtxt.php?filename=$chop1'>\n"
				."<br>chop1.dek</a>\n"
				."<input type='button' name='Edit Dek' value='Edit' onclick='displayPopup(\"$avgfile\", \"$chop1\")'></center></td>\n";
		}
		if ($iternum == 2) {
			$html .= "<td><center><a href='loadtxt.php?filename=$chop2'>\n"
				."<br>chop2.dek</a>\n"
				."<input type='button' name='Edit Dek' value='Edit' onclick='displayPopup(\"$avgfile\", \"$chop2\")'></center></td>\n";
		}
		if ($iternum == 3) {
			$html .= "<td><center>No sniffing in final iteration</center></td>\n";
		}
		$html .= "<td><a href='loadtxt.php?filename=$listfile' target='List'>\n"
			.sprintf("<center>avglist3_%dp.list</center></a></td>\n", $rescut);
		$html .= "<td><center>$fnumpart</center></td>\n";
		$html .= "<td><center>$asymsu</center></td>\n";
		$html .= "<td bgcolor='$bg'>\n";
		foreach ($pngimages['pngfiles'] as $snapshot) {
			if (preg_match('%'.$llsnapfile.'%i',$snapshot)) {
				$snapfile = $snapshot;
				$html .= "<a href='loadps.php?filename=$llfile&path=$path'  target='Layer Lines'"
					."<center><img src='loadimg.php?s=80&filename=$snapfile' HEIGHT='80'></center></a>\n";
			}
		}
		$html .= sprintf("<center>avglist3_%dpll.ps</center>\n", $rescut)
			."<br><a href='download.php?file=$avgfile'>\n"
			."<center><img style='vertical-align:middle' src='img/download_arrow.png' border='0' width='16' height='17'>\n"
			."Download Average</center></a><br/>\n";
		$html .= "<td bgcolor='$bg'>\n";
		foreach ($pngimages['pngfiles'] as $snapshot) {
			if (preg_match('%'.$opsnapfile.'%i',$snapshot)) {
				$snapfile = $snapshot;
				$html .= "<a href='loadps.php?filename=$opfile&path=$path'  target='Overplots'"
					."<center><img src='loadimg.php?s=80&filename=$snapfile' HEIGHT='80'></center></a>\n";
			}
		}
		$html .= sprintf("<center>avglist3_%dpop.ps</center>\n", $rescut)
			."<br></br>"
			."<br></br>"
			."<br></br>"
			."<br></br>";
		$html .= "<td bgcolor='#dddddd'></td>\n";
		$html .= "<td bgcolor='$bg'>\n";
		#$html .= "<td bgcolor='$bg'>\n";
		foreach ($pngimages['pngfiles'] as $snapshot) {
			if (preg_match('%'.$mrcfile.'%i',$snapshot)) {
				$snapfile = $snapshot;
				$html .= "<a href='loadimg.php?filename=$snapfile' target='snapshot'>"
					."<img src='loadimg.php?s=80&filename=$snapfile' HEIGHT='80'></a>\n";
			}

		}
		$html .= "<br><a href='download.php?file=$mapfile'>\n"
			."<center><img style='vertical-align:middle' src='img/download_arrow.png' border='0' width='16' height='17'>\n"
			."Download Map</center></a><br/>\n";
		$html .= "<center><input class='edit' type='button' onClick=\"parent.location='hippostproc.php?expId=$expId&refineIter=$refineIterId'\" value='Post Processing'></center>\n";

		// check for post procs
		$postprocs = $particle->getPostProcsFromHipRefId($refineIterId);
		if ($postprocs[0]) {
			$html .= "<tr>\n";
			foreach ($postprocs as $p) {
				# get list of png files in directory
		  		$procimgs = getPngList($p['path']);
				$html .= "<td bgcolor='$bg' colspan='".($numcols-1)."'>\n";
				$html .= "<b>Post Processing of ".$iteration['volumeDensity']."</b>\n";
				if ($p['handflip']) $html .= "(handedness flipped)\n";
				$html .= "<table border='0' cellpadding='0' cellspacing='0'>\n";
				$html .= "<tr><td><b>path: </b></td><td>".$p['path']."</td></td>\n";

				$postprocfile = $p['path']."/".$p['name'];
				$modellink .= "<font size='-2'><a href='download.php?file=$postprocfile'>\n";
				$modellink .= "  <img style='vertical-align:middle' src='img/download_arrow.png' border='0' width='16' height='17' alt='download model'>\n";
				$modellink .= "</a></font>\n";
				$html .= "<tr><td><b>name: </b></td><td>".$p['name']." $modellink</td></td>\n";

				if ($p['ampName']) $html .= "<tr><td><b>ampcor file: </b></td><td>".$p['amppath']."/".$p['ampName']."</td></tr>\n";
				if ($p['lowpass']) $html .= "<tr><td><b>low pass filter: </b></td><td>".$p['lowpass']." angstroms</td></tr>\n";
				if ($p['highpass']) $html .= "<tr><td><b>high pass filter: </b></td><td>".$p['highpass']." angstroms</td></tr>\n";
				if ($p['mask']) {
				  	// convert to pixels
				  	$boxang = $p['mask']*$apix;
				  	$html .= "<tr><td><b>mask: </b></td><td>$boxang Angstroms (".$p['mask']." pixels)</td></tr>\n";
				}
				if ($p['imask']) {
				  	// convert to pixels
				  	$boxang = $p['imask']*$apix;
					$boxang = sprintf("%.1f",$boxang);
				  	$html .= "<tr><td><b>inner mask: </b></td><td>$boxang Angstroms (".$p['imask']." pixels)</td></tr>\n";
				}
				if ($p['maxjump']) $html .= "<tr><td><b>jumper cutoff: </b></td><td>".$p['maxjump']."&deg;</td></tr>\n";
				if ($p['sigma']) $html .= "<tr><td><b>sigma cutoff: </b></td><td>".$p['sigma']."</td></tr>\n";
				if ($p['resolution']) $html .= "<tr><td><b>FSC 0.5: </b></td><td>".sprintf("%.2f",$p['resolution'])."</td></tr>\n";
				if ($p['rmeasure']) $html .= "<tr><td><b>Rmeas 0.5: </b></td><td>".sprintf("%.2f",$p['rmeasure'])."</td></tr>\n";
				$html .= "</table>\n";
				$html .= "</td><td>\n";
				foreach ($procimgs['pngfiles'] as $s) {
				  	if (preg_match('%'.$p['name'].'%i',$s)) {
						$sfile = $s;
						$html .= "<a href='loadimg.php?filename=$sfile' target='snapshot'>"
							."<img src='loadimg.php?s=80&filename=$sfile' height='80'></a>\n";
					}
				}
				$html .= "</td>\n";
				$html .= "</tr>\n";
			}
		}	  
	}
	$html .= "</form>\n";
	
	"</td></tr>\n";
	$html .= "</table>\n";
	echo $html;

	processing_footer();
};
?>
