<?php
require_once('inc/project.inc.php');
require_once "inc/jpgraph.php";
require_once "inc/jpgraph_line.php";
require_once "inc/jpgraph_scatter.php";
require_once "inc/jpgraph_bar.php";
require_once "inc/histogram.inc";
require_once "inc/image.inc";

$title = "Statistics Report";
login_header($title);

$today = date("m/d/y");
project_header("Statistics Report - " . $today);
$link = mysqli_connect(DB_HOST, DB_USER, DB_PASS);
if (mysqli_connect_errno()) {
    die("Could not connect: " . mysqli_connect_error());
}

/* use leginon database */
mysqli_select_db($link, DB_LEGINON);


?>
		<h3>Number of Images Acquired by Machine:</h3>
		<table border="1"  cellpadding="5" cellspacing="0" width="100%">
			<tr><td><b>TEM</b></td><td><b>Camera</b></td><td><b>Hostname</b></td><td><b># Images</b></td></tr>
			<?php
			mysqli_select_db($link, DB_LEGINON);
			$q = "SELECT B.tem, B.camera, A.hostname, A.image_count
				FROM (
				SELECT i.hostname, c.image_count, cid
				FROM InstrumentData i
				LEFT JOIN (
				SELECT `REF|InstrumentData|ccdcamera` AS cid, count( * ) AS image_count
				FROM `CameraEMData`
				WHERE `align frames` =0
				GROUP BY `REF|InstrumentData|ccdcamera`
				)c ON i.`DEF_id` = c.cid
				WHERE c.image_count IS NOT NULL
				) AS A
				JOIN (
				SELECT i1.`name` tem, i2.`name` camera, i1.`hostname` , i2.`DEF_id`
				FROM `PixelSizeCalibrationData` p
				JOIN `InstrumentData` i1 ON p.`REF|InstrumentData|tem` = i1.`DEF_id`
				JOIN `InstrumentData` i2 ON p.`REF|InstrumentData|ccdcamera` = i2.`DEF_id`
				WHERE i1.`name` not like 'SIM%' and i2.`name` not like 'SIM%'
				GROUP BY `REF|InstrumentData|ccdcamera`
				) AS B ON B.DEF_id = A.cid order by A.`image_count` DESC";
			$r = mysqli_query($link, $q) or die("Query error: " . mysqli_error($link));
			while ($row =  mysqli_fetch_row($r))
			{
				echo "<tr><td>$row[0]</td><td>$row[1]</td><td>$row[2]</td><td>$row[3]</td></tr>";
			}
	?>		</table>
