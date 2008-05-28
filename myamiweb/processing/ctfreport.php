<?php

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";

$ctf = new particledata();

$sessionId = $_GET['expId'];
$ace_params_fields = array ('acerun', 'display', 'stig', 'medium', 'df_override', 'edgethcarbon', 'edgethice', 'pfcarbon', 'pfice', 'overlap', 'fieldsize', 'resamplefr', 'drange', 'reprocess' );

$javafunctions="
<script LANGUAGE='JavaScript'>
	function infopopup(";
foreach ($ace_params_fields as $param) {
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

foreach ($ace_params_fields as $param) {
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

processing_header('CTF report','CTF Report',$javafunctions);

$runIds = $ctf->getCtfRunIds($sessionId);
foreach ($runIds as $runId) {
	$rId=$runId['DEF_id'];
	$rName=$runId['name'];
	$ace_params= $ctf->getAceParams($rId);
	if ($ace_params['stig']==0) {
		$fields = array('defocus1', 'confidence', 'confidence_d');
	}
	else {
		$fields = array('defocus1', 'defocus2', 'confidence', 'confidence_d');
	}
	$stats = $ctf->getCTFStats($fields, $sessionId, $rId);
	$display_ctf=false;
	foreach($stats as  $field=>$data) {
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
		echo "<table>";
		echo "<tr>";
			echo "<td>";
			echo "Run: ";
			$acestring2='';
			echo "<A HREF=\"javascript:infopopup(";
			foreach ($ace_params_fields as $param) {
				$acestring2 .= "'$ace_params[$param]',";
			}
			$acestring2=rtrim($acestring2,',');	
			echo $acestring2;
			echo ")\"><B>$rName</B></A>";
			echo "</td>";
		echo "</tr>\n";
		echo displayCTFstats($stats, $display_keys);
		echo "</table>";
		echo "<br>";	
	} else echo "no CTF information available";
}

processing_footer();
