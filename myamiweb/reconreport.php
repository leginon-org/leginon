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
$display_keys = array ( 'iteration', 'ang incr', 'resolution', 'fsc', 'classes', 'distr', '# particles', 'density','snapshot');
foreach($display_keys as $key) {
        $html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
}
$html .= "</TR>\n";

$refinerun=$particle->getRefinementRunInfo($reconId);
$initmodel=$particle->getInitModelInfo($refinerun['REF|ApInitialModelData|initialModel']);

$stackfile=$stackparams['stackPath']."/".$stackparams['name'];
$initmodelname=$initmodel['name'];

echo "Stack: <A TARGET='stackview' HREF='viewstack.php?file=$stackfile'>$stackfile</A><BR>\n";
echo "Reconstruction path: $refinerun[path]/<BR>\n";
echo "Particles: $stackparticles<BR>\n";
echo "Initial Model: $initmodel[path]/$initmodelname<BR>\n";
$misc = $particle->getMiscInfoFromReconId($reconId);
if ($misc) echo "<A HREF='viewmisc.php?reconId=$reconId'>[Related Images, Movies, etc]</A><BR>\n"; 

$iterations = $particle->getIterationInfo($reconId);

# get starting model png files
$initpngs = array();
$initdir = opendir($initmodel['path']);
while ($f = readdir($initdir)){
  if (eregi($initmodelname.'.*\.png$',$f)) {
    $initpngs[] = $f;
  }
}
sort($initpngs);

# get list of png files in directory
$pngfiles=array();
$refinedir = opendir($refinerun['path']);
while ($f = readdir($refinedir)) {
  if (eregi('\.png$',$f)) {
    $pngfiles[] = $f;
  }
}
sort($pngfiles);

# display starting model
$html .= "<TR>\n";
foreach ($display_keys as $p) {
  $html .= "<TD>";
  if ($p == 'iteration') $html .= "0";
  elseif ($p == 'snapshot') {
    foreach ($initpngs as $snapshot) {
      $snapfile = $initmodel['path'].'/'.$snapshot;
      $html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><IMG SRC='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
    }
  }
  $html .= "</TD>";
}
$html .= "</TR>\n";

# show info for each iteration
sort($iterations);
foreach ($iterations as $iteration){
  $refinementData=$particle->getRefinementData($refinerun['DEF_id'], $iteration['iteration']);
	$numclasses=$particle->getNumClasses($refinementData['DEF_id']);
  $res = $particle->getResolutionInfo($iteration['REF|ApResolutionData|resolution']);
	$fscfile = ($res) ? $refinerun['path'].'/'.$res['fscfile'] : "None" ;
	$halfres = ($res) ? sprintf("%.2f",$res['half']) : "None" ;
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
	$html .= "<TD><A TARGET='stackview' HREF='viewstack.php?file=$clsavg'>$iteration[classAverage]</A></TD>\n";
	$html .= "<TD><A TARGET='blank' HREF='classinfo.php?refinement=$refinementData[DEF_id]&w=800&h=600'>$numclasses</A></TD>\n";
	$html .= "<TD>$prtlsused<BR><A TARGET='stackview' HREF='badprtls.php?refinement=$refinementData[DEF_id]'>[$badprtls bad]</A></TD>\n";
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
<select name='comp_param'>\n";
echo "<option>Eulers</option>\n";
echo "<option>Inplane rotation</option>\n";
echo "<option>Shifts</option>\n";
echo "<option>Quality Factor</option>\n";
echo "</select>\n";
echo "Iteration 1: <select name='iter1'>\n";
foreach ($iterations as $iteration){
        echo "<option>$iteration[iteration]</option>\n";
}
echo "</select>\n";
echo "Iteration 2: <select name='iter2'>\n";
foreach ($iterations as $iteration){
        echo "<option>$iteration[iteration]</option>\n";
}
echo "</select>\n";
echo "<br />";
echo "download: <input type='checkbox' name='dwd' >\n";
echo "<input type='submit' name='compare' value='compare'>\n";
echo "<input type='hidden' name='reconId' value='$reconId'>\n";
echo "</FORM>\n";

echo $html;

writeBottom();
?>
