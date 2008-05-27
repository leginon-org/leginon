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
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";
require "inc/leginon.inc";
require "inc/project.inc";

$expId = (int) $_GET[expId];

processing_header("Template Summary", "Template Summary", "",False);

if ($expId && is_int($expId)){
	$projectId = (int) getProjectFromExpId($expId);
	//echo "project id = $projectId<BR/>";
}

// if user wants to use templates from another project
if($_POST['projectId']) $projectId=$_POST['projectId'];

//$projects=getProjectList();

if (is_int($projectId)) {
	$particle=new particleData;
	$templateData=$particle->getTemplatesFromProject($projectId);
}


echo"<BR/><INPUT TYPE='hidden' NAME='projectId' value='$projectId'>\n";

// extract template info
if ($templateData) {
	$i=1;
	$templatetable="<TABLE CLASS='tableborder' BORDER='1' CELLPADDING='5' WIDTH='600'>\n";
	$templatetable.="<style type='text/css'><!-- input { font-size: 14px; } --></style>";
	$numtemplates=count($templateData);

	foreach($templateData as $templateinfo) { 
		if (is_array($templateinfo)) {
			$filename = $templateinfo['path'] ."/".$templateinfo['templatename'];
			// create the image template table
			$templatetable.="<TR><TD>\n";
			$templatetable.="<IMG SRC='loadimg.php?filename=$filename&rescale=True' WIDTH='200'></TD>\n";
			$templatetable.="<TD>\n";
			$templatetable.="<BR/>\n";
			//$templatetable.=print_r($templateinfo);
			$templatetable.="<B>Template ID:</B>  $templateinfo[DEF_id]<BR/>\n";
			$templatetable.="<B>Diameter:</B>  $templateinfo[diam]<BR/>\n";
			$templatetable.="<B>Pixel Size:</B>  $templateinfo[apix]<BR/>\n";
			$templatetable.="<B>File:</B><BR/>";
			$templatetable.="<TABLE CLASS='tableborder' BORDER='1'><TR><TD CLASS='tablebg'>\n";
			$templatetable.=$filename;
			$templatetable.="</TD></TR></TABLE>\n";
			$templatetable.="<B>Description:</B><BR/>";
			$templatetable.="<TABLE CLASS='tableborder' BORDER='1'><TR><TD CLASS='tablebg'>\n";
			$templatetable.=$templateinfo[description];
			$templatetable.="</TD></TR></TABLE>\n";
			$templatetable.="</TD></TR>\n";
			$i++;
		}
	}
	$templatetable.="</TABLE>\n";
}

if ($templatetable) {
	echo"
  <CENTER>
  </CENTER>\n
  $templatetable
  <CENTER>
  <INPUT TYPE='hidden' NAME='numtemplates' value='$numtemplates'>
  </CENTER>\n";
} else echo "<B>Project does not contain any templates.</B>\n";


