<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";

login_header('Image Collection Timing Statistics per Hour', '', '');

if (privilege('groups') < 3 ){
	echo "Permission Denied";
	exit;
}
?>
<br>
<h1>Image Collection Timing Statistics</h1>

<p>The following table lists how many high magnification images (en or enn) do we collect per hour (on average and max and min). </p>
 
<table>
  <tr>
    <th>Session ID</th>
    <th>Preset</th>
    <th>Average</th>
    <th>Max</th>
    <th>Min</th>
  </tr>
  
<?php
$scopes = $leginondata->getScopesForSelection();
$scopeId = (empty($scopeId)) ? false:$scopeId;

$sessions = $leginondata->getSessions('description', false, '', $scopeId);
for ($i = 1; $i <= 100; $i++) {
	$session = $sessions[$i];

	echo "<tr><td>".$session['name_org']."</td>";
	$presets = $leginondata->getDataTypes($session['id']);
	$presets = array_reverse($presets);
	foreach ($presets as $preset) {
		if (!$preset)
			continue;
		if ($preset != 'en' and $preset != 'enn')
			continue;
		echo "<td>".$preset."</td>";
		$timings = $leginondata->getTiming($session['id'], $preset);
		$data = array(); 
		foreach ($timings as $time) {
			$data[] = intval($time['unix_timestamp']/ 3600);
		} 
		$array = array_count_values($data);
		$average = array_sum($array) / count($array);
		echo "<td>".round($average)."</td>";
		echo "<td>".max($array)."</td>";
		echo "<td>".min($array)."</td></tr>";
	}
}
?>
</table>
</body>
</html>
