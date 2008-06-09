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
	if ($_POST['updateDesc'.$stackid])
		updateDescription('ApStackData', $stackid, $_POST['newdescription'.$stackid]);
	$s=$particle->getStackParams($stackid);
	# get list of stack parameters from database
	$nump=commafy($particle->getNumStackParticles($stackid));
	if ($nump == 0) return;
	$j = "Stack: <a class='aptitle' href='stackreport.php?expId=$expId&sId=$stackid'>".$s['shownstackname']."</a> (ID: $stackid)";
	if ($hidden) $j.= " <input class='edit' type='submit' name='unhideStack".$stackid."' value='unhide'>";
	else $j.= " <input class='edit' type='submit' name='hideStack".$stackid."' value='hide'>";
	$stacktable.= apdivtitle($j);

	$stacktable.= "<table border='0' width='600'>\n";
	$stackavg = $s['path']."/average.mrc";
	if (file_exists($stackavg)) {
		$stacktable.= "<tr><td rowspan='15' align='center'>";
		$stacktable.= "<img src='loadimg.php?filename=$stackavg' height='150'><br/>\n";
		$stacktable.= "<i>averaged stack image</i><br/>\n";
		$stacktable.= "</td></tr>\n\n";
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

	$display_keys['# prtls']=$nump;
	$stackfile = $s['path']."/".$s['name'];
	$display_keys['path']=$s['path'];
	$display_keys['name']="<a target='stackview' HREF='viewstack.php?file=$stackfile&expId=$expId&stackId=$stackid'>".$s['name']."</A>";
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
