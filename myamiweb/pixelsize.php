<?php
#require "inc/leginon.inc";
require "inc/admin.inc";

$dbc=$leginondata->mysql;
$q="
 select count(magnification) `nb`, min(pi.DEF_timestamp) `from` , max(pi.DEF_timestamp) `to`, to_days(max(pi.DEF_timestamp)) - to_days(min(pi.DEF_timestamp)) `days`, ic.name, i.hostname, pi.magnification, format(avg(pi.pixelsize)/1e-6, 5) `mean`, format(min(pi.pixelsize)/1e-6, 5) `min`, format(max(pi.pixelsize)/1e-6, 5) `max`, format(stddev(pi.pixelsize)/1e-6, 5) `stdev` from PixelSizeCalibrationData pi left join InstrumentData i on (i.`DEF_id`=pi.`REF|InstrumentData|tem`) left join InstrumentData ic on (ic.`DEF_id`=pi.`REF|InstrumentData|ccdcamera`) where i.DEF_id in (20,24,56) group by `REF|InstrumentData|ccdcamera`, magnification;
";
$q='
select
concat(i.hostname,"-",ic.name) as instrument, 
pi.magnification,
pi.DEF_timestamp `timestamp`,
pi.pixelsize
from PixelSizeCalibrationData pi left join InstrumentData i on (i.`DEF_id`=pi.`REF|InstrumentData|tem`) left join InstrumentData ic on (ic.`DEF_id`=pi.`REF|InstrumentData|ccdcamera`) where i.DEF_id in (20,24,56) and ic.DEF_id in (21, 25, 57) order by pi.magnification, pi.DEF_timestamp desc; 
';
$r=$dbc->getSQLResult($q);
$data=array();
foreach ($r as $row) {
	$instrument=$row['instrument'];
	$mag=$row['magnification'];
	$timestamp=$row['timestamp'];
	$pixelsize=$row['pixelsize'];
#	$pixelsize=format_sci_number($pixelsize, 4);
	if ($mag>9000) {
		$pixelsize=format_nano_number($pixelsize);
	} else {
		$pixelsize=format_micro_number($pixelsize);
	}
	$data[$instrument][$mag]['mag']=$mag;
	$data[$instrument][$mag][$timestamp]=$pixelsize;
}
admin_header();
echo "<h2>Pixelsize Calibration history</h2>";
$instruments=array_keys($data);
echo "<h3>Instruments</h3>";
echo "<ol>";
foreach ($instruments as $instrument) {
	echo '<li><a href="#'.$instrument.'">'.$instrument."</a></li>\n";
}
echo "</ol>";
foreach ($data as $instrument=>$d) {
	echo "<h3><a name='$instrument'></a>$instrument</h3>\n";
	echo"<div style='font-size: 10px'>";
	foreach ($d as $arr) {
		echo"<p style='font-size: 10px'>";
		echo array2table(array($arr), array(), true);
		echo "</p>";
	}
	echo "</div>";
	
}
?>
