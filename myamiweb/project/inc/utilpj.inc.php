<?php
if (!function_exists("divtitle")) {
function divtitle($title, $option="") {
	$htmlstr = '
	<div style="padding: 4px; border: 1px solid black; background-color:#CCCCFF">
	'.$option.'<b>'.$title.'</b> 
	</div>
	';
	return $htmlstr;
}
}

function display_data_table($data, $columns=array(), $display_header=false) {
	$fields = ($columns) ? $columns : array_keys($data);
	$html = '<table class="tableborder" border="1" >';
	if ($display_header) {
		$html .= "<tr>\n";
		foreach ($fields as $label=>$field ) {
			$l = (is_string($label)) ? $label : $field;
			$html .= "<td><b>" .$l."</b></td>";
		}
		$html .= "</tr>\n";
	}
	$html .= "<tr>\n";
	foreach ($fields as $field) {
		$html .= "<td>"
		.$data[$field]
		."</td>";
	}
	$html .= "</tr>\n";
	$html .= "</table>";
	return $html;
}

//----------------------------------------------------------------------------------------------------------
// return an HTML formatted table.
//
// $projectId - if defined, adds the numeric $projectId to the path supplied for sorting the table based 
// 	on a column clicked on by a user. This field was added for issue #1279.
//----------------------------------------------------------------------------------------------------------
function data2table($data, $columns=array(), $display_header=false, $tableoption="class='tableborder' border='1' cellpadding='5'", $projectId=false) {
	$fields = ($columns) ? $columns : array_keys((array)$data[0]);
	$html = "<table $tableoption >";
	if ($display_header) {
		$html .= "<tr bgcolor='#cccccc'>\n";
		$option="";
		foreach ($fields as $field=>$label) {
			$l = (is_string($label)) ? $label : $field;
			if ($projectId) {
				$html .= "<td><a href='$PHP_SELF?projectId=$projectId&sort=$field'><b>".$l."</b></a></td>";
			} else {	
				$html .= "<td><a href='$PHP_SELF?sort=$field'><b>".$l."</b></a></td>";
			}
		}
		$html .= "</tr>\n";
	}
	foreach ((array)$data as $n=>$row) {
		$html .= "<tr>\n";
		foreach ($fields as $k=>$v) {
			$field = is_numeric($k) ? $v : $k;
			if (is_array($row[$field])) {
				$l=$row[$field][0];
				$option=" ".$row[$field][1]." ";
			} else {
				$l=$row[$field];
				$option="";
			}
			$html .= "<td>"
			.$l
			."</td>";
		}
		$html .= "</tr>\n";
	}
	$html .= "</table>";
	return $html;
}

function data2str($data, $columns=array()) {
	$fields = ($columns) ? $columns : array_keys((array)$data[0]);
	$str = "";
	if ($display_header) {
	}
	foreach ((array)$data as $n=>$row) {
		foreach ($fields as $k=>$v) {
			$field = is_numeric($k) ? $v : $k;
			if (is_array($row[$field])) {
				$l=$row[$field][0];
				$option=" ".$row[$field][1]." ";
			} else {
				$l=$row[$field];
				$option="";
			}
			$str .= $l ."\n";
		}
		$str.= "\n";
	}
	return $str;
}

function edit_menu($links=array(), $display_label=true, $display_icon=true) {
	$menu=array();
	foreach ($links as $label=>$link) {
		$l = "<a class='header' href='$link'>";
		if ($display_label)
			$l .= "&lt;$label&gt;";
		if ($display_icon) {
			if ($label=='new') {
				$l .= "<img alt='new' border='0' src='img/new.png'>";
			}
			if ($label=='edit') {
				$l .= "<img alt='edit' border='0' src='img/edit.png'>";
			}
			if ($label=='delete') {
				$l .= "<img alt='delete' border='0' src='img/btn-trash.png'>";
			}
		}
		$l .= "</a>";
		$menu[] = $l;
	}
	return join(' ', $menu);
}

function display_data_rows($data) {
	if(!is_array($data))
		return;
	$html = "<table class='tableborder' border='1' >";
	foreach ($data as $rows) {
		$html .= "<tr>\n";
		foreach ($rows as $row) {
			$html .= "<td>";
			$html .= $row;
			$html .= "</td>\n";
		}
		$html .= "</tr>\n";
	}
	$html .= "</table>\n";
	return $html;
}

function from_POST_values($args=array()) {
	$r = array();
	$keys=array_keys($_POST);
	foreach($args as $arg) {
		if (in_array($arg,$keys))
			$r[$arg]=$_POST[$arg];
	}
	return $r;
}

?>
