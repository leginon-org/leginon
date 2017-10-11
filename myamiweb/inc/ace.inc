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

function getAceViewerForm($name, $aceruns) {
	global $ACE;

	if (is_array($aceruns) && count($aceruns) > 1) {
		$runselect = '<p>Choose run: <br/>';
		$runselect.='<select id="'.$name.'acerun">';
		$runselect.="<option value='-1'>all</option>";
		foreach ($aceruns as $run) {
			$runselect.="<option value='".$run['DEF_id']."'>".$run['name']."</option>";
		}
		$runselect.='</select>';
		$runselect.='</p>';
	}

	$aceform='<p>Choose method: <br/>';
	$aceform.='<select id="'.$name.'acemethod">';
	$aceform.="<option value='1'>all</option>";
	$aceform.="<option value='2'>ace1 only</option>";
	$aceform.="<option value='3'>ace2 only</option>";
	$aceform.="<option value='4'>ctffind only</option>";
	$aceform.='</select>';
	$aceform.='</p>';
	$aceform.=$runselect;
	$aceform.='<p>Choose graph: <br/>';
	$aceform.='<select id="'.$name.'aceparam">';
	$aceform.="<option value='1'>2D power spec overlay</option>";
	$aceform.="<option value='2'>1D component fit graph</option>";
	$aceform.="<option value='3'>2D from package</option>";
	$aceform.="<option value='4'>1D from package</option>";
	# local CTF
	$aceform.="<option value='5'>Local CTF plot</option>";

	$aceform.='</select>';
	$aceform.='</p>';
	$aceform.='<input type="button" value="update" onclick=setAceParam(\''.$name.'\') />';
	return $aceform;
}
		
?>
