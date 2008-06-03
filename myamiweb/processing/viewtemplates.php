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

$javascript = editTextJava();

processing_header("Template Summary", "Template Summary", $javascript,False);

if ($expId && is_int($expId)){
	$projectId = (int) getProjectFromExpId($expId);
}

if (is_int($projectId)) {
	$particle=new particleData;
	$templateData=$particle->getTemplatesFromProject($projectId);
}


// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

echo"<INPUT TYPE='hidden' NAME='projectId' value='$projectId'>\n";

// extract template info
if ($templateData) {
	$i=1;
	$templatetable="<TABLE class='tableborder' BORDER='1' CELLPADDING='5' WIDTH='600'>\n";
	$numtemplates=count($templateData);

	foreach($templateData as $templateinfo) { 
		if (is_array($templateinfo)) {
			$templateId=$templateinfo['DEF_id'];
			if ($_POST['updateDesc'.$templateId]) {
				updateDescription('ApTemplateImageData', $templateId, $_POST['newdescription'.$templateId]);
				$templateinfo['description']=$_POST['newdescription'.$templateId];
			}
			$filename = $templateinfo['path'] ."/".$templateinfo['templatename'];
			// create the image template table
			$templatetable.="<TR><TD>\n";
			$templatetable.="<IMG SRC='loadimg.php?filename=$filename&rescale=True' WIDTH='150'></TD>\n";
			$templatetable.="<TD>\n";
			$templatetable.="<BR/>\n";
			//$templatetable.=print_r($templateinfo);
			$templatetable.="<B>Template ID:</B>  $templateId<BR/>\n";
			$templatetable.="<B>Diameter:</B>  $templateinfo[diam]<BR/>\n";
			$templatetable.="<B>Pixel Size:</B>  $templateinfo[apix]<BR/>\n";
			//$templatetable.=openRoundBorder();
			$templatetable.="<B>File:</B><BR/>";
			$templatetable.=$filename;
			$templatetable.="<br />\n";
			$templatetable.="<b>Description:</b><br />";

			# add edit button to description if logged in
			$descDiv = ($_SESSION['username']) ? editButton($templateId,$templateinfo['description']) : $templateinfo['description'];
			$templatetable.=$descDiv;
			//$templatetable.=closeRoundBorder();
			$templatetable.="</TD></TR>\n";
			$i++;
		}
	}
	$templatetable.="</TABLE>\n";
	$templatetable.="</form>\n";
}

if ($templatetable) {
	echo"
  <CENTER>
  </CENTER>\n
  $templatetable
  <CENTER>
  <INPUT TYPE='hidden' NAME='numtemplates' value='$numtemplates'>
  </CENTER>\n";
} 
else echo "<B>Project does not contain any templates.</B>\n";
processing_footer();

?>