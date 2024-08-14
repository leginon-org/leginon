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
	$predictions = $tomography->getPredictionData($tiltSeriesId);
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

function formatMDoc($in_array) {
	$out_array = array();
	foreach ($in_array as $k=>$v) {
		$out_array[]="$k = $v";
	}
	$out_array[]='';
	return $out_array;
	
}

$stackheader_array = array(
		"PixelSpacing"=>$results[0]['pixel_size']*1e10,
		"ImageFile"=>$filename.".mrc",
		"ImageSize"=>$results[0]['dimension_x']." ". $results[0]['dimension_y'],
		"DataMode"=>1,
	);
$stackheader = formatMDoc($stackheader_array);

$tiltaxis = $predictions[0]['SUBD|predicted position|phi']*(180.0/3.14159); #degrees
$spot_size = $results[0]['spot_size'];

$title = array(
		"[T = Leginon tomography]",
		'',
		"[T = Tilt axis angle = $tiltaxis, binning = 1 spot = $spot_size ]",
		'',
); 

$frame_format = 'tif';

$data = array_merge($stackheader, $title);
$z = 0;
foreach ($results as $r) {
	$a = array();
	$a['TiltAngle']=$r['alpha'];
	$a['StagePosition']=$r['stage_x']*1e6." ".$r['stage_y']*1e6;
	$a['StageZ']=$r['stage_z']*1e6;
	$a['Magnification']=$r['magnification'];
	$a['Intensity']=$r['mean'];
	$dose_r=$tomography->getImageDose($r['id']); # e/A^2?
	$a['ExposureDose']= ($dose_r) ? $dose_r['dose']: '';
	$a['PixelSpacing']=$r['pixel_size']*1e10; # A
	$a['SpotSize']=$r['spot_size'];
	$a['Defocus']=$r['defocus']*1e6;
	$a['ImageShift']=$r['shift_x']*1e6." ".$r['shift_y']*1e6;
	$a['RotationAngle']=abs($tiltaxis); # Some tilt axis type of notation in serial em.
	$a['ExposureTime']=$r['exposure_time']*1e-3; # seconds
	$a['Binning']=1; #PixelSpacing already binned.
	$a['CameraIndex']=1; # not meaningful for processing
	$a['DividedBy2']=1; # no effect on processing.
	$a['MagIndex']=1; # not meaningful for processing
	$a['MinMaxMean']="-1 1 0"; # what is this ?
	$a['TargetDefocus']=$r['intended_defocus']*1e6;
	$a['SubFramePath']=$r['filename'].'.frames.'.$frame_format;
	$a['NumSubFrames']=$r['nframes'];
	$a['DateTime']=date('d-M-Y H:i:s', $r['timestamp']); #datetime format read literally in Warp.
	$one_data=array();
	$one_data[]="[ZValue = $z]";
	$one_data = array_merge($one_data, formatMDoc($a));
	$z = $z + 1;
	$data = array_merge($data, $one_data);
}

if (!preg_match("%\.mrc$%i", $filename))
	$filename = Preg_replace("%$%", ".mdoc", $filename);


$delimiter = chr(9);
$context = stream_context_create();
$handle = fopen('php://memory', "w");
foreach ($data as $line) {
	fwrite($handle, $line."\n");
}
fseek($handle, 0);
header("Content-Type: text/plain");
header('Content-Disposition: attachment; filename="'.$filename.'";');
fpassthru($handle);
?> 
