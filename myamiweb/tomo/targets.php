<?php

require_once('../config.php');
require_once('../inc/mysql.inc');

$session = $_GET['sessionId'];
if(!$session)
   exit('no session specified');

class Target {
    var $id;
    var $number;
    var $version;
    var $status;
    var $type;
    var $preset;
    var $target_number;
    var $target_list_id;
    var $parent_image_id;
    var $parent_image;
    var $child_images;

    function Target($array) {
        $this->id = $array['id'];
        $this->number = $array['number'];
        $this->version = $array['version'];
        $this->status = $array['status'];
        $this->type = $array['type'];
        $this->preset = $array['preset'];
        $this->target_list_id =  $array['list_id'];
        $this->parent_image_id =  $array['image_id'];
        $this->target_number = null;
        $this->parent_image = null;
        $this->child_images = array();
    }

    function setTargetNumber(&$target_number) {
        $this->target_number = $target_number;
    }

    function setParentImage(&$parent_image) {
        $this->parent_image = $parent_image;
    }

    function addChildImage(&$child_image) {
        $this->child_images[$child_image->id] = &$child_image;
    }

    function hasParent() {
        return !is_null($this->parent_image);
    }
}

class TargetNumber {
    var $number;
    var $targets;
    var $target_list;

    function TargetNumber($number) {
        $this->number = $number;
        $this->target_list = null;
        $this->targets = array();
    }

    function setTargetList(&$target_list) {
        $this->target_list = $target_list;
    }

    function addTarget(&$target) {
        $this->targets[$target->id] = &$target;
    }
}

class Image {
    var $id;
    var $preset;
    var $parent_target_id;
    var $parent_target;
    var $child_targets;
    var $child_target_lists;
    var $tilt_series_id;
    var $tilt_series;
    var $mosaic_tiles;
    var $reference_targets;

    function Image($array) {
        $this->id = $array['id'];
        $this->preset = $array['preset'];
        $this->parent_target_id = $array['target_id'];
        $this->tilt_series_id = $array['tilt_series_id'];
        $this->parent_target = null;
        $this->child_targets = array();
        $this->child_target_lists = array();
        $this->tilt_series = null;
        $this->mosaic_tiles = array();
        $this->reference_targets = array();
    }

    function setParentTarget(&$parent_target) {
        $this->parent_target = $parent_target;
    }

    function addChildTarget(&$child_target) {
        $this->child_targets[$child_target->id] = &$child_target;
    }

    function addChildTargetList(&$child_target_list) {
        $this->child_target_lists[$child_target_list->id] = &$child_target_list;
    }

    function setTiltSeries(&$tilt_series) {
        $this->tilt_series = $tilt_series;
    }

    function addMosaicTile(&$mosaic_tile) {
        $this->mosaic_tiles[$mosaic_tile->id] = &$mosaic_tile;
    }

    function addReferenceTarget(&$reference_target) {
        $this->reference_targets[$reference_target->id] = &$reference_target;
    }

    function hasParent() {
        return !is_null($this->parent_target);
    }
}

class TargetList {
    var $id;
    var $sub_list;
    var $target_numbers;
    var $parent_image_id;
    var $parent_image;
    var $queue_id;
    var $queue;
    var $image_lists;
    var $reference_targets;
    var $dequeueds;

    function TargetList($array) {
        $this->id = $array['id'];
        $this->sub_list = $array['sub_list'];
        $this->parent_image_id =  $array['image_id'];
        $this->queue_id =  $array['queue_id'];
        $this->target_numbers = array();
        $this->parent_image = null;
        $this->queue = null;
        $this->image_lists = array();
        $this->reference_targets = array();
        $this->dequeueds = array();
    }

    function setParentImage(&$parent_image) {
        $this->parent_image = $parent_image;
    }

    function &getTargetNumber(&$number) {
        if(!array_key_exists($number, $this->target_numbers)) {
            $target_number = new TargetNumber($number);
            $this->target_numbers[$number] = &$target_number;
            $target_number->setTargetList($this);
        } else {
            $target_number = &$this->target_numbers[$number];
        }
        return $target_number;
    }

    function setQueue(&$queue) {
        $this->queue = $queue;
    }

    function addDequeued(&$dequeued) {
        $this->dequeueds[$dequeued->id] = &$dequeued;
    }

    function addImageList(&$image_list) {
        $this->image_lists[$image_list->id] = &$image_list;
    }

    function addMosaicTile(&$mosaic_tile) {
        $this->mosaic_tiles[$mosaic_tile->id] = &$mosaic_tile;
    }

    function hasParent() {
        return !is_null($this->parent_image);
    }
}

class ImageList {
    var $id;
    var $target_list_id;
    var $target_list;
    var $mosaic_tiles;

    function ImageList($array) {
        $this->id = $array['id'];
        $this->target_list_id = $array['target_list_id'];
        $this->target_list = null;
        $this->mosaic_tiles = array();
    }

    function setTargetList(&$target_list) {
        $this->target_list = &$target_list;
    }

    function addMosaicTile(&$mosaic_tile) {
        $this->mosaic_tiles[$mosaic_tile->id] = &$mosaic_tile;
    }
}

class TiltSeries {
    var $id;
    var $images;

    function TiltSeries($array) {
        $this->id = $array['id'];
        $this->images = array();
    }

    function addImage(&$image) {
        $this->images[$image->id] = &$image;
    }
}

class Queue {
    var $id;
    var $target_lists;
    var $dequeueds;

    function Queue($array) {
        $this->id = $array['id'];
        $this->target_lists = array();
        $this->dequeueds = array();
    }

    function addTargetList(&$target_list) {
        $this->target_lists[$target_list->id] = &$target_list;
    }

    function addDequeued(&$dequeued) {
        $this->dequeueds[$dequeued->id] = &$dequeued;
    }
}

class Dequeued {
    var $id;
    var $target_list_id;
    var $target_list;
    var $queue_id;
    var $queue;

    function Dequeued($array) {
        $this->id = $array['id'];
        $this->target_list_id = $array['target_list_id'];
        $this->queue_id = $array['queue_id'];
        $this->target_list = null;
        $this->queue = null;
    }

    function setTargetList(&$target_list) {
        $this->target_list = &$target_list;
    }

    function setQueue(&$queue) {
        $this->queue = $queue;
    }
}

class MosaicTile {
    var $id;
    var $image_id;
    var $image;
    var $image_list_id;
    var $image_list;

    function MosaicTile($array) {
        $this->id = $array['id'];
        $this->image_id = $array['image_id'];
        $this->image_list_id = $array['image_list_id'];
        $this->image = null;
        $this->image_list = null;
    }

    function setImage(&$image) {
        $this->image = &$image;
    }

    function setImageList(&$image_list) {
        $this->image_list = &$image_list;
    }
}

class ReferenceTarget {
    var $id;
    var $image_id;
    var $image;
    var $target_list_id;
    var $target_list;

    function Reference($array) {
        $this->id = $array['id'];
        $this->image_id = $array['image_id'];
        $this->target_list_id = $array['target_list_id'];
        $this->image = null;
        $this->target_list = null;
    }

    function setImage(&$image) {
        $this->image = &$image;
    }

    function setTargetList(&$target_list) {
        $this->target_list = &$target_list;
    }
}

$target_query = 'SELECT'
        .' target.DEF_id AS id,'
        .' target.status AS status,'
        .' target.number AS number,'
        .' target.version AS version,'
        .' target.type AS type,'
        .' preset.name AS preset,'
        .' target.`REF|ImageTargetListData|list` AS list_id,'
        .' target.`REF|AcquisitionImageData|image` AS image_id'
        .' FROM'
        .' AcquisitionImageTargetData target'
        .' LEFT JOIN'
        .' PresetData preset'
        .' ON'
        .' target.`REF|PresetData|preset`=preset.DEF_id'
        .' WHERE'
        .' target.`REF|SessionData|session`='.$session
        .';';

$image_query = 'SELECT'
        .' image.DEF_id AS id,'
        .' preset.name AS preset,'
        .' image.`REF|AcquisitionImageTargetData|target` AS target_id,'
        .' image.`REF|TiltSeriesData|tilt series` AS tilt_series_id'
        .' FROM'
        .' AcquisitionImageData image'
        .' LEFT JOIN'
        .' PresetData preset'
        .' ON'
        .' image.`REF|PresetData|preset`=preset.DEF_id'
        .' WHERE'
        .' image.`REF|SessionData|session`='.$session
        .';';

$target_list_query = 'SELECT'
        .' target_list.DEF_id AS id,'
        .' target_list.sublist AS sub_list,'
        .' target_list.`REF|QueueData|queue` AS queue_id,'
        .' target_list.`REF|AcquisitionImageData|image` AS image_id'
        .' FROM'
        .' ImageTargetListData target_list'
        .' WHERE'
        .' target_list.`REF|SessionData|session`='.$session
        .';';

$image_list_query = 'SELECT'
        .' image_list.DEF_id AS id,'
        .' image_list.`REF|ImageTargetListData|targets` AS target_list_id'
        .' FROM'
        .' ImageListData image_list'
        .' WHERE'
        .' image_list.`REF|SessionData|session`='.$session
        .';';

$tilt_series_query = 'SELECT'
        .' tilt_series.DEF_id AS id'
        .' FROM'
        .' TiltSeriesData tilt_series'
        .' WHERE'
        .' tilt_series.`REF|SessionData|session`='.$session
        .';';

$queue_query = 'SELECT'
        .' queue.DEF_id AS id'
        .' FROM'
        .' QueueData queue'
        .' WHERE'
        .' queue.`REF|SessionData|session`='.$session
        .';';

$mosaic_tile_query = 'SELECT'
        .' mosaic_tile.DEF_id AS id,'
        .' mosaic_tile.`REF|AcquisitionImageData|image` AS image_id,'
        .' mosaic_tile.`REF|ImageListData|list` AS image_list_id'
        .' FROM'
        .' MosaicTileData mosaic_tile'
        .' WHERE'
        .' mosaic_tile.`REF|SessionData|session`='.$session
        .';';

$reference_target_query = 'SELECT'
        .' reference_target.DEF_id AS id,'
        .' reference_target.`REF|AcquisitionImageData|image` AS image_id,'
        .' reference_target.`REF|ImageTargetListData|list` AS target_list_id'
        .' FROM'
        .' ReferenceTargetData reference_target'
        .' WHERE'
        .' reference_target.`REF|SessionData|session`='.$session
        .';';

$dequeued_query = 'SELECT'
        .' dequeued.DEF_id AS id,'
        .' dequeued.`REF|QueueData|queue` AS queue_id,'
        .' dequeued.`REF|ImageTargetListData|list` AS target_list_id'
        .' FROM'
        .' DequeuedImageTargetListData dequeued'
        .' WHERE'
        .' dequeued.`REF|SessionData|session`='.$session
        .';';

$mysql = new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

$query_results = $mysql->getSQLResult($target_query);
$targets = array();
foreach($query_results as $query_result)
   $targets[$query_result['id']] = &new Target($query_result);

$query_results = $mysql->getSQLResult($image_query);
$images = array();
foreach($query_results as $query_result)
   $images[$query_result['id']] = &new Image($query_result);

$query_results = $mysql->getSQLResult($target_list_query);
$target_lists = array();
foreach($query_results as $query_result)
   $target_lists[$query_result['id']] = &new TargetList($query_result);

$query_results = $mysql->getSQLResult($image_list_query);
$image_lists = array();
foreach($query_results as $query_result)
   $image_lists[$query_result['id']] = &new ImageList($query_result);

$query_results = $mysql->getSQLResult($tilt_series_query);
$tilt_series_array = array();
foreach($query_results as $query_result)
   $tilt_series_array[$query_result['id']] = &new TiltSeries($query_result);

$query_results = $mysql->getSQLResult($queue_query);
$queues = array();
foreach($query_results as $query_result)
   $queues[$query_result['id']] = &new Queue($query_result);

$query_results = $mysql->getSQLResult($mosaic_tile_query);
$mosaic_tiles = array();
foreach($query_results as $query_result)
   $mosaic_tiles[$query_result['id']] = &new MosaicTile($query_result);

$query_results = $mysql->getSQLResult($reference_target_query);
$reference_targets = array();
foreach($query_results as $query_result)
   $reference_targets[$query_result['id']] = &new ReferenceTarget($query_result);

$query_results = $mysql->getSQLResult($dequeued_query);
$dequeueds = array();
foreach($query_results as $query_result)
   $dequeueds[$query_result['id']] = &new Dequeued($query_result);

foreach(array_keys($targets) as $target_id) {
    $target = &$targets[$target_id];
    if(!is_null($target->target_list_id)) {
        $target_list = &$target_lists[$target->target_list_id];
        $target_number = &$target_list->getTargetNumber($target->number);
        $target->setTargetNumber($target_number);
        $target_number->addTarget($target);
    }
    if(!is_null($target->parent_image_id)) {
        $parent_image = &$images[$target->parent_image_id];
        $target->setParentImage($parent_image);
        $parent_image->addChildTarget($target);
    }
}

foreach(array_keys($target_lists) as $target_list_id) {
    $target_list = &$target_lists[$target_list_id];
    if(!is_null($target_list->parent_image_id)) {
        $parent_image = &$images[$target_list->parent_image_id];
        $target_list->setParentImage($parent_image);
        $parent_image->addChildTargetList($target_list);
    }
    if(!is_null($target_list->queue_id)) {
        $queue = &$queues[$target_list->queue_id];
        $target_list->setQueue($queue);
        $queue->addTargetList($target_list);
    }
}

foreach(array_keys($image_lists) as $image_list_id) {
    $image_list = &$image_lists[$image_list_id];
    if(!is_null($image_list->target_list_id)) {
        $target_list = &$target_lists[$image_list->target_list_id];
        $image_list->setTargetList($target_list);
        $target_list->addImageList($image_list);
    }
}

foreach(array_keys($images) as $image_id) {
    $image = &$images[$image_id];
    if(!is_null($image->parent_target_id)) {
        $parent_target = &$targets[$image->parent_target_id];
        $image->setParentTarget($parent_target);
        $parent_target->addChildImage($image);
    }
    if(!is_null($image->tilt_series_id)) {
        $tilt_series = &$tilt_series_array[$image->tilt_series_id];
        $image->setParentTarget($tilt_series);
        $tilt_series->addImage($image);
    }
}

foreach(array_keys($mosaic_tiles) as $mosaic_tile_id) {
    $mosaic_tile = &$mosaic_tiles[$mosaic_tile_id];
    if(!is_null($mosaic_tile->image_id)) {
        $image = &$images[$mosaic_tile->image_id];
        $mosaic_tile->setImage($image);
        $image->addMosaicTile($mosaic_tile);
    }
    if(!is_null($mosaic_tile->image_list_id)) {
        $image_list = &$image_lists[$mosaic_tile->image_list_id];
        $mosaic_tile->setImageList($image_list);
        $image_list->addMosaicTile($mosaic_tile);
    }
}

foreach(array_keys($reference_targets) as $reference_target_id) {
    $reference_target = &$reference_targets[$reference_target_id];
    if(!is_null($reference_target->image_id)) {
        $image = &$images[$reference_target->image_id];
        $reference_target->setImage($image);
        $image->addReferenceTarget($reference_target);
    }
    if(!is_null($reference_target->target_list_id)) {
        $target_list = &$target_lists[$reference_target->target_list_id];
        $reference_target->setTargetList($target_list);
        $target_list->addReferenceTarget($reference_target);
    }
}

foreach(array_keys($dequeueds) as $dequeued_id) {
    $dequeued = &$dequeueds[$dequeued_id];
    if(!is_null($dequeued->target_list_id)) {
        $target_list = &$target_lists[$dequeued->target_list_id];
        $dequeued->setTargetList($target_list);
        $target_list->addDequeued($dequeued);
    }
    if(!is_null($dequeued->queue_id)) {
        $queue = &$queues[$dequeued->queue_id];
        $dequeued->setQueue($queue);
        $queue->addDequeued($dequeued);
    }
}

$colors = array(
    'new' => 'green',
    'processing' => 'orange',
    'aborted' => 'red',
    'done' => 'blue',
);

echo '<table>';
foreach(array_keys($targets) as $target_id) {
    $target = &$targets[$target_id];
    echo '<tr>';
    echo '<td>';
    echo $target->id;
    echo '</td>';
    echo '<td>';
    echo $target->version;
    echo '</td>';
    echo '<td>';
    echo $target->status;
    echo '</td>';
    echo '<td>';
    echo $target->type;
    echo '</td>';
    echo '<td>';
    echo $target->preset;
    echo '</td>';
    if(is_null($target->target_number)) {
        $target_number = '';
        $target_list_id = '';
    } else {
        $target_number = $target->target_number->number;
        $target_list_id = $target->target_number->target_list->id;
    }
    echo '<td>';
    echo $target_number;
    echo '</td>';
    echo '<td>';
    echo $target_list_id;
    echo '</td>';
    if(is_null($target->parent_image)) {
        $parent_image_id = '';
    } else {
        $parent_image_id = $target->parent_image->id;
    }
    echo '<td>';
    echo $parent_image_id;
    echo '</td>';
    echo '<td>';
    $child_image_ids = array();
    foreach(array_keys($target->child_images) as $child_image_id) {
        $child_image = $target->child_images[$child_image_id];
        $child_image_ids[] = $child_image->id;
    }
    echo implode(', ', $child_image_ids);
    echo '</td>';
    echo '</tr>';
}
echo '</table>';

/*
$statuses = array();
foreach(array_keys($target_lists) as $target_list_id) {
    $target_list = &$target_lists[$target_list_id];
    foreach(array_keys($target_list->target_numbers) as $target_number_id) {
        $target_number = $target_list->target_numbers[$target_number_id];
        $last_target = end($target_number->targets);
        $status = $last_target->status;
        if($last_target->preset != 'Hole')
            continue;
        if($last_target->type != 'acquisition')
            continue;
        if(!array_key_exists($status, $statuses))
            $statuses[$status] = 1;
        else
            $statuses[$status]++;
    }
}
print_r($statuses);

function targetListTable(&$target_list) {
    $n = count($target_list->target_numbers);

    echo '<table>';
    echo '<tr>';
    echo '<th colspan='.$n.'>';
    echo $target_list->id;
    echo '</th>';
    echo '</tr>';
    echo '<tr>';
    foreach(array_keys($target_list->target_numbers) as $target_number_id) {
        $target_number = $target_list->target_numbers[$target_number_id];
        echo '<td>';
        targetNumberTable($target_number);
        echo '</td>';
    }
    echo '</table>';
}

function targetNumberTable(&$target_number) {
    $colors = array(
        'new' => 'green',
        'processing' => 'orange',
        'aborted' => 'red',
        'done' => 'blue',
    );

    $last_target = end($target_number->targets);
    $color = $colors[$last_target->status];
    $n = count($target_number->targets);

    echo '<table>';
    echo '<tr>';
    echo '<th colspan='.$n.' style="color: '.$color.'">';
    echo '#'.$target_number->number;
    echo '</th>';
    echo '</tr>';
    foreach(array_keys($target_number->targets) as $target_id) {
        $target = $target_number->targets[$target_id];
        echo '<td>';
        targetTable($target);
        echo '</td>';
    }
    echo '</table>';
}

function targetTable(&$target) {
    $colors = array(
        'new' => 'green',
        'processing' => 'orange',
        'aborted' => 'red',
        'done' => 'blue',
    );

    $color = $colors[$target->status];
    $n = count($target->child_images);

    echo '<table style="font-size: small">';
    echo '<tr>';
    echo '<th colspan='.$n.' style="color: '.$color.'">';
    echo $target->id;
    echo '</th>';
    echo '</tr>';
    foreach(array_keys($target->child_images) as $child_image_id) {
        $child_image = $target->child_images[$child_image_id];
        echo '<td>';
        imageTable($child_image);
        echo '</td>';
    }
    echo '</table>';
}

function imageTable(&$image) {
    $n = count($target->child_target_lists);

    echo '<table style="font-size: small">';
    echo '<tr>';
    echo '<th colspan='.$n.'>';
    #echo '<img src="jpeg.php?imageId='.$image->id.'">';
    echo $image->id;
    echo '</th>';
    echo '</tr>';
    foreach(array_keys($image->child_target_lists) as $child_target_list_id) {
        $child_target_list = $image->child_target_lists[$child_target_list_id];
        echo '<td>';
        targetListTable($child_target_list);
        echo '</td>';
    }
    foreach(array_keys($image->child_targets) as $child_target_id) {
        $child_target = $image->child_targets[$child_target_id];
        echo '<td>';
        targetTable($child_target);
        echo '</td>';
    }
    echo '</table>';
}

echo '<table>';
foreach(array_keys($target_lists) as $target_list_id) {
    $target_list = &$target_lists[$target_list_id];
    if($target_list->hasParent())
        continue;
    $continue = false;
    foreach(array_keys($target_list->target_numbers) as $target_number_id) {
        $target_number = $target_list->target_numbers[$target_number_id];
        foreach(array_keys($target_number->targets) as $target_id) {
            $target = $target_number->targets[$target_id];
            if($target->hasParent()) {
                $continue = true;
                break;
            }
        }
    }
    if($continue)
        continue;
    echo '<tr>';
    targetListTable($target_list);
    echo '</tr>';
}
echo '</table>';
*/

?>
