<?php

$ACE['d1']='unnormalized power spectrum';
$ACE['d2']='normalized power spectrum';
$ACE['d3']='fitted CTF';
$ACE['d4']='fitted CTF power spectrum';

function readACENormFile($filename) {
	$acedata=array();
	if (file_exists($filename)) {
		$lines = file ($filename);
		foreach ($lines as $line) {
			list($index, $d1, $d2, $d3, $d4)=explode('	', $line);
			$acedata['d1'][]=trim($d1);
			$acedata['d2'][]=trim($d2);
			$acedata['d3'][]=trim($d3);
			$acedata['d4'][]=trim($d4);
		}
	}
	return $acedata;
}

function getAceViewerForm($name) {
	global $ACE;
	$aceform='ACE params';
	$aceform.='<ul style="margin:0; list-style-type:none">';
	$aceform.='<select id="'.$name.'aceparam">';
	$aceform.="<option value='1'>graph1</option>";
	$aceform.="<option value='2'>graph2</option>";
	$aceform.="<option value='3'>CtfFind</option>";
	$aceform.='</select>';
	$aceform.='<li>';
	$aceform.='<input type="checkbox" id="'.$name.'aceparam2">';
	$aceform.=$ACE['d1'];
	$aceform.='</li>';
	$aceform.='<li>';
	$aceform.='<input type="checkbox" id="'.$name.'aceparam3">';
	$aceform.=$ACE['d2'];
	$aceform.='</li>';
	$aceform.='<li>';
	$aceform.='<input type="checkbox" id="'.$name.'aceparam4">';
	$aceform.=$ACE['d3'];
	$aceform.='</li>';
	$aceform.='<li>';
	$aceform.='<input type="checkbox" id="'.$name.'aceparam5">';
	$aceform.=$ACE['d4'];
	$aceform.='</li>';
	$aceform.='</ul>';
	$aceform.='<input type="button" value="update" onclick=setAceParam(\''.$name.'\') />';
	return $aceform;
}
		
?>
