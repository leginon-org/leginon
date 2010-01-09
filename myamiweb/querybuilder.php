<?php
require "config.php";
$proc=(@require "config_processing.php") ? true : false;
require "inc/mysql.inc";
$databases[]=$DB;
#if ($proc)
#	$databases[]=$PROCESSING_DB;
$databases[]="ap172";

$s_db=($_POST['s_db']) ? $_POST['s_db'] : $DB;
$dbchanged=($s_db==$_POST['db_memo']) ? false : true;

$dbc=new mysql($DB_HOST, $DB_USER, $DB_PASS, $s_db);
$tables = $dbc->getTables();

$table = (!empty($_POST['table'])) ? $_POST['table'] : $tables[0];
$tablealias = (!empty($_POST[$table.'alias'])) ? $_POST[$table.'alias'] : $table;
$condition = stripslashes($_POST['condition']);

$formatedfields = (!empty($_POST['sqlfields'])) ? array($_POST['sqlfields']) : array();
$formatedtables = (!empty($_POST['sqltables'])) ? array($_POST['sqltables']) : array();
$formatedjoins = (!empty($_POST['sqljoins'])) ? array($_POST['sqljoins']) : array();

if ($_POST['addselectedfield']) {
	foreach ($_POST['fields'] as $f)
		$condition .= formatField($tablealias,$f)."\n";
}
if ($_POST['clearselectedfield']) {
	$condition = "";
}

if ($_POST['reset']) {
	$table = $tables[0];
	$tablealias = $table;
	$formatedfields = array();
	$formatedtables = array();
	$formatedjoins = array();
	$condition = "";
}

if ($dbchanged) {
	$table = $tables[0];
  $tablealias = $table;
}


$fields = $dbc->getFields($table);

$crlf = "<br />";
?>
<html>
<head>
<title>Query Builder</title>
<link rel="stylesheet" href="css/viewer.css" type="text/css" /> 
<link rel="stylesheet" href="css/view.css" type="text/css" /> 
</head>
<body>
<h3>Query Builder</h3>




<form name="data" method="POST" enctype="multipart/form-data" action="<?php echo $_SERVER['PHP_SELF']; ?>">
<input type="hidden" name="db_memo" value="<?=$s_db?>" />
<select name="s_db" onChange="document.data.submit()">
<?
foreach($databases as $db) {
	$s = ($db==$_POST['s_db']) ? 'selected' : '';
	echo '<option '.$s.'>'.$db.'</option>'."\n";
}
?>
</select>
<?
if ($dbchanged) {
	echo "<font color='red'>DB changed &raquo; $s_db </font><br />";
}
?>	
<table border="0">
<tr>
<td>
	Tables
</td>
<td>
	Fields
</td>
<td>
	References	
</td>
<td>
	Conditions	
</td>
</tr>
<tr valign="top">
<td>
<select name="table" onChange="data.submit()">
	<?php
	foreach ($tables as $t) { 
		if ($t==$table) {
			$selected = "selected";
		} else {
			$selected = "";
		}
		$selected = ($t==$table) ? "selected" : "";
		echo "<option value='$t' $selected >$t</option>\n";
	}
	if ($_POST['addtables'])
		$formatedtables[] = formatTable($table, $tablealias);
	if ($_POST['cleartables'])
		$formatedtables= array();
	$sqltables = implode(', ',$formatedtables);
	?>
</select><br />

Alias: <input class="field" type="text" name="<?php echo $table."alias"; ?>" value="<?php echo $tablealias; ?>"></input>

<br>
<input class="button" type="submit" name="cleartables" value="Clear">
<input class="button" type="submit" name="addtables" value="Add">
</td>
<td>
<select multiple name="fields[]" size="10" >
	<?php foreach ($fields as $field) {
		if (in_array($field, (array)$_POST['fields'])) {
			$selectedfields[] = $field;
			$s = 'selected';
		} else {
			$s = '';
		}
		echo "<option value='".$field."' $s >".$field."</option>\n";
	}
	if ($_POST['addfields'])
		foreach ($selectedfields as $sf) {
			$formatedfields[] = formatField($tablealias, $sf);
		}
	if ($_POST['clearfields'])
		$formatedfields= array();
	$sqlfields = implode(', ',$formatedfields);
?>
</select><br>
<input class="button" type="submit" name="clearfields" value="Clear">
<input class="button" type="submit" name="addfields" value="Add">
</td>
<td>
<select multiple name="joins[]" size="10" >
<?php
	foreach ($fields as $field) {
		if (!ereg('^REF', $field))
			continue;
		$currentjoins[] = $field;
		if (in_array($field, (array)$_POST['joins'])) {
			$selectedjoins[] = $field;
			$s = 'selected';
		} else {
			$s = '';
		}
		echo "<option value='".$field."' $s >".$field."</option>\n";
	}
?>
</select>
<br>
<?php if ($currentjoins) {
echo "Aliases: <br>";
	foreach ($currentjoins as $ref) {
		$reftable = getRefTable($ref);
		$alias = "alias$ref";
		$value = ($_POST[$alias]) ? $_POST[$alias] : $reftable;
		echo "$reftable:<input class='field' type='text' name='$alias' value='$value'><br>";
		if ($_POST['addjoins'] && $selectedjoins && in_array($ref, $selectedjoins))
			$formatedjoins[] = formatJoin($reftable, $value, 'DEF_id', $tablealias, $ref);
	}
}
	if ($_POST['clearjoins'])
		$formatedjoins = array();
	$sqljoins = implode($crlf, $formatedjoins);
?>
<br>
<input class="button" type="submit" name="clearjoins" value="Clear">
<input class="button" type="submit" name="addjoins" value="Add">
</td>
<td>
	<textarea class="textarea" name="condition" cols="40" rows="8"><?php echo $condition; ?></textarea>
<br>
<input class="button" type="submit" name="addselectedfield" value="Add Field">
<input class="button" type="submit" name="clearselectedfield" value="Clear">

</td>
</tr>
<tr>
<td>
<input class="button" type="submit" name="update" value="Update">
<input class="button" type="submit" name="reset" value="Reset">
</td>
</tr>
</table>
<input type="hidden" name="sqlfields" value="<?php echo $sqlfields; ?>">
<input type="hidden" name="sqltables" value="<?php echo $sqltables; ?>">
<input type="hidden" name="sqljoins" value="<?php echo $sqljoins; ?>">
</form>
<?php

function addquotes($string) {
	return '`'.$string.'`';
}

function getRefTable($field) {
	$split = explode('|', $field);
	return $split[1];
}

function formatField($tablealias, $field) {
	return addquotes($tablealias).".".addquotes($field);
}

function formatTable($table, $alias) {
	return addquotes($table)." AS ".addquotes($alias);
}


function formatJoin($reftable, $refalias, $reffield, $tablealias, $field) {
	global $crlf;
	return "LEFT JOIN ".formatTable($reftable, $refalias).$crlf
		."ON (".formatField($refalias, $reffield)."=".formatField($tablealias, $field).") ";
}
?>
<hr>
<h4>SQL:</h4>
<?php
$sqlcondition = ($condition) ? ereg_replace("\n", $crlf, $condition).$crlf : "";
if ($sqltables)
	$sqltables.=$crlf;
if ($sqljoins)
	$sqljoins.=$crlf;
$query = "SELECT ".$crlf
	.$sqlfields.$crlf
	."FROM".$crlf
	.$sqltables
	.$sqljoins
	.$sqlcondition;
echo $query;
?>
<hr>
<h4>PHP:</h4>
<?php
$phpq = ereg_replace('^', '$q="', $query);
$phpq = ereg_replace($crlf.'$', '";', $phpq);
$phpq = ereg_replace($crlf, ' "'.$crlf.'	."', $phpq);
echo $phpq;
?>
</body>
</html>
