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
	$expId = $_GET['expId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	$stacktable .= "<form name='stackform' method='post' action='$formAction'>\n";

	if ($_POST['updateDesc'.$stackid])
		updateDescription('ApStackData', $stackid, $_POST['newdescription'.$stackid]);

	if ($_POST['hideStack'.$stackid]) {
		$particle->updateHide('ApStackData',$stackid,1);
		$stack['hidden']=1;
	} elseif ($_POST['unhideStack'.$stackid]) {
		$particle->updateHide('ApStackData',$stackid,0);
		$stack['hidden']='';
	}

	// get list of stack parameters from database
	$stackdata = $particle->getStackParams($stackid);

	$numpart = $particle->getNumStackParticles($stackid);
	if ($numpart == 0) return;

	$j = "Stack Info: <a class='aptitle' href='stackreport.php?expId=$expId&sId=$stackid'>"
		.$stackdata['shownstackname']."</a> (ID: $stackid)";
	if ($stackdata['hidden'] == 1) {
		$j.= " <font color='#cc0000'>HIDDEN</font>";
		$j.= " <input class='edit' type='submit' name='unhideStack".$stackid."' value='unhide'>";
		$display_keys['hidden']="<font color='#cc0000'>HIDDEN</font>";
	} else $j.= " <input class='edit' type='submit' name='hideStack".$stackid."' value='hide'>";

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
		$stacktable.= "<td rowspan='30' align='center' valign='top'>";
		$stacktable.= "<img src='loadimg.php?filename=$stackavg&s=150' height='150'><br/>\n";
		$stacktable.= "<i>averaged stack image</i>\n";
		if (!$centered) $stacktable.= "<br /><a href='centerStack.php?expId=$expId&sId=$stackid'>[Center Particles]</a>\n";
		$stacktable.= "<br /><a href='subStack.php?expId=$expId&sId=$stackid'>[Create Substack]</a>\n";
		$stacktable.= "</td>\n";
		if ($centered && file_exists($badstackavg)) {
			$stacktable.= "<td rowspan='15' align='center' valign='top'>";
			$stacktable.= "<img src='loadimg.php?filename=$badstackavg&s=150' height='150'><br/>\n";
			$stacktable.= "<i>averaged bad stack</i><br/>\n";
			$stacktable.= "</td>\n";
		} elseif (file_exists($montage)) {
			$stacktable.= "<td rowspan='15' align='center' valign='top'>";
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
	if (substr($stackdata['name'], -4) == ".hed")
		$stackimgfile = $stackdata['path']."/".substr($stackdata['name'], 0, -4).".img";
	else
		$stackimgfile = $stackdata['path']."/".$stackdata['name'];
	if (filesize($stackimgfile) > 1073741824)
		$display_keys['file size'] = sprintf("%.2f GB", filesize($stackimgfile)/1073741824);
	else
		$display_keys['file size'] = sprintf("%.1f MB", filesize($stackimgfile)/1048576);

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
	$stacktable.= "</form><p>\n";
	return $stacktable;
}

?>
