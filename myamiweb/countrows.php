<?php

#require_once "inc/mysql.inc";
require_once "config.php";

function countRows($database,$link){
	mysqli_select_db($link, $database);
	$tables = Array();
	$r = mysqli_query($link, "show tables");
	while($row = @mysqli_fetch_assoc($r)) {
		$tables[] = $row['Tables_in_'.$database];
	}
	$totrows=0;
	foreach ($tables as $table) {
		$r = mysqli_query($link, "SELECT count(*) as num FROM $table");
		$num_rows = @mysqli_fetch_assoc($r);
		$totrows=$totrows+$num_rows['num'];
	}
	return $totrows;
}

$apdbs = Array();
$link = @mysqli_connect($DB_HOST,$DB_USER,$DB_PASS);
$r = mysqli_query($link, "show databases");
while ($row = @mysqli_fetch_assoc($r)) {
	$db = $row['Database'];
	if (preg_match('/^ap/',$db)) {
		$apdbs[]=$db;
	}
}
$rows = countRows('dbemdata',$link);
echo "$rows rows in dbemdata<br>";
$rows = number_format($rows);
echo "<b>Total in leginon:</b> $rows<br>\n";
echo "<br>\n";
$aprows = 0;
foreach ($apdbs as $ap) {
	$rows = countRows($ap,$link);
	echo "$rows rows in $ap<br>";
	$aprows=$aprows+$rows;
}
$aprows = number_format($aprows);
echo "<b>Total in appion:</b> $aprows<br>\n";
?>
