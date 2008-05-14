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
require "inc/viewer.inc";
require "inc/processing.inc";
  
// check if coming directly from a session
$expId = $_GET['expId'];
$url = urlencode($_SERVER['REQUEST_URI']);
if ($expId) {
        $sessionId=$expId;
        $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
}
else {
        $sessionId=$_POST['sessionId'];
        $formAction=$_SERVER['PHP_SELF'];
}
$projectId=$_POST['projectId'];

$javascript = "<script src='../js/viewer.js'></script>\n";

// javascript for hiding/showing edit text & form
$javascript = "<script language='javascript' type='text/javascript'>\n";
$javascript.= "function hideEditForm(stackid) {\n";
$javascript.= "  var descText='descText'+stackid;\n";
$javascript.= "  var descForm='descForm'+stackid;\n";
$javascript.= "  if (document.getElementById) { // DOM3 = IE5, NS6\n";
$javascript.= "    document.getElementById(descText).style.visibility = 'hidden';\n"; 
$javascript.= "    document.getElementById(descForm).style.visibility = 'visible';\n"; 
$javascript.= "  }\n"; 
$javascript.= "  else {\n"; 
$javascript.= "    if (document.layers) { // Netscape 4\n"; 
$javascript.= "      document.descText.visibility = 'hidden';\n"; 
$javascript.= "      document.descForm.visibility = 'visible';\n"; 
$javascript.= "    }\n"; 
$javascript.= "    else { // IE 4\n"; 
$javascript.= "      document.all.descText.style.visibility = 'hidden';\n"; 
$javascript.= "      document.all.descForm.style.visibility = 'visible';\n"; 
$javascript.= "    }\n"; 
$javascript.= "  }\n"; 
$javascript.= "}\n";
$javascript.= "</script>\n";

writeTop("Stack Report","Stack Summary Page", $javascript,False);

echo"<form name='viewerform' method='POST' ACTION='$formAction'>
<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
echo "</FORM>\n";

// --- Get Stack Data --- //
$particle = new particledata();

// edit description form
echo "<form name='stackform' method='post' action='$formAction'>\n";

# find each stack entry in database
$stackIds = $particle->getStackIds($sessionId);
foreach ($stackIds as $row) {
	$stackid=$row['stackid'];
	$s=$particle->getStackParams($stackid);
	# get list of stack parameters from database
	$nump=commafy($particle->getNumStackParticles($stackid));
	if ($nump == 0) continue;
	echo divtitle("STACK: <font class='aptitle'>".$s['shownstackname']
		."</font> (ID: <font>"
		."<a target='params' class='aptitle' href='stackreport.php?sId="
		.$stackid."'>".$stackid."</a>"
		."</font>)");


	echo "<table border='0'>\n";
	$stackavg = $s['path']."/average.mrc";
	if (file_exists($stackavg)) {
		echo "<tr><td rowspan='15' align='center'>";
		echo "<img src='loadimg.php?filename=$stackavg' height='150'><br/>\n";
		echo "<i>averaged stack image</i><br/>\n";
		echo "</td></tr>\n\n";
	} #endif

	# get pixel size of stack
	$mpix=($particle->getStackPixelSizeFromStackId($stackid));
	$apix=format_angstrom_number($mpix)."/pixel";

	# get box size
	$boxsz=($s['bin']) ? $s['boxSize']/$s['bin'] : $s['boxSize'];
	$boxsz.=" pixels";
	
	# add edit button to description
	$descDiv="<div id='descText".$stackid."' style='position:absolute'>";
	$descDiv.=$s['description'];
	$descDiv.=" <input type='button' name='editdesc' value='edit' onclick=\"javascript:hideEditForm('$stackid')\">";
	$descDiv.="</div>\n";
	$descDiv.="<div id='descForm".$stackid."' style='visibility:hidden;'>";
	$descDiv.="<input type='text' name='newdescription' value='";
	$descDiv.=$s['description'];
	$descDiv.="'>";
	$descDiv.=" <input type='submit' name='updateDesc' value='Update'>";
	$descDiv.="</div>\n";

	$display_keys['description']=$descDiv;

	$display_keys['# prtls']=$nump;
	$stackfile = $s['path']."/".$s['name'];
	$display_keys['path']=$s['path'];
	$display_keys['name']="<A target='stackview' HREF='viewstack.php?file=$stackfile&expId=$expId&stackId=$stackid'>".$s['name']."</A>";
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
	        echo formatHtmlRow($k,$v);
	}
	echo "</table>\n";
	echo "<p>\n";
}
echo "</form>\n";
writeBottom();
?>
