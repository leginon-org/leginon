<?php
require "inc/particledata.inc";
require "inc/util.inc";
require "inc/leginon.inc";

$sessionId= $_GET['Id'];
$runId = $_GET'[rId'];
//$runId = 76;
$particle = new particledata();

?>

<html>
<head>
<title>Mask Maker Run Report</title>
<link rel="stylesheet" type="text/css" href="../css/viewer.css">
</head>
<body>

<?php
list($runparams) = $particle->getMaskMakerParams($runId);
echo divtitle("Mask Maker report for $runparams[name]");

$regionstats = $particle->getMaskRegionStats($runId);
echo "<br><table cellspacing='1' cellpadding='2'><tr><td><span class='datafield0'>Total regions for $runparams[name]: </span></td><td>$regionstats[totregions]</td></tr></table>\n";

//Report maskmaker run parameters
$keys = array_keys($runparams);
echo "<h4>mask creation parameters</h4>";
echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'>\n";
$selection_fields = $keys;
foreach($selection_fields as $key) {
	$value = $runparams[$key];
	if ($key != 'DEF_id' and $key != 'DEF_timestamp' and gettype($value) != 'NULL') {
		if ($key == 'REF|leginondata|SessionData|session') $key = 'session';
	echo "<tr>\n";
		echo "<td><span class='datafield0'>$key</span></td>";
		echo "<td>$value</td>";
	echo "</tr>\n";}
}
echo "</table>\n";


?>
</body>
</html>
