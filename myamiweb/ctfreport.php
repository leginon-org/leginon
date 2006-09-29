<?php
require('inc/ctf.inc');
require('inc/util.inc');
require('inc/leginon.inc');
$ctf = new ctfdata();

$defaultId= 1766;
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;

?>
<html>
<head>
<title><?php echo $title; ?> CTF report</title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
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
			echo "Run: $rName";
			echo "</td>";
		echo "</tr>";
		echo "</table>";
		echo display_stats($stats, $display_keys);
	} else echo "no CTF information available";
}

?>
</body>
</html>
