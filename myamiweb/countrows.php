<?

#require_once "inc/mysql.inc";
require_once "config.php";

function countRows($database,$link){
	mysql_select_db($database,$link);
	$tables = Array();
	$r = mysql_query("show tables");
	while($row = @mysql_fetch_assoc($r)) {
		$tables[] = $row['Tables_in_'.$database];
	}
	$totrows=0;
	foreach ($tables as $table) {
		$r = mysql_query("SELECT * FROM $table", $link);
		$num_rows = mysql_num_rows($r);
		$totrows=$totrows+$num_rows;
	}
	return $totrows;
}

$apdbs = Array();
$link = @mysql_connect($DB_HOST,$DB_USER,$DB_PASS);
$r = mysql_query("show databases");
while ($row = @mysql_fetch_assoc($r)) {
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
