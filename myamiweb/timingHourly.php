<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";
?>

<style>
#content
{
	width: 900px;
	margin: 0 auto;
	font-family:Arial, Helvetica, sans-serif;
}
.page
{
	float: right;
	margin: 0;
	padding: 0;
}
.page li
{
	list-style: none;
	display:inline-block;
}
.page li a, .current
{
	display: block;
	padding: 5px;
	text-decoration: none;
	color: #8A8A8A;
}
.current
{
	font-weight:bold;
	color: #000;
}

</style>
<?php

login_header('Image Collection Timing Statistics per Hour', '', '');

if (privilege('groups') < 3 ){
	echo "Permission Denied";
	exit;
}
?>
<br>
<div id="content">
<h1>Image Collection Timing Statistics</h1>

<p>The following table lists how many high magnification images (preset en or enn) do we collect per hour (on average and max and min). </p>
 
<table>
<tr>

<?php

if (isset($_GET["page"])) { $page  = $_GET["page"]; } else { $page=1; };
if (isset($_GET["limit"])) { $page  = $_GET["limit"]; } else { $limit=20; };
$scopes = $leginondata->getScopesForSelection();


$krios1ScopeID = 44;
$krios2ScopeID = 77;
$krios3ScopeID = 84;

$start = ($page - 1) * $limit;
$combinedData = array();
$krios1Sessions = $leginondata->getSessions('description', false, '', $krios1ScopeID);
$krios2Sessions = $leginondata->getSessions('description', false, '', $krios2ScopeID);
$krios3Sessions = $leginondata->getSessions('description', false, '', $krios3ScopeID);

$krios1SessionsCount = count($krios1Sessions);
$krios2SessionsCount = count($krios2Sessions);
$krios3SessionsCount = count($krios3Sessions);

$maxSessionsCount = max($krios1SessionsCount, $krios2SessionsCount, $krios2SessionsCount);

$total_pages = ceil($maxSessionsCount/$limit);

if ($start+$limit < $krios1SessionsCount){
	echo "<th>Krios 1</th><table>
	<tr>
	<th>Session ID</th>
	<th>Preset</th>
	<th>#Images</th>
	<th>Average</th>
	<th>Max</th>
	<th>Min</th>
	</tr>";
	for ($i = $start; $i < $start+$limit; $i++) {
		$session = $krios1Sessions[$i];
	
		$presets = $leginondata->getDataTypes($session['id']);
		$presets = array_reverse($presets);
		foreach ($presets as $preset) {
			if (!$preset)
				continue;
			if ($preset != 'en' and $preset != 'enn' and $preset != 'esn')
				continue;
			$timings = $leginondata->getTiming($session['id'], $preset);
			//if (count($timings) < 100) continue;
			$data = array(); 
			global $combinedData;
			foreach ($timings as $time) {
				$data[] = intval($time['unix_timestamp']/3600);
				$combinedData[] = intval($time['unix_timestamp']/3600);
			} 
			$array = array_count_values($data);
			$average = array_sum($array) / count($array);
			echo "<tr><td>".$session['name_org']."</td>";
			echo "<td>".$preset."</td>";
			echo "<td>".count($timings)."</td>";
			echo "<td>".round($average)."</td>";
			echo "<td>".max($array)."</td>";
			echo "<td>".min($array)."</td></tr>";
		}		
	}
	echo "</table>";
}
if ($start+$limit < $krios2SessionsCount){
	echo "<th>Krios 2</th><table>
	<tr>
	<th>Session ID</th>
	<th>Preset</th>
	<th>#Images</th>
	<th>Average</th>
	<th>Max</th>
	<th>Min</th>
	</tr>";
	for ($i = $start; $i < $start+$limit; $i++) {
		$session = $krios2Sessions[$i];

		$presets = $leginondata->getDataTypes($session['id']);
		$presets = array_reverse($presets);
		foreach ($presets as $preset) {
			if (!$preset)
				continue;
				if ($preset != 'en' and $preset != 'enn' and $preset != 'esn')
					continue;
					$timings = $leginondata->getTiming($session['id'], $preset);
					//if (count($timings) < 100) continue;
					$data = array();
					global $combinedData;
					foreach ($timings as $time) {
						$data[] = intval($time['unix_timestamp']/3600);
						$combinedData[] = intval($time['unix_timestamp']/3600);
					}
					$array = array_count_values($data);
					$average = array_sum($array) / count($array);
					echo "<tr><td>".$session['name_org']."</td>";
					echo "<td>".$preset."</td>";
					echo "<td>".count($timings)."</td>";
					echo "<td>".round($average)."</td>";
					echo "<td>".max($array)."</td>";
					echo "<td>".min($array)."</td></tr>";
		}
	}
	echo "</table>";
}
if ($start+$limit < $krios3SessionsCount){
	echo "<th>Krios 3</th><table>
	<tr>
	<th>Session ID</th>
	<th>Preset</th>
	<th>#Images</th>
	<th>Average</th>
	<th>Max</th>
	<th>Min</th>
	</tr>";
	for ($i = $start; $i < $start+$limit; $i++) {
		$session = $krios3Sessions[$i];

		$presets = $leginondata->getDataTypes($session['id']);
		$presets = array_reverse($presets);
		foreach ($presets as $preset) {
			if (!$preset)
				continue;
				if ($preset != 'en' and $preset != 'enn' and $preset != 'esn')
					continue;
					$timings = $leginondata->getTiming($session['id'], $preset);
					//if (count($timings) < 100) continue;
					$data = array();
					global $combinedData;
					foreach ($timings as $time) {
						$data[] = intval($time['unix_timestamp']/3600);
						$combinedData[] = intval($time['unix_timestamp']/3600);
					}
					$array = array_count_values($data);
					$average = array_sum($array) / count($array);
					echo "<tr><td>".$session['name_org']."</td>";
					echo "<td>".$preset."</td>";
					echo "<td>".count($timings)."</td>";
					echo "<td>".round($average)."</td>";
					echo "<td>".max($array)."</td>";
					echo "<td>".min($array)."</td></tr>";
		}
	}
	echo "</table>";
}
echo "</tr>
	</table>";

$combinedArray = array_count_values($combinedData);
$average = array_sum($combinedArray) / count($combinedArray);
echo "<p>Combined statistics below is a result of combining number of all high magnification images (preset en or enn) across all sessions per hour (3600 seconds) of data collection.</p>
		<p>Combined Average: ".round($average).'<br>Combined Max: '.max($combinedArray).'<br>Combined Min: '.min($combinedArray)."</p>";


echo "<ul class='page'>";
for($i=1;$i<=$total_pages;$i++)
{
	if($i==$page) { echo "<li class='current'>".$i."</li>"; }

	else { echo "<li><a href='?page=".$i."'>".$i."</a></li>"; }
}
echo "</ul>";

?>

</div>
</body>
</html>
