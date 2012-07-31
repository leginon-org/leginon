<?php

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";

$ctf = new particledata();

$sessionId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$sessionId";

$fieldarray = $ctf->getCTFParameterFields();
foreach ($fieldarray as $k=>$v) {
	$aceparamsfields[] = $k;
}

// *********************
// SETUP JAVA SCRIPT
// *********************

$javafunctions="
<script LANGUAGE='JavaScript'>
	function infopopup(";
foreach ($aceparamsfields as $param) {
	if (preg_match("%\|%", $param)) {
		$namesplit=explode("|",$param);
		$param=end($namesplit);
	}
	$acestring .= "$param,";
}

$acestring=rtrim($acestring,',');	
$javafunctions.= $acestring;
$javafunctions.="){
		var newwindow=window.open('','name','height=560, width=480, resizable=1, scrollbars=1');
		newwindow.document.write(\"<HTML><HEAD><link rel='stylesheet' type='text/css' href='../css/viewer.css'>\");
		newwindow.document.write('<TITLE>Ace Parameters</TITLE>');
		newwindow.document.write(\"</HEAD><BODY><TABLE class='tableborder' border='1' cellspacing='1' cellpadding='5'>\");";

foreach ($aceparamsfields as $param) {
	if (preg_match("%\|%", $param)) {
		$namesplit=explode("|",$param);
		$param=end($namesplit);
	}
	
	$javafunctions.= "if ($param && $param.length > 0) {\n";
	$javafunctions.= "  newwindow.document.write('<tr><td><b>$param</b></td>');\n";
	$javafunctions.= "  newwindow.document.write('<td>'+$param+'</td></tr>');\n";
	$javafunctions.= "};\n";
}
$javafunctions.= "newwindow.document.write('</table></BODY></HTML>');\n";
$javafunctions.= "newwindow.document.close();\n";
$javafunctions.= "}\n";
$javafunctions.= "</script>\n";
$javafunctions.= editTextJava();

// *********************
// FORMAT HTML
// *********************

processing_header('CTF report','CTF Report',$javafunctions);

if (!$_GET['showHidden']) {
	$ctfrundatas = $ctf->getCtfRunIds($sessionId, False);
	$hidectfrundatas = $ctf->getCtfRunIds($sessionId, True);
} else {
	$ctfrundatas = $ctf->getCtfRunIds($sessionId, True);
	$hidectfrundatas = $ctfrundatas;
}

if (!$ctfrundatas && $hidectfrundatas) {
	$ctfrundatas = $ctf->getCtfRunIds($sessionId, True);
	$hidectfrundatas = $ctfrundatas;
}

if (count($ctfrundatas) != count($hidectfrundatas) && !$_GET['showHidden']) {
	$numhidden = count($hidectfrundatas) - count($ctfrundatas);
	echo "<a href='".$formAction."&showHidden=1'>[Show ".$numhidden." hidden ctf runs]</a><br/><br/>\n";
	echo "<form name='ctfform' method='post' action='$formAction'>\n";
} elseif($_GET['showHidden']) {
	echo "<a href='".$formAction."'>[Hide hidden ctf runs]</a><br/>\n";
	echo "<form name='ctfform' method='post' action='$formAction&showHidden=1'>\n";
}

if ($ctfrundatas) {
	echo "<h3>Summary of confidence values from all runs</h3>\n";
	echo "<a href='ctfgraph.php?hg=1&expId=$sessionId&s=1&f=confidence'>\n";
	echo "<img border='0' width='400' height='300' src='ctfgraph.php?w=400&h=300&hg=1&expId=$sessionId&s=1&f=confidence'></a>\n";
	echo "<br/>\n";

	echo "<h3>Confidence values during run</h3>\n";
	echo "<a href='ctfgraph.php?hg=0&expId=$sessionId&s=1&f=confidence'>\n";
	echo "<img border='0' width='400' height='300' src='ctfgraph.php?w=400&h=300&hg=0&expId=$sessionId&s=1&f=confidence'></a>\n";
	echo "<br/>\n";

	$ctfdownlink .= "<h3>";
	$ctfdownlink .= "<a href='downloadctfdata.php?expId=$sessionId'>\n";
	$ctfdownlink .= "  <img style='vertical-align:middle' src='img/download_arrow.png' border='0' width='16' height='17' alt='download best ctf data'>&nbsp;download best ctf data\n";
	$ctfdownlink .= "</a></h3>\n";
	echo $ctfdownlink;

	foreach ($ctfrundatas as $ctfrundata) {
		$ctfrunid=$ctfrundata['DEF_id'];
		$rName=$ctfrundata['name'];

		$ctfdata= $ctf->getAceParams($ctfrunid);
		if ($_POST['hideRun'.$ctfrunid] == 'hide') {
			$ctf->updateHide('ApAceRunData', $ctfrunid, '1');
			$ctfdata['hidden']='1';
		} elseif ($_POST['unhideRun'.$ctfrunid] == 'unhide') {
			$ctf->updateHide('ApAceRunData', $ctfrunid, '0');
			$ctfdata['hidden']='0';
		}

		//echo "ctfdata".print_r($ctfdata);
		if ($ctfdata['stig']!=1 && $ctfdata!=0) {
			$fields = array('defocus1', 'confidence', 'confidence_d', 'amplitude_contrast');
		}
		else {
			$fields = array('defocus1', 'defocus2', 'confidence', 'angle_astigmatism', 'amplitude_contrast');
		}
		$stats = $ctf->getCTFStats($fields, $sessionId, $ctfrunid);
		$display_ctf=false;
		foreach($stats as $field=>$data) {
			//echo $field."&nbsp;=>&nbsp;".$data."<br/>\n";
			foreach($data as $k=>$v) {
				$display_ctf=true;
				$imageId = $stats[$field][$k]['id'];
				$p = $leginondata->getPresetFromImageId($imageId);
				$stats[$field][$k]['preset'] = $p['name'];
				$cdf = '<a href="ctfgraph.php?hg=1&expId='
						.$sessionId.'&rId='.$ctfrunid.'&f='.$field.'&preset='.$p['name'].'">'
					.'<img border="0" src="ctfgraph.php?w=100&hg=1&expId='
						.$sessionId.'&rId='.$ctfrunid.'&f='.$field.'&preset='.$p['name'].'"></a>';
				$stats[$field][$k]['img'] = $cdf;
			}
		}
		$display_keys = array ( 'preset', 'nb', 'min', 'max', 'avg', 'stddev');
		if ($display_ctf) {
			$popupstr = "<a href=\"javascript:infopopup(";
			foreach ($aceparamsfields as $param) {
				$popupstr .= "'".$ctfdata[$param]."',";
			}
			$popupstr = rtrim($popupstr,',');	
			$popupstr .=  ")\">\n";

			echo "\n\n<br/>\n\n";
			echo openRoundBorder();
			echo "<table cellspacing='3'>";

			echo "<tr>";
				echo "<td>\n";
				$j = "";
				if ($ctfdata['hidden'] == 1) {
					$j.= " <font color='#cc0000'>HIDDEN</font>\n";
					$j.= " <input class='edit' type='submit' name='unhideRun".$ctfrunid."' value='unhide'>\n";
				} else $j.= " <input class='edit' type='submit' name='hideRun".$ctfrunid."' value='hide'>\n";
				$downloadLink = "(<font size='-2'><a href='downloadctfdata.php?expId=$sessionId&runId=$ctfrunid'>\n";
				$downloadLink .= "  <img style='vertical-align:middle' src='img/download_arrow.png' border='0' width='16' height='17' alt='download coordinates'>";
				$downloadLink .= "  &nbsp;download ctf data\n";
				$downloadLink .= "</a></font>)\n";
				echo apdivtitle("Ctf Run: ".$ctfrunid." ".$popupstr."<b>".$rName."</b></a>".$j."&nbsp$downloadLink\n");
				
				echo "</td>\n";
			echo "</tr>\n";

			echo "<tr bgcolor='#ffffff'>\n";
				echo "<td>Path:&nbsp;<i>".$ctfdata['path']."</i></td>\n";
			echo "</tr>\n";

			if ($ctfdata['resamplefr']) {
				echo "<tr bgcolor='#ffffff'>\n";
					echo "<td>Resample Freq:&nbsp;".$ctfdata['resamplefr']."</td>\n";
				echo "</tr>\n";
			} elseif ($ctfdata['bin']) {
				echo "<tr bgcolor='#ffffff'>\n";
					echo "<td>Binning:&nbsp;".$ctfdata['bin']."</td>\n";
				echo "</tr>\n";
			}

			echo "<tr><td colspan='10'>\n";
				echo displayCTFstats($stats, $display_keys);
			echo "</td></tr>\n";
			echo "</table>";
			echo closeRoundBorder();

		} else
			echo "no CTF information available <br/>";
	}
	echo "</form><br/>\n";
} else {
	echo "no CTF information available <br/>";
}

if (count($ctfrundatas) != count($hidectfrundatas) && !$_GET['showHidden']) {
	$numhidden = count($hidectfrundatas) - count($ctfrundatas);
	echo "<a href='".$formAction."&showHidden=1'>[Show ".$numhidden." hidden ctf runs]</a><br/><br/>\n";
	echo "<form name='ctfform' method='post' action='$formAction'>\n";
} elseif($_GET['showHidden']) {
	echo "<a href='".$formAction."'>[Hide hidden ctf runs]</a><br/>\n";
	echo "<form name='ctfform' method='post' action='$formAction&showHidden=1'>\n";
}

processing_footer();
