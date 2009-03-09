<?php
require "inc/particledata.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/project.inc";

$expId= $_GET['expId'];
$runId = $_GET['rId'];
$particle = new particledata();

processing_header('Mask Maker Run Report','Mask Maker Run Report');

list($runparams) = $particle->getMaskMakerParams($runId);
echo apdivtitle("Mask Maker report for $runparams[name]");

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

processing_footer();
?>
