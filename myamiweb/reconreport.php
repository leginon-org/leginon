<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Display results for each iteration of a refinement
 */

require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
  
// check if reconstruction is specified
$reconId = $_GET['reconId'];
$refine_params_fields = array('refinerun', 'ang', 'mask', 'imask', 'pad', 'hard', 'classkeep', 'classiter', 'median', 'phasecls', 'refine');
$javascript="<script src='js/viewer.js'></script>\n";

// javascript to display the refinement parameters
$javascript="<script LANGUAGE='JavaScript'>
        function infopopup(";
foreach ($refine_params_fields as $param) {
        if (ereg("\|", $param)) {
	        $namesplit=explode("|", $param);
		$param=end($namesplit);
	}
	$refinestring.="$param,";
}
$refinestring=rtrim($refinestring,',');
$javascript.=$refinestring;
$javascript.=") {
                var newwindow=window.open('','name','height=400, width=200, resizable=1, scrollbar=1');
                newwindow.document.write(\"<HTML><HEAD><link rel='stylesheet' type='text/css' href='css/viewer.css'>\");
                newwindow.document.write('<TITLE>Ace Parameters</TITLE>');
                newwindow.document.write(\"</HEAD><BODY><TABLE class='tableborder' border='1' cellspacing='1' cellpadding='5'>\");\n";
foreach($refine_params_fields as $param) {
        if (ereg("\|", $param)) {
	        $namesplit=explode("|", $param);
		$param=end($namesplit);
	}
	$javascript.="                if ($param) {\n";
	$javascript.="                        newwindow.document.write('<TR><TD>$param</TD>');\n";
        $javascript.="                        newwindow.document.write('<TD>'+$param+'</TD></TR>');\n";
        $javascript.="                }\n";
}
$javascript.="                newwindow.document.write('</TABLE></BODY></HTML>');\n";
$javascript.="                newwindow.document.close()\n";
$javascript.="        }\n";
$javascript.="</script>\n";
 
writeTop("Reconstruction Report","Reconstruction Report Page", $javascript);

// --- Get Reconstruction Data
$particle = new particledata();
$stackId = $particle->getStackIdFromReconId($reconId);
$stackparticles = $particle->getNumStackParticles($stackId);
$stackparams = $particle->getStackParams($stackId);
// get pixel size
$apix=($particle->getPixelSizeFromStackId($stackId))*1e10;
$apix=($stackparams['bin']) ? $apix*$stackparams['bin'] : $apix;

$boxsz=($stackparams['bin']) ? $stackparams['boxSize']/$stackparams['bin'] : $stackparams['boxSize'];

$html = "<BR>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$html .= "<TR>\n";
$display_keys = array ( 'iteration', 'ang incr', 'resolution', 'fsc', 'classes', '# particles', 'density','snapshot');
foreach($display_keys as $key) {
        $html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
}

$refinerun=$particle->getRefinementRunInfo($reconId);
$initmodel=$particle->getInitModelInfo($refinerun['REF|ApInitialModelData|initialModel']);

echo "Stack: $stackparams[stackPath]/$stackparams[name]<BR>\n";
echo "Reconstruction path: $refinerun[path]/<BR>\n";
echo "Particles: $stackparticles<BR>\n";
echo "Initial Model: $initmodel[path]/$initmodel[name]<BR>\n";

$iterations = $particle->getIterationInfo($reconId);

# get list of png files in directory
$pngfiles=array();
$refinedir = opendir($refinerun['path']);
while ($f = readdir($refinedir)) {
        if (eregi('\.png$',$f)) {
	        $pngfiles[] = $f;
	}
}
sort($pngfiles);

# show info for each iteration
foreach ($iterations as $iteration){
        $refinementData=$particle->getRefinementData($refinerun['DEF_id'], $iteration['iteration']);
	$numclasses=$particle->getNumClasses($refinementData['DEF_id']);
        $res = $particle->getResolutionInfo($iteration['REF|ApResolutionData|resolution']);
	$fscfile = ($res) ? $refinerun['path'].'/'.$res['fscfile'] : "None" ;
	$halfres = ($res) ? sprintf("%.2f",$res['half']) : "None" ;
	$numparticles=$stackparticles-$iteration['numBadParticles'];
	$badprtls=$particle->getNumBadParticles($refinementData['DEF_id']);
	$prtlsused=$stackparticles-$badprtls;
	$html .= "<TR>\n";
	$html .= "<TD><A HREF=\"javascript:infopopup(";
	$refinestr2='';
	foreach ($refine_params_fields as $param) {
	        if (!eregi('^ang|mask$|^pad',$param)){$param="EMAN_$param";}
		$refinestr2.="'$iteration[$param]',";
	}
	$refinestr2=rtrim($refinestr2,',');
	$html .=$refinestr2;
	$html .=")\">$iteration[iteration]</A></TD>\n";
	$html .= "<TD>$iteration[ang]</TD>\n";
	$html .= "<TD>$halfres</TD>\n";
	if ($halfres!='None')
	        $html .= "<TD><A HREF='fscplot.php?fscfile=$fscfile&width=800&height=600&apix=$apix&box=$boxsz'><IMG SRC='fscplot.php?fscfile=$fscfile&width=100&height=80&nomargin=TRUE'>\n";
	else $html .= "<TD>-</TD>\n";
	$clsavg = $refinerun['path'].'/'.$iteration['classAverage'];
	$html .= "<TD><A TARGET='black' HREF='viewstack.php?file=$clsavg'>$numclasses</A></TD>\n";
#	$html .= "<TD><A TARGET='blank' HREF='classinfo.php?refinement=$refinementData[DEF_id]&w=800&h=600'>$numclasses</A></TD>\n";
	$html .= "<TD>$prtlsused</TD>\n";
	$html .= "<TD>$iteration[volumeDensity]</TD>\n";
	$html .= "<TD>\n";
	foreach ($pngfiles as $snapshot) {
	        if (eregi($iteration['volumeDensity'],$snapshot)) {
		        $snapfile = $refinerun['path'].'/'.$snapshot;
			$html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><IMG SRC='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
		}
	}
	$html .= "</TD>\n";
	$html .= "</TR>\n";
}
$html.="</TABLE>\n";

echo "<P><FORM NAME='compareparticles' METHOD='POST' ACTION='compare_eulers.php'>
Compare Iterations:
<SELECT NAME='comp_param'>\n";
echo "<OPTION>Eulers</OPTION>\n";
echo "<OPTION>Inplane Rotation</OPTION>\n";
echo "<OPTION>Shifts</OPTION>\n";
echo "<OPTION>Quality Factor</OPTION>\n";
echo "</SELECT>\n";
echo "Iteration 1: <SELECT NAME='iter1'>\n";
foreach ($iterations as $iteration){
        echo "<OPTION>$iteration[iteration]</OPTION>\n";
}
echo "</SELECT>\n";
echo "Iteration 2: <SELECT NAME='iter2'>\n";
foreach ($iterations as $iteration){
        echo "<OPTION>$iteration[iteration]</OPTION>\n";
}
echo "</SELECT>\n";
echo "<BR><INPUT TYPE='SUBMIT' NAME='compare' VALUE='compare'>\n";
echo "<INPUT TYPE='HIDDEN' NAME='reconId' VALUE='$reconId'>\n";
echo "</FORM>\n";

echo $html;

writeBottom();
?>
