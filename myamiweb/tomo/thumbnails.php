<?php
require_once "config.php";
require_once "inc/image.inc";
require_once "tomo/tomography.php";

function sortTiltSeriesData(&$data) {
    $threshold = 0.05;
    $n = count($data);
    if($n < 3)
         return -1;
    for($i = 1; $i < $n; $i++) {
        $diff = abs($data[$i]['alpha'] - $data[$i - 1]['alpha']);
        if($diff < $threshold) {
            if($i + 1 < $n - 1) {
                $delta_id1 = abs($data[$i]['id'] - $data[$i + 1]['id']);
                $delta_id2 = abs($data[$i - 1]['id'] - $data[$i + 1]['id']);
                $swap = $delta_id1 > $delta_id2;
            } else {
                $delta_id1 = abs($data[$i]['id'] - $data[$i - 2]['id']);
                $delta_id2 = abs($data[$i - 1]['id'] - $data[$i - 2]['id']);
                $swap = $delta_id1 < $delta_id2;
            }
            if($swap) {
                $temp = $data[$i];
                $data[$i] = $data[$i - 1];
                $data[$i - 1] = $temp;
                return $i;
            }
            break;
        }
    }
    return -1;
}

function findMinImageId($results) {
    $min_image_id = -1;
    $tilts = array();
		if (is_array($results))
    foreach($results as $result) {
        if($result['imageId'] < $min_image_id or $min_image_id == -1)
            $min_image_id = $result['imageId'];
    }
    return $min_image_id;
}

function getTiltData($data, $indices) {
    $tilts = array();
    $n = count($data);
    foreach($indices as $i => $index) {
        $image_id = $data[$index]['imageId'];
        $alpha = $data[$index]['alpha'];
        $tilts[$image_id] = $alpha;
    }
    return $tilts;
}

function thumbnailTable($tilts, $min_image_id) {
    echo '<tr>';
    foreach($tilts as $image_id => $tilt) {
        echo '<th>';
        echo '#'.($image_id - $min_image_id + 1);
        echo '</th>';
    }
    echo '</tr>';
    echo '<tr>';
    foreach($tilts as $image_id => $tilt) {
        echo '<th>';
        echo number_format($tilt, 1).'&deg';
        echo '</th>';
    }
    echo '</tr>';
    echo '<tr>';
    foreach($tilts as $image_id => $tilt) {
        echo '<td>';
        echo '<img src="jpeg.php?imageId='.$image_id.'" width=64 height=64>';
        echo '</td>';
    }
    echo '</tr>';
}

function getIndicies($results, $split) {
    $n = count($results);
    if($n < 10)
        return range(0, $n - 1);
    $indices = array();
    $indices[] = 0;
    if($split == -1) {
        $m = $n/9;
	for($i = 0; $i < 9; $i++)
    		$indices[] = round($i*$m);
    } else {
        $m = $split/5;
	for($i = 0; $i < 4; $i++)
    		$indices[] = round($i*$m);
        $indices[] = $split - 1;
	for($i = 0; $i < 4; $i++)
    		$indices[] = round($i*$m + $split);
        $indices[] = $split;
    }
    $indices[] = $n - 1;
    return $indices;
}

function thumbnails($tiltSeriesId, $tomography) {
	$results = $tomography->getTiltSeriesData($tiltSeriesId, true);
	$split = sortTiltSeriesData($results);
	$min_image_id = findMinImageId($results);
	$indices = getIndicies($results, $split);
	$tilts = getTiltData($results, $indices);
	echo '<table>';
	thumbnailTable($tilts, $min_image_id);
	echo '</table>';
}

?> 
