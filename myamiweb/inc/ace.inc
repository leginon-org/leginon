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

function getAceViewerForm($name,$aceruns) {
	global $ACE;

	if (is_array($aceruns) && count($aceruns) > 1) {
		$runselect = 'or choose run: <select id="'.$name.'acerun">';
		$runselect.="<option value='-1'>all</option>";
		foreach ($aceruns as $run) {
			$runselect.="<option value='".$run['DEF_id']."'>".$run['name']."</option>";
		}
		$runselect.='</select>';
		$runselect.='<br/>';
	}

	$aceform='Best CTF estimation of ';
	$aceform.='<ul style="margin:0; list-style-type:none">';
	$aceform.='<select id="'.$name.'acemethod">';
	$aceform.="<option value='1'>all</option>";
	$aceform.="<option value='2'>ace1 only</option>";
	$aceform.="<option value='3'>ace2 only</option>";
	$aceform.="<option value='4'>ctffind only</option>";
	$aceform.='</select>';
	$aceform.=' method(s)';
	$aceform.='</ul>';
	$aceform.=$runselect;
	$aceform.='<br/>';
	$aceform.='Show ';
	$aceform.='<select id="'.$name.'aceparam">';
	$aceform.="<option value='3'>package diagnosis</option>";
	$aceform.="<option value='1'>2D power spec overlay</option>";
	$aceform.="<option value='2'>1D component fit graph</option>";
	$aceform.='</select>';
	$aceform.='<hr>';
	$aceform.='For ACE2 1D graph only ';
	$aceform.='<ul style="margin:0; list-style-type:none">';
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
	$aceform.='Graph Axis Scaling (0-1):<br>';
	$aceform.='x:<input type="text" id="'.$name.'xscale" size=3> ';
	$aceform.='y:<input type="text" id="'.$name.'yscale" size=3> ';
	$aceform.='</ul>';
	$aceform.='<input type="button" value="update" onclick=setAceParam(\''.$name.'\') />';
	return $aceform;
}
		
?>
