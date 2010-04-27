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
require "inc/summarytables.inc";

$expId = (int) $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
if ($_GET['showHidden']) $formAction.="&showHidden=True";

$javascript = editTextJava();

processing_header("Template Stack Summary", "Template Stack Summary Page", $javascript,False);

if ($expId && is_int($expId)){
	$projectId = getProjectId();
}

if (is_int($projectId)) {
	$particle=new particleData;
	if ($_GET['type'] == 'forward') $templateStackData=$particle->getTemplateStacksFromProject($projectId,True,"forward");
	elseif ($_GET['type'] == 'clsavg') $templateStackData=$particle->getTemplateStacksFromProject($projectId,True,"clsavg");
}


// first give the option of uploading a new template stack
echo "<a href='uploadTemplateStack.php?expId=$expId'><P><B>Upload a New Template Stack</B></P></a><br>\n";


// extract template info
if ($templateStackData) {
	// separate hidden from shown;
	$shown = array();
	$hidden = array();
	foreach($templateStackData as $stackInfo) { 
		if (is_array($stackInfo)) {
			$templateId=$stackInfo['DEF_id'];
			// first update hide value
			if ($_POST['hideTemplate'.$templateId]) {
				$particle->updateHide('ApTemplateImageData',$templateId,1);
				$stackInfo['hidden']=1;
			}
			elseif ($_POST['unhideTemplate'.$templateId]) {
				$particle->updateHide('ApTemplateImageData',$templateId,0);
				$stackInfo['hidden']='';
			}
			if ($stackInfo['hidden']==1) $hidden[]=$stackInfo;
			else $shown[]=$stackInfo;
		}
	}
	$templatetable="<form name='templateform' method='post' action='$formAction'>\n";
	foreach ($shown as $template) $templatetable.=templateStackEntry($template);
	// show hidden templates
	if ($_GET['showHidden'] && $hidden) {
		if ($shown) $templatetable.="<hr />\n";
		$templatetable.="<b>Hidden Templates</b> ";
		$templatetable.="<a href='".$_SERVER['PHP_SELF']."?expId=$expId'>[hide]</a><br />\n";
		foreach ($hidden as $template) $templatetable.= templateStackEntry($template,True);
	}
	$templatetable.="</form>\n";
}

if ($hidden && !$_GET['showHidden']) echo "<a href='".$formAction."&showHidden=True'>[Show Hidden Templates]</a><br />\n";

if ($shown || $hidden) echo $templatetable;
else echo "<B>Project does not contain any template stacks.</B>\n";
processing_footer();
exit;

?>
