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

$expId = (int) $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
if ($_GET['showHidden']) $formAction.="&showHidden=True";

$javascript = editTextJava();

processing_header("Template Summary", "Template Summary", $javascript,False);

if ($expId && is_int($expId)){
	$projectId = getProjectId();
}

if (is_int($projectId)) {
	$particle=new particleData;
	$templateData=$particle->getTemplatesFromProject($projectId,True);
}

// extract template info
if ($templateData) {
	// separate hidden from shown;
	$shown = array();
	$hidden = array();
	foreach($templateData as $templateinfo) { 
		if (is_array($templateinfo)) {
			$templateId=$templateinfo['DEF_id'];
			// first update hide value
			if ($_POST['hideTemplate'.$templateId]) {
				$particle->updateHide('ApTemplateImageData',$templateId,1);
				$templateinfo['hidden']=1;
			}
			elseif ($_POST['unhideTemplate'.$templateId]) {
				$particle->updateHide('ApTemplateImageData',$templateId,0);
				$templateinfo['hidden']='';
			}
			if ($templateinfo['hidden']==1) $hidden[]=$templateinfo;
			else $shown[]=$templateinfo;
		}
	}
	$templatetable="<form name='templateform' method='post' action='$formAction'>\n";
	foreach ($shown as $template) $templatetable.=templateEntry($template);
	// show hidden templates
	if ($_GET['showHidden'] && $hidden) {
		if ($shown) $templatetable.="<hr />\n";
		$templatetable.="<b>Hidden Templates</b> ";
		$templatetable.="<a href='".$_SERVER['PHP_SELF']."?expId=$expId'>[hide]</a><br />\n";
		foreach ($hidden as $template) $templatetable.= templateEntry($template,True);
	}
	$templatetable.="</form>\n";
}

if ($hidden && !$_GET['showHidden']) echo "<a href='".$formAction."&showHidden=True'>[Show Hidden Templates]</a><br />\n";

if ($shown || $hidden) echo $templatetable;
else echo "<B>Project does not contain any templates.</B>\n";
processing_footer();
exit;

function templateEntry($templateinfo, $hidden=False){
	$templateId=$templateinfo['DEF_id'];
	$expId = (int) $_GET['expId'];
	if ($_POST['updateDesc'.$templateId]) {
		updateDescription('ApTemplateImageData', $templateId, $_POST['newdescription'.$templateId]);
		$templateinfo['description']=$_POST['newdescription'.$templateId];
	}
	$filename = $templateinfo['path'] ."/".$templateinfo['templatename'];
	// create the image template table
	$j = "Template ID: $templateId";
	if ($hidden) $j.= " <input class='edit' type='submit' name='unhideTemplate".$templateId."' value='unhide'>";
	else $j.= " <input class='edit' type='submit' name='hideTemplate".$templateId."' value='hide'>";
	$templatetable.= apdivtitle($j);
	$templatetable.="<table border='0' cellpadding='5'>\n";
	$templatetable.="<tr><td valign='top'>\n";
	$templatetable.="<img src='loadimg.php?filename=$filename&s=100' width='100'></td>\n";
	$templatetable.="<td>\n";
	$templatetable.="<B>Diameter:</B>  $templateinfo[diam]<br>\n";
	$templatetable.="<B>Pixel Size:</B>  $templateinfo[apix]<br>\n";
	$templatetable.="<B>File:</B><br>";
	$templatetable.=$filename;
	$templatetable.="<br />\n";
	$templatetable.="<b>Description:</b><br />";

	# add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($templateId,$templateinfo['description']) : $templateinfo['description'];
	$templatetable.=$descDiv;
	$templatetable.="</td></tr>\n";
	$templatetable.="</table>\n";
	return $templatetable;
}
?>
