<?php

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";

$ctf = new particledata();

$expId = $_GET['expId'];
$showmore = $_GET['showmore'] ? $_GET['showmore'] : '0';
$projectId =getProjectId();
$formAction=$_SERVER['PHP_SELF']."?expId=$expId&showmore=$showmore";

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

// for cutoff values
$javafunctions.= "function changeCutoff(sel) {\n";
$javafunctions.= "  if (sel.value.substring(0,10)=='resolution') {\n";
$javafunctions.= "    document.getElementById('cval').innerHTML='&Aring;';\n";
$javafunctions.= "  } else {document.getElementById('cval').innerHTML='0-1';}\n";
$javafunctions.= "}\n";
$javafunctions.= "function submitCutoff() {\n";
$javafunctions.= "  var sel = document.getElementById('bydf').value;\n";
$javafunctions.= "  var cutoff = document.getElementById('cutoff').value;\n";
$javafunctions.= "  if ((sel.substring(0,10)!='resolution') && \n";
$javafunctions.= "    (cutoff >= 1 || cutoff <= 0)) {\n";
$javafunctions.= "    alert ('Enter a cutoff value between 0 and 1');\n";
$javafunctions.= "    return false;\n";
$javafunctions.= "  }\n";
$javafunctions.= "  var cimg = document.getElementById('cutoffimg');\n";
$javafunctions.= "  var imgsrc = 'ctfgraph.php?w=600&h=350&hg=1&expId=$expId&s=1'\n";
$javafunctions.= "  imgsrc += '&f=defocus1&cutoff='+ cutoff + '&bydf=' + sel;\n";
$javafunctions.= "  cimg.src = imgsrc;\n";
$javafunctions.= "  cimg.width='600';\n";
$javafunctions.= "  cimg.height='350';\n";
$javafunctions.= "}\n";
$javafunctions.= "</script>\n";
$javafunctions.= editTextJava();

// *********************
// FORMAT HTML
// *********************

processing_header('CTF report','CTF Report',$javafunctions);

if (!$_GET['showHidden']) {
	$ctfrundatas = $ctf->getCtfRunIds($expId, False);
	$hidectfrundatas = $ctf->getCtfRunIds($expId, True);
} else {
	$ctfrundatas = $ctf->getCtfRunIds($expId, True);
	$hidectfrundatas = $ctfrundatas;
}

if (!$ctfrundatas && $hidectfrundatas) {
	$ctfrundatas = $ctf->getCtfRunIds($expId, True);
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
	if ($showmore > 0) {
		$showmorelink = $_SERVER['PHP_SELF']."?expId=$expId&showmore=0";
		echo "<a href='$showmorelink'>[show less statistics]</a>\n";
	}	else {
		$showmorelink = $_SERVER['PHP_SELF']."?expId=$expId&showmore=1";
		echo "<a href='$showmorelink'>[show all statistics]</a>\n";
	}
	echo "<br/>\n";
	echo "<h3>Summary of confidence values from all runs</h3>\n";

	echo "<table>\n";

	// Overall Summary
	echo "<tr><td colspan='2' align='center'>\n";

		$minconf = 0.2;
		$ctfinfo = $ctf->getBestCtfInfoByResolution($expId, $minconf);

		$numctfest = count($ctfinfo);

		if ($numctfest > 1) {

			echo "<b>Overall Summary for $numctfest CTF estimates</b></br>\n";

			$fields = array('defocus1', 'defocus2', 
				//'confidence', 'confidence_d', 
				'angle_astigmatism', 'amplitude_contrast',  
				'confidence_30_10', 'confidence_5_peak',  
				'resolution_80_percent', 'resolution_50_percent');
			$stats = $ctf->getCTFStats($fields, $expId);
			$display_ctf=false;
			foreach($stats as $field=>$data) {
				//echo $field."&nbsp;=>&nbsp;".$data."<br/>\n";
				foreach($data as $k=>$v) {
					$display_ctf=true;
					$imageId = $stats[$field][$k]['id'];
					$p = $leginondata->getPresetFromImageId($imageId);
					$stats[$field][$k]['preset'] = $p['name'];
					$cdf = '<a href="ctfgraph.php?hg=1&expId='
							.$expId.'&rId='.$ctfrunid.'&f='.$field.'&preset='.$p['name'].'">'
						.'<img border="0" src="ctfgraph.php?w=100&hg=1&expId='
							.$expId.'&rId='.$ctfrunid.'&f='.$field.'&preset='.$p['name'].'"></a>';
					$stats[$field][$k]['img'] = $cdf;
				}
			}
			$display_keys = array ( 'nb', 'min', 'max', 'avg', 'stddev');

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
				echo "<td colspan='10'>\n";
				$j = "";
				if ($ctfdata['hidden'] == 1) {
					$j.= " <font color='#cc0000'>HIDDEN</font>\n";
					$j.= " <input class='edit' type='submit' name='unhideRun".$ctfrunid."' value='unhide'>\n";
				} else $j.= " <input class='edit' type='submit' name='hideRun".$ctfrunid."' value='hide'>\n";
				$j .= "<input class='edit' type='button' onClick='parent.location=\"dropctf.php?expId="
					."$expId&ctfId=$ctfrunid\"' value='delete'>\n";
				$downloadLink = "(<font size='-2'><a href='downloadctfdata.php?expId=$expId&runId=$ctfrunid'>\n";
				$downloadLink .= "  <img style='vertical-align:middle' src='img/download_arrow.png' "
					." border='0' width='16' height='17' alt='download coordinates'>";
				$downloadLink .= "  &nbsp;download ctf data\n";
				$downloadLink .= "</a></font>)\n";
				echo apdivtitle("Overall Stats: &nbsp$downloadLink\n");
			
				echo "</td>\n";
			echo "</tr>\n";

			if ($ctfdata['resamplefr']) {
				echo "<tr bgcolor='#ffffff'>\n";
					echo "<td>Resample Freq</td><td>".$ctfdata['resamplefr']."</td>\n";
				echo "</tr>\n";
			} elseif ($ctfdata['bin']) {
				echo "<tr bgcolor='#ffffff'>\n";
					echo "<td>Binning</td><td>".$ctfdata['bin']."</td>\n";
				echo "</tr>\n";
			}

			echo "<tr><td colspan='10'>\n";
				echo displayCTFstats($stats, $display_keys);
			echo "</td></tr>\n";
			echo "</table>";
			echo closeRoundBorder();

		}

	echo "</td></tr>";


	// Row 0
	echo "<tr><td>\n";
		echo "<h3>Defocus 1</h3>";
		echo "<a href='ctfgraph.php?hg=1&expId=$expId&s=1&f=defocus1'>\n";
		echo "<img border='0' width='400' height='200' src='ctfgraph.php?"
			."w=800&h=600&hg=1&expId=$expId&s=1&xmax=7e-6&f=defocus1' alt='please wait...'></a>\n";
	echo "</td><td>\n";
		echo "<h3>Defocus 2</h3>";
		echo "<a href='ctfgraph.php?hg=1&expId=$expId&s=1&f=defocus2'>\n";
		echo "<img border='0' width='400' height='200' src='ctfgraph.php?"
			."w=800&h=600&hg=1&expId=$expId&s=1&xmax=7e-6&f=defocus2' alt='please wait...'></a>\n";
	echo "</td></tr>";

	// Row 0
	echo "<tr><td>\n";
		echo "<h3>Amplitude Contrast</h3>";
		echo "<a href='ctfgraph.php?hg=1&expId=$expId&s=1&xmin=0.0&f=amplitude_contrast'>\n";
		echo "<img border='0' width='400' height='200' src='ctfgraph.php?"
			."w=800&h=600&hg=1&expId=$expId&s=1&xmin=0.0&f=amplitude_contrast' alt='please wait...'></a>\n";
	echo "</td><td>\n";
		echo "<h3>Angle Astigmatism</h3>";
		echo "<a href='ctfgraph.php?hg=1&expId=$expId&s=1&xmin=-90&xmax=90&f=angle_astigmatism'>\n";
		echo "<img border='0' width='400' height='200' src='ctfgraph.php?"
			."w=800&h=600&hg=1&expId=$expId&s=1&xmin=-90&xmax=90&f=angle_astigmatism' alt='please wait...'></a>\n";
	echo "</td></tr>";

	$confidenceOpts=array();

	if ($showmore > 0) {
	// Row 0
	$confidenceOpts[]='confidence';
	echo "<tr><td>\n";
		echo "<h3>Merged Confidence</h3>";
		echo "<a href='ctfgraph.php?hg=1&expId=$expId&s=1&f=confidence'>\n";
		echo "<img border='0' width='400' height='200' src='ctfgraph.php?"
			."w=800&h=600&hg=1&expId=$expId&s=1&xmin=0.3&f=confidence' alt='please wait...'></a>\n";
	$confidenceOpts[]='confidence_d';
	echo "</td><td>\n";
		echo "<h3>Confidence D</h3>";
		echo "<a href='ctfgraph.php?hg=1&expId=$expId&s=1&f=confidence_d'>\n";
		echo "<img border='0' width='400' height='200' src='ctfgraph.php?"
			."w=800&h=600&hg=1&expId=$expId&s=1&xmin=0.3&f=confidence_d' alt='please wait...'></a>\n";
	echo "</td></tr>";
	}

	// Row 1
	$confidenceOpts[]='confidence_30_10';
	echo "<tr><td>\n";
		echo "<h3>Confidence 1/30&Aring; - 1/10&Aring;</h3>";
		echo "<a href='ctfgraph.php?hg=1&expId=$expId&s=1&f=confidence_30_10'>\n";
		echo "<img border='0' width='400' height='200' src='ctfgraph.php?"
			."w=800&h=600&hg=1&expId=$expId&s=1&xmin=0.3&f=confidence_30_10' alt='please wait...'></a>\n";
	$confidenceOpts[]='confidence_5_peak';
	echo "</td><td>\n";
		echo "<h3>Confidence 5 Peaks</h3>";
		echo "<a href='ctfgraph.php?hg=1&expId=$expId&s=1&f=confidence_5_peak'>\n";
		echo "<img border='0' width='400' height='200' src='ctfgraph.php?"
			."w=800&h=600&hg=1&expId=$expId&s=1&xmin=0.3&f=confidence_5_peak' alt='please wait...'></a>\n";
	echo "</td></tr>";
	// Row 2
	$confidenceOpts[]='resolution_80_percent';
	echo "<tr><td>\n";
		echo "<h3>Resolution at 0.8</h3>";
		echo "<a href='ctfgraph.php?hg=1&expId=$expId&s=1&xmin=2&xmax=50&f=resolution_80_percent'>\n";
		echo "<img border='0' width='400' height='200' src='ctfgraph.php?"
			."w=800&h=600&hg=1&expId=$expId&s=1&xmin=2&xmax=30&f=resolution_80_percent' alt='please wait...'></a>\n";
	$confidenceOpts[]='resolution_50_percent';
	echo "</td><td>\n";
		echo "<h3>Resolution at 0.5</h3>";
		echo "<a href='ctfgraph.php?hg=1&expId=$expId&s=1&xmin=2&xmax=30&f=resolution_50_percent'>\n";
		echo "<img border='0' width='400' height='200' src='ctfgraph.php?"
			."w=800&h=600&hg=1&expId=$expId&s=1&xmin=2&xmax=30&f=resolution_50_percent' alt='please wait...'></a>\n";
	echo "</td></tr>";
	// Row 3
	echo "<tr><td>\n";
		echo "<h3>Confidence values during run</h3>\n";
		echo "<a href='ctfgraph.php?hg=0&expId=$expId&s=1&f=confidence'>\n";
		echo "<img border='0' width='400' height='200' src='ctfgraph.php?"
			."w=800&h=600&hg=0&expId=$expId&s=1&f=confidence'></a>\n";
	echo "</td><td>\n";
	// very hacky
		$sessiondata = getSessionList($projectId, $expId);
		$preset = end($sessiondata['presets']);
		echo "<h3>Difference from Leginon for preset '$preset'</h3>\n";
		echo "<a href='autofocacegraph.php?hg=0&expId=$expId&s=1&f=difference&preset=$preset'>\n";
		echo "<img border='0' width='400' height='200' src='autofocacegraph.php?"
			."hg=0&expId=$expId&s=1&f=difference&preset=$preset' alt='please wait...'></a>\n";
	echo "</td></tr>";
	echo "</table>";

	// show defocus histograms with different cutoffs
	echo "<hr>\n";
	echo "<h3>Generate defocus histogram with applied cutoff</h3>\n";

	echo "<table cellpadding=5 cellspacing=0 border=0><tr><td>\n";
	echo "<b>Cutoff method: </b><select name='bydf' id='bydf' onChange='changeCutoff(this)'>\n";
	foreach ($confidenceOpts as $confm) {
		echo "<option>$confm</option>\n";
	}
	echo "</select>\n";
	echo "</td></tr><tr><td>\n";

	echo "<b>Cutoff value (<span id='cval'>0-1</span>): </b><input name='cutoff' type='text' id='cutoff' size='5'>\n";
	echo "</td></tr><tr><td>\n";

	echo "<input type='submit' name='applycutoff' value='Generate Histogram' onclick='submitCutoff()'>\n";
	echo "</td></tr></table>\n";
	echo "<img id='cutoffimg' name='cutoffimg' border='0'>\n";
	echo "<hr>\n";

	$ctfdownlink = "<h3>";
	$ctfdownlink .= "<a href='downloadctfdata.php?expId=$expId&relion=True'>\n";
	$ctfdownlink .= "  <img style='vertical-align:middle' src='img/download_arrow.png' border='0' width='16' height='17' alt='download star file for RELION'>&nbsp;download star file for RELION\n";
	$ctfdownlink .= "</a></h3>\n";
	echo $ctfdownlink;

	$ctfdownlink = "<h3>";
	$ctfdownlink .= "<a href='downloadctfdata.php?expId=$expId'>\n";
	$ctfdownlink .= "  <img style='vertical-align:middle' src='img/download_arrow.png' border='0' width='16' height='17' alt='download best ctf data'>&nbsp;download best ctf data\n";
	$ctfdownlink .= "</a></h3>\n";
	echo $ctfdownlink;

	$ctfdownlink = "<h3>";
	$ctfdownlink .= "<a href='downloadctfemxfile.php?expId=$expId'>\n";
	$ctfdownlink .= "  <img style='vertical-align:middle' src='img/download_arrow.png' border='0' width='16' height='17' alt='download best ctf data'>&nbsp;download best ctf EMX file\n";
	$ctfdownlink .= "</a></h3>\n";
	echo $ctfdownlink;


	echo "<hr/>\n";

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
		$fields = array('defocus1', 'defocus2', 
			//'confidence', 'confidence_d', 
			'angle_astigmatism', 'amplitude_contrast',  
			'confidence_30_10', 'confidence_5_peak',  
			'resolution_80_percent', 'resolution_50_percent');
		$stats = $ctf->getCTFStats($fields, $expId, $ctfrunid);
		$display_ctf=false;
		foreach($stats as $field=>$data) {
			//echo $field."&nbsp;=>&nbsp;".$data."<br/>\n";
			foreach($data as $k=>$v) {
				$display_ctf=true;
				$imageId = $stats[$field][$k]['id'];
				$p = $leginondata->getPresetFromImageId($imageId);
				$stats[$field][$k]['preset'] = $p['name'];
				$cdf = '<a href="ctfgraph.php?hg=1&expId='
						.$expId.'&rId='.$ctfrunid.'&f='.$field.'&preset='.$p['name'].'">'
					.'<img border="0" src="ctfgraph.php?w=100&hg=1&expId='
						.$expId.'&rId='.$ctfrunid.'&f='.$field.'&preset='.$p['name'].'"></a>';
				$stats[$field][$k]['img'] = $cdf;
			}
		}
		$display_keys = array ( 'nb', 'min', 'max', 'avg', 'stddev');
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
				echo "<td colspan='10'>\n";
				$j = "";
				if ($ctfdata['hidden'] == 1) {
					$j.= " <font color='#cc0000'>HIDDEN</font>\n";
					$j.= " <input class='edit' type='submit' name='unhideRun".$ctfrunid."' value='unhide'>\n";
				} else $j.= " <input class='edit' type='submit' name='hideRun".$ctfrunid."' value='hide'>\n";
				$j .= "<input class='edit' type='button' onClick='parent.location=\"dropctf.php?expId=$expId&ctfId=$ctfrunid\"' value='delete'>\n";
				$downloadLink = "(<font size='-2'><a href='downloadctfdata.php?expId=$expId&runId=$ctfrunid'>\n";
				$downloadLink .= "  <img style='vertical-align:middle' src='img/download_arrow.png' border='0' width='16' height='17' alt='download coordinates'>";
				$downloadLink .= "  &nbsp;download ctf data\n";
				$downloadLink .= "</a></font>)\n";
				echo apdivtitle("Ctf Run: ".$ctfrunid." ".$popupstr."<b>".$rName."</b></a>".$j."&nbsp$downloadLink\n");
				
				echo "</td>\n";
			echo "</tr>\n";

			echo "<tr bgcolor='#ffffff'>\n";
				echo "<td>Time:</td><td><i>".$ctfdata['DEF_timestamp']."</i></td>\n";
			echo "</tr>\n";

			echo "<tr bgcolor='#ffffff'>\n";
				echo "<td>Path:</td><td><i>".$ctfdata['path']."</i></td>\n";
			echo "</tr>\n";

			if ($ctfdata['resamplefr']) {
				echo "<tr bgcolor='#ffffff'>\n";
					echo "<td>Resample Freq</td><td>".$ctfdata['resamplefr']."</td>\n";
				echo "</tr>\n";
			} elseif ($ctfdata['bin']) {
				echo "<tr bgcolor='#ffffff'>\n";
					echo "<td>Binning</td><td>".$ctfdata['bin']."</td>\n";
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
