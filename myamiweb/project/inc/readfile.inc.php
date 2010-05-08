<?
function readtxtfile ($file) {
	$delimiter = "\t";
	if (!is_readable($file) || !($fp = fopen($file, 'r')))
		return false;

	$fields = array();
	$data = array();
	$fieldsline = fgets($fp);
	$fieldsline = rtrim($fieldsline);
	$fields = explode($delimiter, $fieldsline);
	while ($dataline = fgets($fp)) {
		$nrow = array();
		$dataline = rtrim($dataline);
		$row  = explode($delimiter, $dataline);
		for ($i=0; $i<count($fields); $i++)
			$nrow[trim($fields[$i])] = trim($row[$i]);
		$data[] = $nrow;
	}
	fclose($fp);
	return array('fields' => $fields, 'data' => $data);
}

function label2sqlfields($labels) {
	if (!is_array($labels) || empty($labels))
		return false;

	$sqlfields = '(';
	$labels = addBackquotes($labels);
	$sqlfields .= implode(', ',$labels);
	$sqlfields .= ')';
	return $sqlfields;
}

function data2sqlvalues($data) {
	if (!is_array($data) || empty($data))
		return false;

	foreach ($data as $k=>$d ) {
		$data[$k] = "'".addslashes(formatstring($d))."'";
	}
	$sqlvalues = '(';
	$sqlvalues .= implode(', ',$data);
	$sqlvalues .= ')';
	return $sqlvalues;
}

function formatstring($string) {
	$match1 = ereg('(^")(.*)("$)', $string);	
	$match2 = ereg('(^\')(.*)(\'$)', $string);	
	if ($match1 || $match2)
		$string = ereg_replace('(^"|^\'|\'$|"$)', '', $string);	
	return trim($string);
}

function addBackquotes($field) {
	if (!is_array($field))
		return '`'.trim($field).'`';

	$formatedfield = array();
	foreach($field as $f)
		$formatedfield[] = '`'.trim($f).'`';

	return $formatedfield;
}

function getsqlinsert($table, $data) {
	if (!$table)
		return false;
	if (!$sqlfields = label2sqlfields(array_keys($data)))
		return false;
	if (!$sqldata = data2sqlvalues($data))
		return false;

	return "INSERT INTO ".addBackquotes($table)." ".$sqlfields." VALUES  ".$sqldata.";";
}
?>
