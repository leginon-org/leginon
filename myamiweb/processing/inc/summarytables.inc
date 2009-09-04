<?php
/**
 *  The Leginon software is Copyright 2003 
 *  The Scripps Research Institute, La Jolla, CA
 *  For terms of the license agreement
 *  see  http://ami.scripps.edu/software/leginon-license
 *
 *	summary tables for common appion objects
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

/****************************************
****************************************/
function stacksummarytable($stackid, $mini=false, $tiny=false) {
	$expId = $_GET['expId'];
	$particle = new particledata();
	$stackdata = $particle->getStackParams($stackid);

	if ($_POST['updateDesc'.$stackid])
		updateDescription('ApStackData', $stackid, $_POST['newdescription'.$stackid]);

	if ($_POST['hideStack'.$stackid] == 'hide') {
		$particle->updateHide('ApStackData', $stackid, '1');
		$stackdata['hidden']=1;
	} elseif ($_POST['unhideStack'.$stackid] == 'unhide') {
		$particle->updateHide('ApStackData', $stackid, '0');
		$stackdata['hidden']='0';
	}

	$numpart = $particle->getNumStackParticles($stackid);
	if ($numpart == 0) return;

	
	$stackname = $stackdata['shownstackname'];
	$stackfile = $stackdata['path']."/".$stackdata['name'];
	$j = "Stack Info: <a class='aptitle' href='stackreport.php?expId=$expId&sId=$stackid'>"
		.$stackname."</a> (ID: $stackid)\n";
	if ($stackdata['hidden'] == 1) {
		$j.= " <font color='#cc0000'>HIDDEN</font>\n";
		$j.= " <input class='edit' type='submit' name='unhideStack".$stackid."' value='unhide'>\n";
		$display_keys['hidden']="<font color='#cc0000'>HIDDEN</font>";
	} else $j.= " <input class='edit' type='submit' name='hideStack".$stackid."' value='hide'>\n";

	$stacktable.= apdivtitle($j);
	if ($tiny)
		return $stacktable;


	// if particles were centered, set centered variable
	if ($stackdata['centered'] == 1) {
		$centered = True;
	}

	// if particles were junk sorted, set junk sorted variable
	if ($stackdata['junksorted'] == 1) {
		$junksorted = True;
	}

	$stacktable.= "<table border='0' width='700' >\n";
	$stackavg = $stackdata['path']."/average.mrc";
	$badstackavg = $stackdata['path']."/badaverage.mrc";
	$montage = $stackdata['path']."/montage".$stackdata['DEF_id'].".png";
	if (!$mini && file_exists($stackavg)) {
		$stacktable.= "<tr>\n";
		$stacktable.= "<td  align='left' rowspan='30' align='center' valign='top'>";
		$stacktable.= "<img src='loadimg.php?filename=$stackavg&s=150' height='150'><br/>\n";
		$stacktable.= "<i>averaged stack image</i>\n";
		if (!$centered) $stacktable.= "<br /><a href='centerStack.php?expId=$expId&sId=$stackid'>[Center Particles]</a>\n";
		if (!$junksorted) $stacktable.= "<br /><a href='sortJunk.php?expId=$expId&sId=$stackid&junksort=1'>[Sort Junk]</a>\n";
		if ($junksorted) $stacktable.= "<br /><a href='viewstack.php?file=$stackfile&expId=$expId&stackId=$stackid&junksort=1'>[Apply Junk Cutoff]</a>\n";

		$stacktable.= "<br /><a href='subStack.php?expId=$expId&sId=$stackid'>[Create Substack]</a>\n";
		$stacktable.= "</td>\n";
		if ($centered && file_exists($badstackavg)) {
			$stacktable.= "<td  align='left' rowspan='30' align='center' valign='top'>";
			$stacktable.= "<img src='loadimg.php?filename=$badstackavg&s=150' height='150'><br/>\n";
			$stacktable.= "<i>averaged bad stack</i><br/>\n";
			$stacktable.= "</td>\n";
		} elseif (file_exists($montage)) {
			$stacktable.= "<td align='left' rowspan='30' align='center' valign='top'>";
			$stacktable.= "<a href='loadimg.php?filename=$montage'>\n";
			$stacktable.= "<img border=0 src='loadimg.php?filename=$montage&s=150' height='150'></a><br/>\n";
			$stacktable.= "<i>mean/stdev montage</i><br/>\n";
			$stacktable.= "<a href='subStack.php?expId=$expId&sId=$stackid&mean=1'>[Filter by Mean/Stdev]</a>\n";
			$stacktable.= "</td>\n";
		}
		$stacktable.= "</tr>\n\n";
	} elseif (file_exists($stackavg)) {
		// mini version
		$stacktable.= "<tr >\n";
		$stacktable.= "<td align='center' rowspan='30' align='center' valign='top'>";
		$stacktable.= "<img src='loadimg.php?filename=$stackavg&s=80' height='80'><br/>\n";
		$stacktable.= "<i>average</i>\n";
		if (!$junksorted)
			$stacktable.= "<br/><font size='-2'><a href='sortJunk.php?expId=$expId&sId=$stackid&junksort=1'>[Sort Junk]</a></font>\n";
		if ($junksorted)
			$stacktable.= "<br/><font size='-2'><a href='viewstack.php?file=$stackfile&expId=$expId&stackId=$stackid&junksort=1'>[Apply Junk Cutoff]</a></font>\n";
		$stacktable.= "</td></tr>\n\n";
	} #endif

	// get pixel size of stack
	$mpix=($particle->getStackPixelSizeFromStackId($stackid));
	$apix=format_angstrom_number($mpix)."/pixel";

	// get box size
	$boxsz=($stackdata['bin']) ? $stackdata['boxSize']/$stackdata['bin'] : $stackdata['boxSize'];
	$boxsz.=" pixels";

	$display_keys['date time'] = $stackdata['DEF_timestamp'];
	for($i=0; $i<=10; $i++) {
		if ($stackdata[$i]['sessionid']) {
			$sessionid = $stackdata[$i]['sessionid'];
			$sessiondata = $particle->getSessionData($sessionid);
			$display_keys['session id'].="<a href='index.php?expId=".$sessiondata['DEF_id']."'>"
				.$sessiondata['name']."</a>&nbsp;\n";
		}
	}

	// add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($stackid,$stackdata['description']) : $stackdata['description'];
	if (!$mini) 
		$display_keys['description']=$descDiv;
	else
		$display_keys['descript']="<font size='-2'>$descDiv</font>";

	// Show number of particles
	$oldnumpart = $particle->getNumStackParticles($stackdata['REF|ApStackData|oldstack']);
	if ($mini)
		$display_keys['size']= commafy($numpart)." / ".getStackSize($stackdata);
	elseif ($oldnumpart > $numpart) {
		$display_keys['# particles']= commafy($numpart)." (".commafy($oldnumpart-$numpart)." bad)";
	} else 
		$display_keys['# particles'] = commafy($numpart);

	if (!$mini) {
		// Number images used to make stack
		$display_keys['# images used']=$particle->getNumStackImages($stackid);
		// Get filesize
		$display_keys['file size'] = getStackSize($stackdata);
	}

	if ($mini) {
		$display_keys['path'] = "<font size='-2'>".$stackdata['path']
			."/<a href='viewstack.php?file=$stackfile&expId=$expId&stackId=$stackid&ps=$mpix'>"
			.$stackdata['name']."</a></font>";
		$display_keys['box/apix'] = $boxsz." / ".$apix;
	} else {
		$display_keys['path']=$stackdata['path'];
		$display_keys['stack file']= "<a target='stackview' HREF='viewstack.php?file="
			."$stackfile&expId=$expId&stackId=$stackid&ps=$mpix'>".$stackdata['name']."</A>";
		# if stack was created by cenalignint, also view avg & bad stacks
		if ($centered) {
			$display_keys['iterative avgs']="<a target='stackview' HREF='viewstack.php?file=".$stackdata['path']
				."/avg.hed&expId=$expId'>avg.hed</A>";
			$display_keys['stack file'].=" &nbsp;(<a target='stackview' HREF='viewstack.php?file=".$stackdata['path']
				."/bad.hed&expId=$expId'>bad.hed</A>)";
		}
		$display_keys['box size']=$boxsz;
		$display_keys['pixel size']=$apix;
	}

	if (!$mini) {
		# use values from first of the combined run, if any for now	
		$pflip = ($stackdata['phaseFlipped']==1) ? "yes" : "no";
		if ($stackdata['fliptype']) $pflip.= ", ".$stackdata['fliptype'];
		if ($stackdata['aceCutoff']) $pflip.=" (ACE > $stackdata[aceCutoff])";
		
		$display_keys['ctf correct']=$pflip;
		//$display_keys['raw data'] = print_r($stackdata);

		if ($stackdata['correlationMin']) $display_keys['correlation min']=$stackdata['correlationMin'];
		if ($stackdata['correlationMax']) $display_keys['correlation max']=$stackdata['correlationMax'];
		if ($stackdata['minDefocus']) $display_keys['min defocus']=$stackdata['minDefocus'];
		if ($stackdata['maxDefocus']) $display_keys['max defocus']=$stackdata['maxDefocus'];
		$display_keys['density']=($stackdata['inverted']==1) ? 'inverted' : 'not inverted';
		$display_keys['normalization']=($stackdata['normalized']==1) ? 'no' : 'yes';
		if ($stackdata['tiltangle'] && $stackdata['tiltangle']!='all') $display_keys['tilt angle'] = $stackdata['tiltangle'];
		//$partruns = $particle->getParticleRunsFromStack($stackid);
		//print_r($partruns);
		$partrun = $particle->getStackSelectionRun($stackid);
		//print_r($partrun);
		if($partrun) {
			$parturl = "particlerunreport.php?expId=$expId&rId=".$partrun[0]['selectionid'];
			$display_keys['selection run'] = "<a href='$parturl'>".$partrun[0]['name']."</a> (".$partrun[0]['selectionid'].")";;
		}
	}
	//echo print_r($stackdata)."<br/><br/>";
	//$display_keys['file type']=$stackdata['fileType'];
	foreach($display_keys as $k=>$v) {
	        $stacktable.= formatHtmlRow($k,$v);
	}
	$stacktable.= "</table>\n";
	$stacktable.= "<p>\n";
	return $stacktable;
}

/****************************************
****************************************/
function ministacksummarytable($stackid) {
	return stacksummarytable($stackid, true);
}

/****************************************
****************************************/
function alignstacksummarytable($alignstackid, $mini=false) {
	$expId = $_GET['expId'];
	$particle = new particledata();
	$stackdata = $particle->getAlignStackParams($alignstackid);
	//echo print_r($stackdata)."<br/>\n";

	if ($stackdata['REF|ApSpiderNoRefRunData|norefrun'])
		$type = 'none';
	elseif ($stackdata['REF|ApRefBasedRunData|refbasedrun'])
		$type = 'score';
	elseif ($stackdata['REF|ApEdIterRunData|editerrun'])
		$type = 'score';
	elseif ($stackdata['REF|ApMaxLikeRunData|maxlikerun'])
		$type = 'spread';
	elseif ($stackdata['REF|ApMultiRefAlignRunData|imagicMRA'])
		$type = 'correlation';
	else
		$type = 'score';

	if ($_POST['updateDesc'.$alignstackid])
		updateDescription('ApAlignStackData', $alignstackid, $_POST['newdescription'.$alignstackid]);

	if ($_POST['hideStack'.$alignstackid] == 'hide') {
		$particle->updateHide('ApAlignStackData', $alignstackid, '1');
		$stackdata['hidden']='1';
	} elseif ($_POST['unhideStack'.$alignstackid] == 'unhide') {
		$particle->updateHide('ApAlignStackData', $alignstackid, '0');
		$stackdata['hidden']='0';
	}

	$numpart = $particle->getNumAlignStackParticles($alignstackid);
	//echo $numpart."<br/>\n";

	$j = "Align Stack Info: <span class='aptitle' >"
		.$stackdata['runname']."</span> (ID: $alignstackid)\n";
	if ($stackdata['hidden'] == 1) {
		$j.= " <font color='#cc0000'>HIDDEN</font>\n";
		$j.= " <input class='edit' type='submit' name='unhideStack".$alignstackid."' value='unhide'>\n";
		$display_keys['hidden']="<font color='#cc0000'>HIDDEN</font>";
	} else $j.= " <input class='edit' type='submit' name='hideStack".$alignstackid."' value='hide'>\n";

	$stacktable.= apdivtitle($j);
	//echo $j."<br/>\n";


	$stacktable.= "<table border='0'>\n";
	$stackavg = $stackdata['path']."/average.mrc";
	if (file_exists($stackavg)) {
		$stacktable.= "<tr>\n";
		$stacktable.= "<td rowspan='30' align='center' valign='top'>";
		if ($mini) {
			$stacktable.= "<img src='loadimg.php?filename=$stackavg&h=60' height='60'><br/>\n";
			$stacktable.= "<i>avg image</i>\n";
		} else {
			$stacktable.= "<img src='loadimg.php?filename=$stackavg&h=120' height='120'><br/>\n";
			$stacktable.= "<i>averaged stack image</i>\n";
		}
		$stacktable.= "</td>\n";

		if ($type != "none") {
			$stacktable.= "<td rowspan='30' align='center' valign='top'>";
			$stacktable.= "<a href='aligngraph.php?expId=$expId&alignid=$alignstackid&type=$type'>\n";
			if ($mini)
				$stacktable.= "<img border='0' src='aligngraph.php?expId=$expId&alignid=$alignstackid&h=60&type=$type' height='60'><br/>\n";
			else
				$stacktable.= "<img border='0' src='aligngraph.php?expId=$expId&alignid=$alignstackid&h=120&type=$type' height='120'><br/>\n";
			$stacktable.= "</a><i>$type distribution</i>\n";
			$stacktable.= "</td>\n";
		}

		$stacktable.= "</tr>\n\n";
	} #endif

	// add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($alignstackid, $stackdata['description']) : $stackdata['description'];

	$display_keys['date time'] = $stackdata['DEF_timestamp'];
	$display_keys['description']=$descDiv;

	// Show number of particles


	// Get filesize
	if (substr($stackdata['imagicfile'], -4) == ".hed")
		$stackimgfile = $stackdata['path']."/".substr($stackdata['imagicfile'], 0, -4).".img";
	if (filesize($stackimgfile) > 1073741824)
		$filesize = sprintf("%.2f GB", filesize($stackimgfile)/1073741824);
	else
		$filesize = sprintf("%.1f MB", filesize($stackimgfile)/1048576);

	if ($mini)
		$display_keys['size']=commafy($numpart)." particles (".$filesize.")";
	else {
		$display_keys['# particles']=commafy($numpart);
		$display_keys['file size'] = $filesize;
	}

	$origstackid = $stackdata['REF|ApStackData|stack'];
	$origstackdata = $particle->getStackParams($origstackid);
	$origpixelsize = $origstackdata['pixelsize'];  // --- Angstrom ?
	$origps = $origpixelsize; 
	$display_keys['original stack'] = "<a href='stackreport.php?expId=$expId&sId=$origstackid'>$origstackid</a>";
	$refstack = $stackdata['path']."/".$stackdata['refstackfile'];
	if ($stackdata['refstackfile'] && file_exists($refstack))
		$display_keys['reference stack'] = "<a target='stackview' HREF='viewstack.php?"
			."file=$refstack&expId=$expId&ps=$origps&alignId=$alignstackid'>".$stackdata['refstackfile']."</a>";

	$stackfile = $stackdata['path']."/".$stackdata['imagicfile'];

	$pixelsize = $stackdata['pixelsize']; // --- Angstrom ?

	// --- pixel size in meter --- //
	$ps = $pixelsize * 1e-10;
	if ($mini) {
		$display_keys['pixel / box size']=round($pixelsize,2)." &Aring;/pixel and ".$stackdata['boxsize']." pixels";
		$display_keys['stack file']=$stackdata['path']."/<a target='stackview' HREF='viewstack.php?file=$stackfile&expId=$expId&ps=$ps'>"
			.$stackdata['imagicfile']."</a>";
	} else {
		// get box size
		$display_keys['box size']=$stackdata['boxsize']." pixels";
		// get pixel size of stack
		$display_keys['pixel size']=round($pixelsize,2)." &Aring;/pixel";
		$display_keys['filter']=$stackdata['lp_filt']." and ".$stackdata['hp_filt']." &Aring;";
		//$display_keys['run time']=round($stackdata['run_seconds']/60.0,2)." minutes";
		$display_keys['path']=$stackdata['path'];
		$display_keys['stack file']="<a target='stackview' HREF='viewstack.php?file=$stackfile&expId=$expId&ps=$ps'>"
			.$stackdata['imagicfile']."</A>";
	}

	//$display_keys['file type']=$stackdata['fileType'];
	foreach($display_keys as $k=>$v) {
	        $stacktable.= formatHtmlRow($k,$v);
	}
	$stacktable.= "</table>\n";
	$stacktable.= "<p>\n";
	return $stacktable;
}

/****************************************
****************************************/
function analysissummarytable($analysisid, $mini=false) {
	$expId = $_GET['expId'];
	$particle = new particledata();
	$analysisdata = $particle->getAnalysisParams($analysisid);
	if ($analysisdata['REF|ApImagicAlignAnalysisData|imagicMSArun']) {
	        $imagicrun = $particle->getImagicAnalysisParams($analysisid);
	}

	if ($_POST['updateDesc'.$analysisid])
		updateDescription('ApAlignAnalysisRunData', $analysisid, $_POST['newdescription'.$analysisid]);

	if ($_POST['hideAnalysis'.$analysisid] == 'hide') {
		$particle->updateHide('ApAlignAnalysisRunData', $analysisid, '1');
		$analysisdata['hidden']='1';
	} elseif ($_POST['unhideAnalysis'.$analysisid] == 'unhide') {
		$particle->updateHide('ApAlignAnalysisRunData', $analysisid, '0');
		$analysisdata['hidden']='0';
	}

	$j = "Analysis Info: <span class='aptitle'>"
		.$analysisdata['runname']."</span> (ID: $analysisid)\n";
	if ($analysisdata['hidden'] == 1) {
		$j.= " <font color='#cc0000'>HIDDEN</font>\n";
		$j.= " <input class='edit' type='submit' name='unhideAnalysis".$analysisid."' value='unhide'>\n";
		$display_keys['hidden']="<font color='#cc0000'>HIDDEN</font>";
	} else $j.= " <input class='edit' type='submit' name='hideAnalysis".$analysisid."' value='hide'>\n";

	$analysistable.= apdivtitle($j);
	//echo $j."<br/>\n";

	$analysistable.= "<table border='0' align='center' valign='top'>\n";
	// open table row
	$analysistable.= "<tr>\n";

	$dendrogram = $analysisdata['path']."/dendrogram.png";
	if (file_exists($dendrogram)) {

		$analysistable.= "<td rowspan='30' align='center' valign='top'>";
		$analysistable.= "<a href='loadimg.php?filename=$dendrogram'>\n";
		if ($mini)
			$analysistable.= "<img src='loadimg.php?filename=$dendrogram&s=60' height='60' border='1'></a><br/>\n";
		else
			$analysistable.= "<img src='loadimg.php?filename=$dendrogram&s=160' height='160' border='1'></a><br/>\n";
		$analysistable.= "<i>dendrogram</i>\n";
		$analysistable.= "</td>\n";

	} #endif

	// eigen images
	$eigendata = $particle->getCoranEigenDataFromAnalysis($analysisid);
	if(!$mini && $eigendata) {
		$analysistable.= "<td rowspan='30' align='center' valign='top'>\n";
		$analysistable.= "<table class='tablebg' border='0' cellpadding='2'>\n";
		$analysistable.= "<tr>\n";
		foreach ($eigendata as $edata) {
			$analysistable.= "<td>\n";
			$index = (int) $edata['num'];
			$efile = $edata['path']."/".$edata['name'];
			$contrib = round($edata['contrib'],1);
			$level = dechex($contrib/$eigendata[0]['contrib']*239 + 16);
			$analysistable.=  "<a href='loadimg.php?filename=$efile' target='eigenimage'>\n"
				."<img src='loadimg.php?filename=$efile&s=48' width='48' height='48' border='0'></a><br />\n";
			$imgname = 'eigenimg'.$index;
			$analysistable.=  "<center>$index ";
			// when first loading page select first 3
			// eigenimgs, otherwise reload selected
			$analysistable.=  "<font color='#".$level."2222' size='-2'>($contrib %)</font></center>\n";
			$analysistable.=  "</td>\n";
			if ($index % 3 == 0) $analysistable.= "</tr>\n";
			if ($index >= 9) break;
		}
		if ($index % 3 != 0) $analysistable.= "</tr>\n";
		$analysistable.=  "</table>\n";
	}

	// close table row
	$analysistable.= "</tr>\n\n";

	// add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($analysisid, $analysisdata['description']) : $analysisdata['description'];

	$display_keys['date time'] = $analysisdata['DEF_timestamp'];
	$display_keys['description']=$descDiv;
	$display_keys['path']=$analysisdata['path'];
	if (!$mini)
		if ($analysisdata['REF|ApCoranRunData|coranrun']) {
			$display_keys['number of factors']=$analysisdata['num_factors'];
		}
		elseif ($imagicrun) {
			$display_keys['number of factors']="69 IMAGIC eigenimages";
		}
	if (!$mini)
		$display_keys['run time']=round($analysisdata['run_seconds']/60.0,2)." minutes";
	if (!$mini)
		if ($analysisdata['REF|ApCoranRunData|coranrun']) {
			$display_keys['mask diam']=$analysisdata['mask_diam']." &Aring;ngstroms";
		}
		elseif ($imagicrun) {
			$display_keys['mask radius']=$imagicrun['mask_radius']." (fraction of inner radius)";
		}
	// imagic-specific parameters
	if (!$mini && $imagicrun) {
		$display_keys['mask dropoff'] = $imagicrun['mask_dropoff'];
		$display_keys['hp filt'] = $imagicrun['highpass']. " &Aring;ngstroms";
		$display_keys['lp filt'] = $imagicrun['lowpass']." &Aring;ngstroms";
		$display_keys['bin'] = $imagicrun['bin'];
		$display_keys['overcorrection factor'] = $imagicrun['overcorrection'];
		$display_keys['MSA method'] = $imagicrun['MSAmethod'];
	}



	// show data
	foreach($display_keys as $k=>$v) {
		$analysistable.= formatHtmlRow($k,$v);
	}

	$analysistable.= "</table>\n";
	$analysistable.= "<p>\n";
	return $analysistable;
}

/****************************************
****************************************/
function clustersummarytable($clusterrunid, $mini=false) {
	$clustertable = "";
	$expId = $_GET['expId'];
	$particle = new particledata();
	$clusterrun = $particle->getClusteringRunParams($clusterrunid);
	$clusterrunname = $clusterrun['runname'];
	$clusterdatas = $particle->getClusteringStacksForClusteringRun($clusterrunid, false);
	if ($clusterdatas) {
		$clustertable .= apdivtitle("Clustering Info: <span class='aptitle'>$clusterrunname</span>"
			." (ID: $clusterrunid) with ".count($clusterdatas)." clusters\n");
		$clustertable .= "<br/>";
		if ($clusterrun['REF|ApImagicAlignAnalysisData|imagicMSArun']) {
			$clustertable .= "<b>Type:</b> <i>Imagic MSA</i><br/>\n";
			$clustertable .= "<ul>\n";
		} elseif ($clusterrun['REF|ApSpiderClusteringParamsData|spiderparams']) {
			$clustertable .= "<b>Type:</b> <i>SPIDER Coran</i><br/>\n";
			$clustertable .= "<b>Method:</b> <i>".$clusterrun['method']."</i><br/>\n";
			$clustertable .= "<b>Factor list:</b> <i>".$clusterrun['factor_list']."</i>\n";
			$clustertable .= "<ul>\n";
		} elseif ($clusterrun['REF|ApKerDenSOMParamsData|kerdenparams']) {
			// KerDen only has one cluster data
			$clusterdata = $clusterdatas[0];
			$clusterid = $clusterdata['clusterid'];
			$clusterpixelsize = $clusterdata['pixelsize'] * 1e-10; // Angstrom ????
			$clustertable .= "<b>Type:</b> <i>Xmipp KerDen SOM</i><br/><br/>\n";

			$montagefile = $clusterdata['path']."/"."montage.png";
			$clustertable .= "<a href='loadimg.php?filename=$montagefile' target='snapshot'>\n"
				."<img src='loadimg.php?h=120&filename=$montagefile' height='120'></a><br/>";

			$clustertable .= "<ul>\n";
			$clustertable .= "<li><a target='snapshot' href='loadimg.php?filename=$montagefile'>View montage of self-organizing map</a>\n";
			$clusteravgfile = $clusterdata['path']."/".$clusterdata['avg_imagicfile'];
			$clustertable .= "<li><a href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clusteravgfile&ps=$clusterpixelsize' target='stackview'>"
				."View montage as a stack for further processing</a><br/>\n";
			$clustertable .= "</ul>\n";
		} elseif ($clusterrun['REF|ApRotKerDenSOMParamsData|rotkerdenparams']) {
			// Rot KerDen only has one cluster data
			$clusterdata = $clusterdatas[0];
			$clusterid = $clusterdata['clusterid'];
			$clustertable .= "<b>Type:</b> <i>Xmipp Rot KerDen SOM</i><br/><br/>\n";

			$montagefile = $clusterdata['path']."/"."montage.png";
			$clustertable .= "<a href='loadimg.php?filename=$montagefile' target='snapshot'>\n"
				."<img src='loadimg.php?h=120&filename=$montagefile' height='120'></a><br/>";

			$clustertable .= "<ul>\n";
			$clustertable .= "<li><a target='snapshot' href='loadimg.php?filename=$montagefile'>View montage of self-organizing map</a>\n";
			$clusteravgfile = $clusterdata['path']."/".$clusterdata['avg_imagicfile'];
			$clustertable .= "<li><a href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clusteravgfile' target='stackview'>"
				."View montage as a stack for further processing</a><br/>\n";
			$clustertable .= "</ul>\n";
		} elseif ($clusterrun['REF|ApAffinityPropagationClusterParamsData|affpropparams']) {
			// Affinity Propagation only has one cluster data
			$clusterdata = $clusterdatas[0];
			$clusterid = $clusterdata['clusterid'];
			$clustertable .= "<b>Type:</b> <i>Affinity Propagation Cluster</i><br/><br/>\n";

			$clustertable .= "<ul>\n";
			$clusteravgfile = $clusterdata['path']."/".$clusterdata['avg_imagicfile'];
			$clustertable .= "<li><a href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clusteravgfile' target='stackview'>"
				."View class averages</a><br/>\n";
			$clustertable .= "</ul>\n";
		} else {
			$clustertable .= "<b>Type:</b> <i>Unknown type of clustering</i><br/>\n";
			$clustertable .= "<ul>\n";
		}
		foreach ($clusterdatas as $clusterdata) {
			$clusterid = $clusterdata['clusterid'];
			$clusteravgfile = $clusterdata['path']."/".$clusterdata['avg_imagicfile'];
			$clustervarfile = $clusterdata['path']."/".$clusterdata['var_imagicfile'];
			if ($clusterdata['REF|ApImagicAlignAnalysisData|imagicMSArun']) {
				$clustertable .= "<li><span>"
					."<a target='stackview' href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clusteravgfile'>"
					.$clusterdata['num_classes']." Class Averages</a>&nbsp;"
					."</span></li>\n";
			} elseif ($clusterdata['REF|ApSpiderClusteringParamsData|spiderparams']) {
				$clustertable .= "<li><span>"
					."<a target='stackview' href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clusteravgfile'>"
					.$clusterdata['num_classes']." Class Averages</a>&nbsp;"
					."<a target='stackview' href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clustervarfile'>"
					."[variance]</a>&nbsp;(ID $clusterid) "
					."</span></li>\n";
			}
		}
		$clustertable .= "</ul>\n";
	}
	return $clustertable;
}

/****************************************
****************************************/
function modelsummarytable($modelid, $mini=false) {
	// initialization
	$modeltable = "";
	$expId = $_GET['expId'];
	$particle = new particledata();
	$modeldata = $particle->getInitModelInfo($modelid);
	$modelname = $modeldata['name'];
	$symdata = $particle->getSymInfo($modeldata['REF|ApSymmetryData|symmetry']);

	// start table
	$modeltable .= apdivtitle("Initial model: <span class='aptitle'>$modelname</span> (ID: $modelid)\n");
	$display_keys['id'] = "<b>".$modeldata['DEF_id']."</b> [<a href='viewmodels.php?expId=$expId'>show all</a>]";
	$display_keys['description'] = $modeldata['description'];
	$display_keys['path'] = $modeldata['path']."/".$modelname;
	$display_keys['symmetry'] = "".$symdata['symmetry'].": <i>".$symdata['description']."</i>";
	$display_keys['pixel size'] = format_angstrom_number($modeldata['pixelsize']/1e10)."/pix";
	$display_keys['box size'] = $modeldata['boxsize']." pixels";

	$modeltable .= "<table border='0'>\n";
	// get first image
	$modeltable .= "<tr><td rowspan='15'>";
	$allpngs = glob($modeldata['path']."/*.png");
	$firstimage = $allpngs[0];
	$modeltable .= "<img src='loadimg.php?filename=$firstimage&s=120' height='120'>\n";
	$modeltable .= "</td></tr>";
	// show data
	foreach($display_keys as $k=>$v) {
		$modeltable .= formatHtmlRow($k,$v);
	}
	$modeltable .= "</table>\n";
	return $modeltable;
}

/****************************************
****************************************/
function templateStackEntry($stackInfo, $hidden=False, $mini=False){
        $templateId=$stackInfo['DEF_id'];
        $expId = (int) $_GET['expId'];
	if (!$mini) {
	        if ($_POST['updateDesc'.$templateId]) {
	                updateDescription('ApTemplateImageData', $templateId, $_POST['newdescription'.$templateId]);
	                $stackInfo['description']=$_POST['newdescription'.$templateId];
	        }
	}
        $filename = $stackInfo['path'] ."/".$stackInfo['templatename'];

        // create the image template table
        $j = "Template ID: $templateId";
	
	if (!$mini) {
	        if ($hidden) $j.= " <input class='edit' type='submit' name='unhideTemplate".$templateId."' value='unhide'>";
        	else $j.= " <input class='edit' type='submit' name='hideTemplate".$templateId."' value='hide'>";
	}
        $templatetable.= apdivtitle($j);
        $templatetable.="<table border='0' cellpadding='5'>\n";
        $templatetable.="<tr><td valign='top'>\n";
        $templatetable.="<img src='loadimg.php?filename=$filename&s=100' width='100'></td>\n";
        $templatetable.="<td>\n";
        $templatetable.="<B>Pixel Size:</B>  $stackInfo[apix]<br>\n";
        $templatetable.="<B>Box Size: </B> $stackInfo[boxsize]<br>\n";
        $templatetable.="<B>File: </B>";
        $templatetable.=$filename;
        $templatetable.="<br />\n";
        $templatetable.="<b>Description: </b>";

        # add edit button to description if logged in
	if (!$mini) {
        	$descDiv = ($_SESSION['username']) ? editButton($templateId,$stackInfo['description']) : $stackInfo['description'];
        	$templatetable.=$descDiv;
	}
	else $templatetable.=$stackInfo['description']."<br>";
        $templatetable.="<a target=tsview href='viewstack.php?file=$filename&expId=$expId&templateStackId=$templateId'><b>View Template Stack</b></a>";
        $templatetable.="</td></tr>\n";
        $templatetable.="</table>\n";
        return $templatetable;
}


?>
