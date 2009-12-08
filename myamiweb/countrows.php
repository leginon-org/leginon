<?

function countRows($database){
	$link = mysql_connect("localhost","usr_object");
	mysql_select_db($database,$link);

	$tables = Array();
	$r = mysql_query("show tables");
	while($row = @mysql_fetch_assoc($r)) {
		$tables[] = $row['Tables_in_'.$database];
	}
	$totrows=0;
	foreach ($tables as $table) {
		$result = mysql_query("SELECT * FROM $table", $link);
		$num_rows = mysql_num_rows($result);
		#echo "$num_rows Rows in $table<br >\n";
		$totrows=$totrows+$num_rows;
	}
	return $totrows;
}

$link = mysql_connect("localhost","usr_object");
$apdbs = Array();
$r = mysql_query("show databases");
while ($row = @mysql_fetch_assoc($r)) {
	$db = $row['Database'];
	if (preg_match('/^ap/',$db)) {
		$apdbs[]=$db;
	}
}

$rows = countRows('dbemdata');
echo "$rows rows in dbemdata<br>";
echo "<b>Total in leginon:</b> $rows<br>\n";
echo "<br>\n";
$aprows = 0;
foreach ($apdbs as $ap) {
	$rows = countRows($ap);
	echo "$rows rows in $ap<br>";
	$aprows=$aprows+$rows;
}
echo "<b>Total in appion:</b> $aprows<br>\n";
?>
