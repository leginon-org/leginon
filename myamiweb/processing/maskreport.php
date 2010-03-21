<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/particledata.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/project.inc";

// --- Set  experimentId
$lastId = $leginondata->getLastSessionId();
$expId = $_GET['expId'];
$sessioninfo = $leginondata->getSessionInfo($expId);
$title = $sessioninfo[Name];

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();
if($projectdb) {
	$currentproject = $projectdata->getProjectFromSession($sessioninfo['Name']);
	$proj_link= '<a class="header" target="project" href="'.PROJECT_URL."getproject.php?pId=".$currentproject['projectId'].'">'.$currentproject['name'].'</a>';
}

$javascript = "
<STYLE type='text/css'>
DIV.comment_section { text-align: justify; 
		margin-top: 5px;
		font-size: 10pt}
DIV.comment_subsection { text-indent: 2em;
		font-size: 10pt;
		margin-top: 5px ;
		margin-bottom: 15px ;
	}
</STYLE>
<script>
function init() {
	this.focus();
}
</script>\n";

processing_header('Mask Creation Results','Mask Creation Results');

echo"<table border='0' cellpadding=10>
<TR>
  <td>\n";

$sessionDescr=$sessioninfo['Purpose'];
echo "<table>";
echo "<TR><td><B>Project:</B></TD><td>$proj_link</TD></tr>\n";
echo "<TR><td><B>Session:</B></TD><td><A CLASS='header' target='project' href='3wviewer.php?expId=$expId'>$sessionDescr</A></TD></tr>\n";
echo "</table>";
echo "<HR>\n";
/*
$inspectcheck=($_POST['onlyinspected']=='on') ? 'CHECKED' : '';
echo"<FORM NAME='prtl' method='POST' action='$_SERVER[REQUEST_URI]'>
     <INPUT TYPE='CHECKBOX' name='onlyinspected' $inspectcheck onclick='javascript:document.prtl.submit()'>Don't use regions from discarded images<br>
     <INPUT CLASS='field' NAME='mselex' TYPE='text' size='5' VALUE='$mselexval'>Minimum correlation value
     </form>\n";
*/
$sessionId=$expId;
$particle = new particledata();
$numinspected=$particle->getNumAssessedImages($sessionId);
echo"Inpected images: $numinspected\n";
if ($particle->hasMaskMakerData($sessionId)) {
	$display_keys = array ( 'totregions', 'numimgs', 'areamean', 'Imean', 'Istddev', 'img');
	$maskruns=$particle->getMaskMakerRunIds($sessionId);
	echo $particle->displayMaskRegionStats($expId,$maskruns, $display_keys, $inspectcheck);
}
else {
        echo "no Mask information available";
}


echo "</td>
</tr>
</table>\n";

processing_footer();

?>
