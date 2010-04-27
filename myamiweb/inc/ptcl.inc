<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once('inc/leginon.inc');
require_once('inc/mysql.inc');


class particledata_a {

	var $crlf = "\n";

	function particledata_a() {
		$this->mysql = new mysql(
					DB_HOST,
					DB_USER,
					DB_PASS,
					PARTICLE_DB);
	}

	function getSelections($sessionId="") {
		$sqlwhere = ($sessionId) ? " where `SessionId`='$sessionId'" : "";
		$q = "select * from `selection` ".$sqlwhere;
		return $this->mysql->getSQLResult($q);
	}

	function getId($fields=array(), $table, $id ) {
		$acq_fields = $this->mysql->getFields($table); 
		$where = array();
		
		foreach ($fields as $k=>$f) {
			if (!in_array($k, $acq_fields))
				return false;
			$where[] = "`$k`='".addslashes($f)."'";
		}
		if (empty($where))
			return false;
		$wherestr = implode(' and ', $where);
		$q = 'select `'.$id.'` as id from `'.$table.'`'
			.' where '.$wherestr;
		$ids = $this->mysql->getSQLResult($q);
		if (count($ids[0])==1)
			return $ids[0]['id'];
		else
			return $ids;
	}

	function getParticlesFromFilename($filename) {
		$q = "select p.Xcoord, p.Ycoord "
			."from image i "
			."left join particle p on (i.imageId = p.imageId ) "
			."where i.ImageName= '".$filename."' "
			."";
		return $this->mysql->getSQLResult($q);
	}

	function getParticlesFromSelectionId($selectionId, $filename) {
		$q = "select p.Xcoord, p.Ycoord, p.Boxsize "
			."from image i "
			."left join particle p on (i.imageId = p.imageId ) "
			."where i.ImageName= '".$filename."' "
			."and p.selectionId=$selectionId";
		return $this->mysql->getSQLResult($q);
	}

}

function string2selections($string) {
	/* "(id1, color1, target1),(id2, color2, target2),(...)" 
		=>
		array(
			array(id1, color1, target1),
			array(id2, color2, target2),
			array(...)
		)
	*/ 
	$selections = array();
	preg_match_all('|\((.*)\)|U', $string, $m);
	$s = $m[1];
	foreach ($s as $selection)
		$selections[] = explode(',',$selection);	
	return $selections;
}

function ptcl_header($javascriptinit="") {


$link = new iconlink();
$link->align = 'center';
$link->cols = 1;
$link->onimg = "_on.png";
$link->offimg = "_off.png";
$link->setImagePath('img/');
$link->addlink('addptclselect.php','Selection','', '', '');


?>

<html>
<head>
<title>Particle Tools</title>
<link rel="stylesheet" href="css/viewer.css" type="text/css" /> 
<script src="js/dataform.js"></script>
</head>
<body Background='img/background.jpg' leftmargin="0" topmargin="5" marginwidth="0" marginheight="5" alink="#00CCCC" vlink="#006699" link="#006699" <?php echo $javascriptinit; ?>>

<center><h1>Particle Tools</h1></center>
<hr/>
<table border=0>
<tr valign="top">
<td width=100>
<?php $link->Display(); ?>
</td>
<td>
<?php
}

function ptcl_footer() {
	echo "
 	 </td>
	</tr>
    </body>
</html>
";
}

function mysql2UnixTime($mysqltime) {
	$year = substr($mysqltime, 0,4);
	$month  = substr($mysqltime, 4,2);
	$day = substr($mysqltime, 6,2);
	$hour = substr($mysqltime, 8,2);
	$minute = substr($mysqltime, 10,2);
	$second = substr($mysqltime, 12,2);
	return mktime($hour, $minute, $second, $month, $day, $year);
}

function display($r, $display_fields=False) {
	echo "<table border=1 cellspacing=0, cellpadding=5>";
	if (!is_array($r))
		return False;
	$data = $r;
	if ($display_fields) {
		if ($r[0]) {
			$fields = array_keys($r[0]);
			foreach ($fields as $field)
				$f[$field] = $field;
			$data = array_merge(array($f), $r);
		}
	}
	foreach ($data as $row) {
	echo "<tr>";
		foreach ($row as $k=>$value) {
			if (eregi('^DEF_id|^REF\|', $k)) 
				continue;
			else if (eregi('^DEF_timestamp$', $k)) {
				if (!$display_fields)
					$value = date('D, j M Y G:i:s ', mysql2UnixTime($value));
				$display_fields = False;
			}
			echo "	<td>$value</td>\n";
		}
	echo "</tr>";
	}
	echo "</table>";
}
?>
