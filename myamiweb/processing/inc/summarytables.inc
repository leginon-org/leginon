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

function stacksummarytable($stackid) {
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

	$j = "Stack Info: <a class='aptitle' href='stackreport.php?expId=$expId&sId=$stackid'>"
		.$stackdata['shownstackname']."</a> (ID: $stackid)\n";
	if ($stackdata['hidden'] == 1) {
		$j.= " <font color='#cc0000'>HIDDEN</font>\n";
		$j.= " <input class='edit' type='submit' name='unhideStack".$stackid."' value='unhide'>\n";
		$display_keys['hidden']="<font color='#cc0000'>HIDDEN</font>";
	} else $j.= " <input class='edit' type='submit' name='hideStack".$stackid."' value='hide'>\n";

	$stacktable.= apdivtitle($j);

	// if particles were centered, set centered variable
	if ($stackdata['centered'] == 1) {
		$centered = True;
	}

	$stacktable.= "<table border='0' width='700'>\n";
	$stackavg = $stackdata['path']."/average.mrc";
	$badstackavg = $stackdata['path']."/badaverage.mrc";
	$montage = $stackdata['path']."/montage".$stackdata['DEF_id'].".png";
	if (file_exists($stackavg)) {
		$stacktable.= "<tr>\n";
		$stacktable.= "<td  align='left' rowspan='30' align='center' valign='top'>";
		$stacktable.= "<img src='loadimg.php?filename=$stackavg&s=150' height='150'><br/>\n";
		$stacktable.= "<i>averaged stack image</i>\n";
		if (!$centered) $stacktable.= "<br /><a href='centerStack.php?expId=$expId&sId=$stackid'>[Center Particles]</a>\n";
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
			$sessiondata = $particle->getSessionData($stackdata[$i]['sessionid']);
			$display_keys['session id'].="<a href='index.php?expId=".$stackdata['sessionid']."'>"
				.$sessiondata['name']."</a>&nbsp;\n";
		}
	}

	// add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($stackid,$stackdata['description']) : $stackdata['description'];
	$display_keys['description']=$descDiv;

	// Show number of particles
	if ($centered) {
		$oldnumpart = $particle->getNumStackParticles($stackdata['REF|ApStackData|oldstack']);
		$display_keys['# particles']= commafy($numpart)." (".commafy($oldnumpart-$numpart)." bad)";
	} else 
		$display_keys['# particles']=commafy($numpart);

	// Get filesize
	$display_keys['file size'] = getStackSize($stackdata);

	$stackfile = $stackdata['path']."/".$stackdata['name'];
	$display_keys['path']=$stackdata['path'];
	$display_keys['stack file']="<a target='stackview' HREF='viewstack.php?file=$stackfile&expId=$expId&stackId=$stackid'>"
		.$stackdata['name']."</A>";
	# if stack was created by cenalignint, also view avg & bad stacks
	if ($centered) {
		$display_keys['iterative avgs']="<a target='stackview' HREF='viewstack.php?file=".$stackdata['path']
			."/avg.hed&expId=$expId'>avg.hed</A>";
		$display_keys['stack file'].=" &nbsp;(<a target='stackview' HREF='viewstack.php?file=".$stackdata['path']
			."/bad.hed&expId=$expId'>bad.hed</A>)";
	}
	$display_keys['box size']=$boxsz;
	$display_keys['pixel size']=$apix;

	# use values from first of the combined run, if any for now	
	$pflip = ($stackdata['phaseFlipped']==1) ? "Yes" : "No";
	if ($stackdata['aceCutoff']) $pflip.=" (ACE > $stackdata[aceCutoff])";
	
	$display_keys['phase flipped']=$pflip;
	if ($stackdata['correlationMin']) $display_keys['correlation min']=$stackdata['correlationMin'];
	if ($stackdata['correlationMax']) $display_keys['correlation max']=$stackdata['correlationMax'];
	if ($stackdata['minDefocus']) $display_keys['min defocus']=$stackdata['minDefocus'];
	if ($stackdata['maxDefocus']) $display_keys['max defocus']=$stackdata['maxDefocus'];
	$display_keys['density']=($stackdata['inverted']==1) ? 'Inverted':'Not inverted';
	$display_keys['normalization']=($stackdata['normalized']==1) ? 'On':'Off';
	//$display_keys['file type']=$stackdata['fileType'];
	foreach($display_keys as $k=>$v) {
	        $stacktable.= formatHtmlRow($k,$v);
	}
	$stacktable.= "</table>\n";
	$stacktable.= "<p>\n";
	return $stacktable;
}

function ministacksummarytable($stackid) {
	$particle = new particledata();
	$stackdata = $particle->getStackParams($stackid);

	$numpart = $particle->getNumStackParticles($stackid);
	if ($numpart == 0) return;

	$j = "Stack Info: <a class='aptitle' href='stackreport.php?expId=$expId&sId=$stackid'>"
		.$stackdata['shownstackname']."</a> (ID: $stackid)\n";

	$stacktable.= apdivtitle($j);

	// if particles were centered, set centered variable
	if ($stackdata['centered'] == 1) {
		$centered = True;
	}

	$stacktable.= "<table border='0'>\n";
	$stackavg = $stackdata['path']."/average.mrc";
	$badstackavg = $stackdata['path']."/badaverage.mrc";
	$montage = $stackdata['path']."/montage".$stackdata['DEF_id'].".png";
	if (file_exists($stackavg)) {
		$stacktable.= "<tr >\n";
		$stacktable.= "<td align='left' rowspan='30' align='center' valign='top'>";
		$stacktable.= "<img src='loadimg.php?filename=$stackavg&s=80' height='80'><br/>\n";
		$stacktable.= "<i>average</i>\n";
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
			$sessiondata = $particle->getSessionData($stackdata[$i]['sessionid']);
			$display_keys['session id'].="<a href='index.php?expId=".$stackdata[$i]['sessionid']."'>"
				.$sessiondata['name']."</a>&nbsp;\n";
		}
	}

	// add edit button to description if logged in
	$display_keys['description']="<font size=-2>".$stackdata['description']."</font>\n";

	// Show size
	$display_keys['size']=commafy($numpart)." parts / ".getStackSize($stackdata);

	$stackfile = $stackdata['path']."/".$stackdata['name'];
	$display_keys['path']="<font size=-2>".$stackdata['path']."</font>\n";;
	$display_keys['stack file']="<a target='stackview' HREF='viewstack.php?file=$stackfile&expId=$expId&stackId=$stackid'>"
		.$stackdata['name']."</A>";
	# if stack was created by cenalignint, also view avg & bad stacks
	$display_keys['pixel / box size']=$boxsz." / ".$apix;

	//$display_keys['file type']=$stackdata['fileType'];
	foreach($display_keys as $k=>$v) {
	        $stacktable.= formatHtmlRow($k,$v);
	}
	$stacktable.= "</table>\n";
	$stacktable.= "<p>\n";
	return $stacktable;
}



function alignstacksummarytable($alignstackid) {
	$particle = new particledata();
	$stackdata = $particle->getAlignStackParams($alignstackid);
	//echo print_r($stackdata)."<br/>\n";

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
	if ($numpart == 0) return;

	$j = "Align Stack Info: <a class='aptitle' href='alignreport.php?expId=$expId&sId=$alignstackid'>"
		.$stackdata['runname']."</a> (ID: $alignstackid)\n";
	if ($stackdata['hidden'] == 1) {
		$j.= " <font color='#cc0000'>HIDDEN</font>\n";
		$j.= " <input class='edit' type='submit' name='unhideStack".$stackid."' value='unhide'>\n";
		$display_keys['hidden']="<font color='#cc0000'>HIDDEN</font>";
	} else $j.= " <input class='edit' type='submit' name='hideStack".$stackid."' value='hide'>\n";

	$stacktable.= apdivtitle($j);
	//echo $j."<br/>\n";

	$stacktable.= "<table border='0' width='700'>\n";
	$stackavg = $stackdata['path']."/average.mrc";
	if (file_exists($stackavg)) {
		$stacktable.= "<tr>\n";
		$stacktable.= "<td rowspan='30' align='center' valign='top'>";
		$stacktable.= "<img src='loadimg.php?filename=$stackavg&s=150' height='150'><br/>\n";
		$stacktable.= "<i>averaged stack image</i>\n";
		$stacktable.= "</td>\n";
		$stacktable.= "</tr>\n\n";
	} #endif

	// add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($stackid,$stackdata['description']) : $stackdata['description'];

	$display_keys['date time'] = $stackdata['DEF_timestamp'];
	$display_keys['description']=$descDiv;

	// Show number of particles
	$display_keys['# particles']=commafy($numpart);

	// Get filesize
	if (substr($stackdata['imagicfile'], -4) == ".hed")
		$stackimgfile = $stackdata['path']."/".substr($stackdata['imagicfile'], 0, -4).".img";
	if (filesize($stackimgfile) > 1073741824)
		$display_keys['file size'] = sprintf("%.2f GB", filesize($stackimgfile)/1073741824);
	else
		$display_keys['file size'] = sprintf("%.1f MB", filesize($stackimgfile)/1048576);

	$stackfile = $stackdata['path']."/".$stackdata['imagicfile'];
	$display_keys['path']=$stackdata['path'];
	$display_keys['stack file']="<a target='stackview' HREF='viewstack.php?file=$stackfile&expId=$expId&stackId=$stackid'>"
		.$stackdata['imagicfile']."</A>";
	// get box size
	$display_keys['box size']=$stackdata['boxsize']." pixels";
	// get pixel size of stack
	$display_keys['pixel size']=round($stackdata['pixelsize'],2)." &Aring;/pixel";

	//$display_keys['file type']=$stackdata['fileType'];
	foreach($display_keys as $k=>$v) {
	        $stacktable.= formatHtmlRow($k,$v);
	}
	$stacktable.= "</table>\n";
	$stacktable.= "<p>\n";
	return $stacktable;
}



?>
