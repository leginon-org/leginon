<?php

$mrc2014_format = array(
    "n" => array(
        "x" => "V",
        "y" => "V",
        "z" => "V",
    ),
    "mode" => "V",
    "n start" => array(
        "x" => "V",
        "y" => "V",
        "z" => "V",
    ),
    "m" => array(
        "x" => "V",
        "y" => "V",
        "z" => "V",
    ),
    "cell" => array(
        "x" => "f",
        "y" => "f",
        "z" => "f",
        "alpha" => "f",
        "beta" => "f",
        "gamma" => "f",
    ),
    "axis" => array(
        "c" => "V",
        "r" => "V",
        "s" => "V",
    ),
    "density" => array(
        "min" => "f",
        "max" => "f",
        "mean" => "f",
    ),
    "space group number" => "V",
    "n symmetry bytes" => "V",
    "extra1" => "x8",
    "exttype" => "x4",
    "extra2" => "x88",
    "origin" => array(
        "x" => "f",
        "y" => "f",
        "z" => "f",
    ),
    "map" => "a4",
    "machine stamp" => "V",
    "map rms" => "f",
    "n labels" => "V",
    "labels" => "a800",
);

//This mrc stack format is the definition of UCSF Tomography.
//It is not compatible with CCP4 library but readable by IMOD
//and libraries not reading bytes 197-220 (base 1)
$mrc_stack_format = array(
    "n" => array(
        "x" => "V",
        "y" => "V",
        "z" => "V",
    ),
    "mode" => "V",
    "n start" => array(
        "x" => "V",
        "y" => "V",
        "z" => "V",
    ),
    "m" => array(
        "x" => "V",
        "y" => "V",
        "z" => "V",
    ),
    "cell" => array(
        "x" => "f",
        "y" => "f",
        "z" => "f",
        "alpha" => "f",
        "beta" => "f",
        "gamma" => "f",
    ),
    "axis" => array(
        "c" => "V",
        "r" => "V",
        "s" => "V",
    ),
    "density" => array(
        "min" => "f",
        "max" => "f",
        "mean" => "f",
    ),
    "space group number" => "V",
    "n symmetry bytes" => "V",
    "dvid" => "S",
    "n blank" => "S",
    "itst" => "V",
    "exttype" => "a4",
    "blank" => "a20",
    "n integers" => "S",
    "n floats" => "S",
    "sub" => "S",
    "zfac" => "S",
    "min2" => "f",
    "max2" => "f",
    "min3" => "f",
    "max3" => "f",
    "min4" => "f",
    "max4" => "f",
    "type" => "S",
    "lensum" => "S",
    "nd1" => "S",
    "nd2" => "S",
    "vd1" => "S",
    "vd2" => "S",
    "min5" => "f",
    "max5" => "f",
    "numtimes" => "S",
    "imgseq" => "S",
    "xtilt" => "f",
    "ytilt" => "f",
    "ztilt" => "f",
    "numwaves" => "S",
    "wave1" => "S",
    "wave2" => "S",
    "wave3" => "S",
    "wave4" => "S",
    "wave5" => "S",
    "origin" => array(
        "x" => "f",
        "y" => "f",
        "z" => "f",
    ),
    "n labels" => "V",
    "labels" => "a800",
);
$mrc_header_size = 1024;

$mrc_stack_extended_format = array(
    "stage" => array(
        "alpha" => "f",
        "beta" => "f",
        "x" => "f",
        "y" => "f",
        "z" => "f",
    ),
    "shift" => array(
        "x" => "f",
        "y" => "f",
    ),
    "defocus" => "f",
    "exposure time" => "f",
    "mean intensity" => "f",
    "tilt axis" => "f",
    "pixel size" => "f",
    "magnification" => "f",
    "reserved" => "a36",
);
$mrc_stack_extended_format_size = 88;
$float_size = 4;

function getFormat($array, $prefix="") {
    $format = "";
    foreach($array as $key => $value) {
        if(strlen($format) > 0) {
            $format .= "/";
        }
        if(strlen($prefix) > 0) {
            $key = $prefix."->".$key;
        }
        if(is_string($value)) {
            $format .= $value;
            $format .= $key;
        } else if(is_array($value)) {
            $format .= getFormat($value, $key);
        } else {
            exit;
        }
    }
    return $format;
}

function getContents($array, $format, $prefix="") {
    $contents = "";
    foreach($format as $key => $format_string) {
        if(strlen($prefix) > 0) {
            $key = $prefix."->".$key;
        }
        if(is_string($format_string)) {
            $contents .= pack($format_string, $array[$key]);
        } else if(is_array($format_string)) {
            $contents .= getContents($array, $format_string, $key);
        } else {
            exit;
        }
    }
    return $contents;
}

function readMRCHeader($handle, $format) {
    $format = getFormat($format);
    $size = 1024;
    $contents = "";
    $bytes_read = 0;
    while(!feof($handle) && $bytes_read < $size) {
        $contents .= fread($handle, $size - $bytes_read);
        $bytes_read = strlen($contents);
    }
    $header = unpack($format, $contents);
    return $header;
}

function getSize($header) {
    $mode_sizes = array(
        0 => 1,
        1 => 2,
        2 => 4,
        3 => 2,
        4 => 4,
        6 => 2,
    );

    $n = $header["n->x"]*$header["n->y"]*$header["n->z"];
    if($n > 1) {
        $n *= $header["n->z"];
    }
    $bytes = $mode_sizes[$header["mode"]];
    $size = $n*$bytes;
    return $size;
}

function writeHeader($filename, $size) {
    header("Cache-Control: no-store, no-cache, must-revalidate");
    header("Cache-Control: post-check=0, pre-check=0", false);
    header("Pragma: no-cache");
    header("Expires: ".gmdate("D, d M Y H:i:s", mktime(date("H")+2, date("i"), date("s"), date("m"), date("d"), date("Y")))." GMT");
    header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
    header("Content-Type: application/octet-stream");
    header("Content-Length: ".$size);
    header("Content-Disposition: inline; filename=$filename");
    header("Content-Transfer-Encoding: binary\n");
}

function writeMRCData($handle, $size) {
    $bytes_read = 0;
    while(!feof($handle) && $bytes_read < $size) {
        $s = fread($handle, 8192);
        $bytes_read += strlen($s);
        echo $s;
    }
}

require_once('tomography.php');

header("Content-Type: text/plain");
$tiltSeriesId = $_GET['tiltSeriesId'];
$tiltSeriesNumber = $_GET['tiltSeriesNumber'];
$alabel = $_GET['alignlabel'];
//Use the following to combine two half tilt series separated by 5
#$numbers = array($tiltSeriesId-5,$tiltSeriesId);
$numbers = array($tiltSeriesId);
$extended_headers = array();
$stack_size = 0;
$min = NULL;
$mean = 0.0;
$max = NULL;
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

// for debugging
/*
foreach($results as $result) {
    $filename = $session['image path'].'/'.$result['filename'].'.mrc';
		echo $filename.' ';
}}
*/

foreach($results as $result) {
    $filename = $session['image path'].'/'.$result['filename'].'.mrc';
    $handle = fopen($filename, "rb");
    if(!$handle) {
        exit;
    }

    $header = readMRCHeader($handle, $mrc2014_format);

    $size = getSize($header);
    $stack_size += $mrc_stack_extended_format_size;
    $stack_size += $size;

    if($min == NULL || $header['density->min'] < $min) {
        $min = $header['density->min'];
    }
    $mean += $header['density->mean']/$n_results;
    if($max == NULL || $header['density->max'] > $max) {
        $max = $header['density->max'];
    }

    if($result['mean'] == NULL) {
        $result['mean'] = $header['density->mean'];
    }
    
    $extended_header = array_diff($mrc_stack_extended_format, array());
    $extended_header["stage->alpha"] = $result["alpha"];
    $extended_header["stage->beta"] = $result["beta"];
    $extended_header["stage->x"] = $result["stage_x"];
    $extended_header["stage->y"] = $result["stage_y"];
    $extended_header["stage->z"] = $result["stage_z"];
    $extended_header["shift->x"] = $result["shift_x"];
    $extended_header["shift->y"] = $result["shift_y"];
    $extended_header["defocus"] = $result["defocus"];
    $extended_header["magnification"] = $result["magnification"];
    $extended_header["exposure time"] = $result["exposure_time"];
    $extended_header["tilt axis"] = $result["tilt_axis"];
    $extended_header["mean intensity"] = $result["mean"];
    $extended_header["pixel size"] = $result["pixel_size"]*$result["binning_x"];
    $extended_header["reserved"] = NULL;

    $extended_headers[] = array(
        "header" => $extended_header,
        "size" => $size,
        "filename" => $filename,
    );
    fclose($handle);
}
}
$n_results = count($numbers) * $n_results;
# make stack
$stack_header = array_diff($header, array());
$stack_header['n->z'] = $n_results;
$stack_header['m->z'] = 1;
$stack_header['cell->z'] = 1.0;
$stack_header['density->min'] = $min; 
$stack_header['density->mean'] = $mean;
$stack_header['density->max'] = $max;
$stack_header['origin->z'] = $n_results/2;
$stack_header["n symmetry bytes"] = $mrc_stack_extended_format_size*$n_results;
$stack_header["exttype"] = 'AGAR';
$stack_header["n integers"] = 0;
$stack_header["n floats"] = $mrc_stack_extended_format_size/$float_size;

$stack_size += $mrc_header_size;

#$filename = $results[0]["filename"];
#$filename = preg_replace("%_[0-9]*$%", '_stack.mrc', $filename);
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
	$filename = Preg_replace("%$%", ".mrc", $filename);

writeHeader($filename, $stack_size);

echo getContents($stack_header, $mrc_stack_format);
foreach($extended_headers as $extended_header) {
    $header = $extended_header["header"];
    echo getContents($header, $mrc_stack_extended_format);
}

foreach($extended_headers as $extended_header) {
    $filename = $extended_header["filename"];
    $size = $extended_header["size"];
    $handle = fopen($filename, "rb");
    if(!$handle) {
        exit;
    }
    fseek($handle, $mrc_header_size);
    writeMRCData($handle, $size);

    fclose($handle);
}
?> 
