<?
require('inc/ctf.inc');
require('inc/util.inc');
require('inc/leginon.inc');
$ctf = new ctfdata();

$defaultId= 1766;
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;
$runId = $ctf->getLastCtfRun($sessionId);
$r = $ctf->getCtfInfo($sessionId, $runId);
foreach ($r as $row) {
	$id[] = $row['DEF_id'];
	$where[] = "DEF_id=".$row['DEF_id'];
}

$sessioninfo = $leginondata->getSessionInfo($sessionId);
$title = $sessioninfo[Name];

$fields = array('defocus1', 'defocus2', 'snr');
$stats = $ctf->getStats($fields, $sessionId, $runId);
?>
<html>
<head>
<title><?=$title?> CTF report</title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>
<body>
<?= divtitle("CTF Report $title Experiment"); ?>
<br>
<?
foreach($stats as  $field=>$data) {
		foreach($data as $k=>$v) {
			$imageId = $stats[$field][$k]['id'];
			$p = $leginondata->getPresetFromImageId($imageId);
			$stats[$field][$k]['preset'] = $p['name'];
			$cdf = '<br><a href="ctfgraph.php?hg=1&Id='.$sessionId
				.'&preset='.$p['name'].'&f='.$field.'&df='.$data[$k]['defocus_nominal'].'">'
				.'<img border="0" src="ctfgraph.php?w=400&hg=1&Id='.$sessionId
				.'&preset='.$p['name'].'&f='.$field.'&df='.$data[$k]['defocus_nominal'].'"></a>';
			$stats[$field][$k]['histogram'] = $cdf;
			$cdf = '<a href="ctfgraph.php?vd=1&Id='.$sessionId
				.'&preset='.$p['name'].'&f='.$field.'&df='.$data[$k]['defocus_nominal'].'">'
				.'[data]</a><br>';
			$cdf .= '<a href="ctfgraph.php?Id='.$sessionId
				.'&preset='.$p['name'].'&f='.$field.'&df='.$data[$k]['defocus_nominal'].'">'
				.'<img border="0" src="ctfgraph.php?w=400&Id='.$sessionId
				.'&preset='.$p['name'].'&f='.$field.'&df='.$data[$k]['defocus_nominal'].'"></a>';
			$stats[$field][$k]['graph'] = $cdf;
		}
}
$display_keys = array ('preset', 'defocus_nominal', 'nb', 'min', 'max', 'avg', 'stddev');
echo display_stats($stats, $display_keys);
echo "<br>";

$display_keys = array ('graph', 'histogram');
echo display_stats($stats, $display_keys);


?>
</body>
</html>
