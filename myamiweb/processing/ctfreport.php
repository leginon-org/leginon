<?php

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";

$ctf = new particledata();

$sessionId = $_GET['expId'];
$aceparamsfields = array (
	'acerun', 'display', 'stig', 'medium',
	'df_override', 'edgethcarbon', 'edgethice', 'pfcarbon',
	'pfice', 'overlap', 'fieldsize', 'resamplefr',
	'drange', 'reprocess', 'path',
);

// *********************
// SETUP JAVA SCRIPT
// *********************

$javafunctions="
<script LANGUAGE='JavaScript'>
	function infopopup(";
foreach ($aceparamsfields as $param) {
	if (ereg("\|", $param)) {
		$namesplit=explode("|",$param);
		$param=end($namesplit);
	}
	$acestring .= "$param,";
}

$acestring=rtrim($acestring,',');	
$javafunctions.= $acestring;
$javafunctions.="){
		var newwindow=window.open('','name','height=400, width=200, resizable=1, scrollbars=1');
		newwindow.document.write(\"<HTML><HEAD><link rel='stylesheet' type='text/css' href='../css/viewer.css'>\");
		newwindow.document.write('<TITLE>Ace Parameters</TITLE>');
		newwindow.document.write(\"</HEAD><BODY><TABLE class='tableborder' border='1' cellspacing='1' cellpadding='5'>\");";

foreach ($aceparamsfields as $param) {
	if (ereg("\|", $param)) {
		$namesplit=explode("|",$param);
		$param=end($namesplit);
	}
	$javafunctions.= "newwindow.document.write('<TR><TD>$param</TD>');\n";
	$javafunctions.= "newwindow.document.write('<TD>'+$param+'</TD></TR>');\n";
}
$javafunctions.= "newwindow.document.write('</TABLE></BODY></HTML>');\n";
$javafunctions.= "newwindow.document.close();\n";
$javafunctions.= "}\n";
$javafunctions.= "</script>\n";

// *********************
// FORMAT HTML
// *********************

processing_header('CTF report','CTF Report',$javafunctions);

$runIds = $ctf->getCtfRunIds($sessionId);
foreach ($runIds as $runId) {
	$rId=$runId['DEF_id'];
	$rName=$runId['name'];
	$ace_params= $ctf->getAceParams($rId);
	//echo "ace_params".print_r($ace_params);
	if ($ace_params['stig']!=1 && $ace_params!=0) {
		$fields = array('defocus1', 'confidence', 'confidence_d', 'amplitude_contrast');
	}
	else {
		$fields = array('defocus1', 'defocus2', 'confidence', 'angle_astigmatism', 'amplitude_contrast');
	}
	$stats = $ctf->getCTFStats($fields, $sessionId, $rId);
	$display_ctf=false;
	foreach($stats as  $field=>$data) {
			//echo $field."&nbsp;=>&nbsp;".$data."<br/>\n";
			foreach($data as $k=>$v) {
				$display_ctf=true;
				$imageId = $stats[$field][$k]['id'];
				$p = $leginondata->getPresetFromImageId($imageId);
				$stats[$field][$k]['preset'] = $p['name'];
				$cdf = '<a href="ctfgraph.php?&hg=1&Id='.$sessionId.'&rId='.$rId.'&f='.$field.'&preset='.$p['name'].'">'
					.'<img border="0" src="ctfgraph.php?w=150&hg=1&Id='.$sessionId.'&rId='.$rId.'&f='.$field.'&preset='.$p['name'].'"></a>';
				$stats[$field][$k]['img'] = $cdf;
			}
	}
	$display_keys = array ( 'preset', 'nb', 'min', 'max', 'avg', 'stddev', 'img');
	if ($display_ctf) {
		$popupstr = "<a href=\"javascript:infopopup(";
		foreach ($aceparamsfields as $param) {
			$popupstr .= "'".$ace_params[$param]."',";
		}
		$popupstr = rtrim($popupstr,',');	
		$popupstr .=  ")\">\n";

		echo "\n\n<br/>\n\n";
		echo openRoundBorder();
		echo "<table cellspacing='3'>";

		echo "<tr>";
			echo "<td>\n";
			echo apdivtitle("Ctf Run: ".$popupstr."<b>".$rName."</b></a>\n");
			echo "</td>\n";
		echo "</tr>\n";

		echo "<tr bgcolor='#ffffff'>\n";
			echo "<td>Path:&nbsp;<i>".$ace_params['path']."</i></td>\n";
		echo "</tr>\n";

		echo "<tr bgcolor='#ffffff'>\n";
			echo "<td>Resample Freq:&nbsp;".$ace_params['resamplefr']."</td>\n";
		echo "</tr>\n";

		echo "<tr><td colspan='10'>\n";
			echo displayCTFstats($stats, $display_keys);
		echo "</td></tr>\n";
		echo "</table>";
		echo closeRoundBorder();

	} else
		echo "no CTF information available <br/>";
}

processing_footer();
