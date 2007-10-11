<?php
require "inc/ctf.inc";
require "inc/util.inc";
require "inc/leginon.inc";

$ctf = new ctfdata();

$defaultId= 1766;
$sessionId= ($_GET['Id']) ? $_GET['Id'] : $defaultId;
$ace_params_fields = array ('acerun', 'display', 'stig', 'medium', 'df_override', 'edgethcarbon', 'edgethice', 'pfcarbon', 'pfice', 'overlap', 'fieldsize', 'resamplefr', 'drange', 'reprocess' );


	
?>
<html>
<head>
<title><?php echo $title; ?> CTF report</title>
<link rel="stylesheet" type="text/css" href="../css/viewer.css"> 
<script LANGUAGE='JavaScript'>
	function infopopup(<?
		foreach ($ace_params_fields as $param) {
			if (ereg("\|", $param)) {
				$namesplit=explode("|",$param);
				$param=end($namesplit);
			}
			$acestring .= "$param,";
		}

		$acestring=rtrim($acestring,',');	
		echo $acestring;
		?>){
		var newwindow=window.open('','name','height=400, width=200, resizable=1, scrollbars=1');
		newwindow.document.write('<HTML><HEAD><link rel="stylesheet" type="text/css" href="../css/viewer.css">');
		newwindow.document.write('<TITLE>Ace Parameters</TITLE>');
		newwindow.document.write("</HEAD><BODY><TABLE class='tableborder' border='1' cellspacing='1' cellpadding='5'>");
		<?
				foreach ($ace_params_fields as $param) {
					if (ereg("\|", $param)) {
						$namesplit=explode("|",$param);
						$param=end($namesplit);
					}
					echo "newwindow.document.write('<TR><TD>$param</TD>');\n";
					echo "newwindow.document.write('<TD>'+$param+'</TD></TR>');\n";
				}
				echo "newwindow.document.write('</TABLE></BODY></HTML>');\n";
				echo "newwindow.document.close()\n";
			?>
	}
</script>
</head>
<body>
<?php echo  divtitle("CTF Report $title Experiment"); ?>
<br>
<?php

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
	$stats = $ctf->getStats($fields, $sessionId, $rId);
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
		echo "\n<table>";
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
		echo display_stats($stats, $display_keys);
		echo "</table>";
		echo "<br>";	
	} else echo "no CTF information available";
}

?>
</body>
</html>
