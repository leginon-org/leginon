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
require "inc/processing.inc";
  
$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
if ($_GET['showHidden']) $formAction.="&showHidden=True";

$javascript.= editTextJava();

processing_header("Stack Report","Stack Summary Page", $javascript,False);

// --- Get Stack Data --- //
$particle = new particledata();

// find each stack entry in database
$stackIds = $particle->getStackIds($expId, True);

if ($stackIds) {
	// separate hidden from shown;
	$shown = array();
	$hidden = array();
	foreach ($stackIds as $stack) {
		if (is_array($stack)) {
			$stackId=$stack['DEF_id'];
			// first update hide value
			if ($_POST['hideStack'.$stackId]) {
				$particle->updateHide('ApStackData',$stackId,1);
				$stack['hidden']=1;
			}
			elseif ($_POST['unhideStack'.$stackId]) {
				$particle->updateHide('ApStackData',$stackId,0);
				$stack['hidden']='';
			}
			if ($stack['hidden']==1) $hidden[]=$stack;
			else $shown[]=$stack;
		}
	}
	echo "<form name='stackform' method='post' action='$formAction'>\n";
	foreach ($shown as $st) $stacktable.=stackEntry($st, $particle);
	// show hidden stacks
	if ($_GET['showHidden'] && $hidden) {
		if ($shown) $stacktable.="<hr />\n";
		$stacktable.="<b>Hidden Stacks</b> ";
		$stacktable.="<a href='".$_SERVER['PHP_SELF']."?expId=$expId'>[hide]</a><br />\n";
		foreach ($hidden as $st) $stacktable.= stackEntry($st,$particle,True);
	}
	$stacktable.="</form>\n";
}

if ($hidden && !$_GET['showHidden']) echo "<a href='".$formAction."&showHidden=True'>[Show Hidden Stacks]</a><br />\n";

if ($shown || $hidden) echo $stacktable;
else echo "<B>Session does not contain any stacks.</B>\n";
processing_footer();
exit;

function stackEntry($stack, $particle, $hidden=False) {
	$stackid=$stack['stackid'];
	$expId=$_GET['expId'];
	if ($_POST['updateDesc'.$stackid])
		updateDescription('ApStackData', $stackid, $_POST['newdescription'.$stackid]);
	$s=$particle->getStackParams($stackid);
	# get list of stack parameters from database
	$nump=$particle->getNumStackParticles($stackid);
	if ($nump == 0) return;
	$j = "Stack: <a class='aptitle' href='stackreport.php?expId=$expId&sId=$stackid'>".$s['shownstackname']."</a> (ID: $stackid)";
	if ($hidden) $j.= " <input class='edit' type='submit' name='unhideStack".$stackid."' value='unhide'>";
	else $j.= " <input class='edit' type='submit' name='hideStack".$stackid."' value='hide'>";

	// if particles were centered, find out info about original stack
	if ($s['name'] == 'ali.hed' || $s['name'] == 'ali.img') {
		$centered=True;
		$oldnump=$particle->getNumStackParticles($s[0]['stackId']);
	}

	$stacktable.= apdivtitle($j);

	$stacktable.= "<table border='0' width='600'>\n";
	$stackavg = $s['path']."/average.mrc";
	$badstackavg = $s['path']."/badaverage.mrc";
	$montage = $s['path']."/montage".$s['DEF_id'].".png";
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
		}
		if (!$centered && file_exists($montage)) {
			$stacktable.= "<td rowspan='15' align='center' valign='top'>";
			$stacktable.= "<a href='loadimg.php?filename=$montage'>\n";
			$stacktable.= "<img border=0 src='loadimg.php?filename=$montage&s=150' height='150'></a><br/>\n";
			$stacktable.= "<i>mean/stdev montage</i><br/>\n";
			$stacktable.= "<a href='subStack.php?expId=$expId&sId=$stackid&mean=1'>[Filter by Mean/Stdev]</a>\n";
			$stacktable.= "</td>\n";
		}
		$stacktable.= "</tr>\n\n";
	} #endif
	# get pixel size of stack
	$mpix=($particle->getStackPixelSizeFromStackId($stackid));
	$apix=format_angstrom_number($mpix)."/pixel";

	# get box size
	$boxsz=($s['bin']) ? $s['boxSize']/$s['bin'] : $s['boxSize'];
	$boxsz.=" pixels";
	
	# add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($stackid,$s['description']) : $s['description'];

	$display_keys['description']=$descDiv;

	if ($centered) {
		$display_keys['# good prtls']=commafy($nump);
		$display_keys['# bad prtls']=commafy($oldnump-$nump);
	}
	else $display_keys['# prtls']=commafy($nump);

	if (substr($s['name'], -4) == ".hed")
		$stackimgfile = $s['path']."/".substr($s['name'], 0, -4).".img";
	else
		$stackimgfile = $s['path']."/".$s['name'];
	$display_keys['file size'] = sprintf("%.2f GB", filesize($stackimgfile)/1073741824);

	$stackfile = $s['path']."/".$s['name'];
	$display_keys['path']=$s['path'];
	$display_keys['name']="<a target='stackview' HREF='viewstack.php?file=$stackfile&expId=$expId&stackId=$stackid'>".$s['name']."</A>";
	# if stack was created by cenalignint, also view avg & bad stacks
	if ($centered) {
		$display_keys['iterative avgs']="<a target='stackview' HREF='viewstack.php?file=".$s['path']."/avg.hed&expId=$expId'>avg.hed</A>";
		$display_keys['bad particles']="<a target='stackview' HREF='viewstack.php?file=".$s['path']."/bad.hed&expId=$expId'>bad.hed</A>";
	}
	$display_keys['box size']=$boxsz;
	$display_keys['pixel size']=$apix;

	# use values from first of the combined run, if any for now	
	$s = $s[0];
	$pflip = ($s['phaseFlipped']==1) ? "Yes" : "No";
	if ($s['aceCutoff']) $pflip.=" (ACE > $s[aceCutoff])";
	
	$display_keys['phase flipped']=$pflip;
	if ($s['correlationMin']) $display_keys['correlation min']=$s['correlationMin'];
	if ($s['correlationMax']) $display_keys['correlation max']=$s['correlationMax'];
	if ($s['minDefocus']) $display_keys['min defocus']=$s['minDefocus'];
	if ($s['maxDefocus']) $display_keys['max defocus']=$s['maxDefocus'];
	$display_keys['density']=($s['inverted']==1) ? 'light on dark background':'dark on light background';
	$display_keys['normalization']=($s['normalized']==1) ? 'On':'Off';
	$display_keys['file type']=$s['fileType'];
	foreach($display_keys as $k=>$v) {
	        $stacktable.= formatHtmlRow($k,$v);
	}
	$stacktable.= "</table>\n";
	$stacktable.= "<p>\n";
	return $stacktable;
}
?>
