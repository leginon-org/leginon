<?php

require_once('tomography.php');

//header("Content-Type: text/plain");
$tiltSeriesId = $_GET['tiltSeriesId'];
$tiltSeriesNumber = $_GET['tiltSeriesNumber'];
$alabel = $_GET['alignlabel'];
//Use the following to combine two half tilt series separated by 5
#$numbers = array($tiltSeriesId-5,$tiltSeriesId);
$numbers = array($tiltSeriesId);
foreach ($numbers as $tiltSeriesId) {
	$session = $tomography->getTiltSeriesSession($tiltSeriesId);
	$results = $tomography->getTiltSeriesData($tiltSeriesId,$excludeAligned=empty($alabel), $alabel);
	$n_results = count($results);
	$first_imageid = $results[0]["imageId"];
	$parents = $tomography->getImageParent($first_imageid);
	while ($parents[0]['parentId']) {
		$lastparents = $parents;
		$parents = $tomography->getImageParent($parents[0]['parentId']);
	}
	$atlas_name = $tomography->getAtlasName($lastparents[0]['parentId']);

	# look for start of each tilt series
	$threshold = 0.05;
	if($n_results > 2) {
    for($i = 1; $i < $n_results; $i++) {
			$diff = abs($results[$i]['alpha'] - $results[$i - 1]['alpha']);
			if($diff < $threshold) {
        if($i + 1 < $n_results - 1) {
            $d_id1 = abs($results[$i]['id'] - $results[$i + 1]['id']);
            $d_id2 = abs($results[$i - 1]['id'] - $results[$i + 1]['id']);
            if($d_id1 > $id_id2) {
                $temp = $results[$i];
                $results[$i] = $results[$i - 1];
                $results[$i - 1] = $temp;
            }
        } else {
            $d_id1 = abs($results[$i]['id'] - $results[$i - 2]['id']);
            $d_id2 = abs($results[$i - 1]['id'] - $results[$i - 2]['id']);
            if($d_id1 < $id_id2) {
                $temp = $results[$i];
                $results[$i] = $results[$i - 1];
                $results[$i - 1] = $temp;
            }
        }
        break;
			}
    }
	}
}
// for debugging
/*
foreach($results as $result) {
    $filename = $session['image path'].'/'.$result['filename'].'.mrc';
		echo $filename.' ';
}}
*/

$filename = $session['name'].'_'.$atlas_name.'_';
if ($tiltSeriesNumber < 10) {
	$filename .= '00'.$tiltSeriesNumber; 
} else {
	if ($tiltSeriesNumber < 100) {
		$filename .= '0'.$tiltSeriesNumber; 
	} else {
		$filename .= $tiltSeriesNumber; 
	}
}

if (!preg_match("%\.mrc$%i", $filename))
	$filename = Preg_replace("%$%", ".txt", $filename);

$data = array();
foreach($results as $result) {
		$mrc_filename = $result['filename'].'.mrc';
    $data[] = array(
        "filename" => $mrc_filename,
				"alpha" => $result["alpha"],
    );
}
$delimiter = chr(9);
$context = stream_context_create();
$handle = fopen('php://memory', "w");
foreach ($data as $line) {
	fputcsv($handle, $line, $delimiter);
}
fseek($handle, 0);
header("Content-Type: text/plain");
header('Content-Disposition: attachment; filename="'.$filename.'";');
fpassthru($handle);
?> 
