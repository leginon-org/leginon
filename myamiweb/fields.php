<html>
<head>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
<link rel="stylesheet" type="text/css" href="css/view.css">
<title>Data</title>
<?php

require_once "config.php";
require_once "inc/mysql.inc";

$db = new mysql($DB_HOST, $DB_USER, $DB_PASS, $DB);

$q = "show tables";
$Rtables = $db->SQLQuery($q);

$data = array();
while ( $row = mysql_fetch_array($Rtables, MYSQL_ASSOC)) {
	$table = $row[Tables_in_dbemdata];
	$q = "show fields from $table";
	$Rfields = $db->SQLQuery($q);
	echo "<h3>$table</h3>";
	while ($fields=mysql_fetch_array($Rfields, MYSQL_ASSOC)) {
		if (!preg_match("%^REF\||^DEF_%",$fields[Field]))
			echo "$fields[Field] <br>";
	}
}
?>
<pre>
<?php
print_r($data);
?>
</pre>

