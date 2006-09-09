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
    var $child_image;

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
        $this->child_image = null;
    }

    function setTargetNumber(&$target_number) {
        $this->target_number = $target_number;
    }

    function setParentImage(&$parent_image) {
        $this->parent_image = $parent_image;
    }

    function setChildImage(&$child_image) {
        $this->child_image = $child_image;
    }

    function toString($prefix='') {
        $string = $prefix.'Target '.$this->id.'<br>';
        if(!is_null($this->child_image))
            $string .= $this->child_image->toString($prefix.'___');
        return $string;
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

    function toString($prefix='') {
        $string = $prefix.'Target #'.$this->number.'<br>';
        foreach(array_keys($this->targets) as $target_id) {
            $target = &$this->targets[$target_id];
            $string .= $target->toString($prefix.'___');
        }
        return $string;
    }

}

class Image {
    var $id;
    var $preset;
    var $parent_target_id;
    var $parent_target;
    var $child_targets;
    var $child_target_lists;

    function Image($array) {
        $this->id = $array['id'];
        $this->preset = $array['preset'];
        $this->parent_target_id = $array['target_id'];
        $this->parent_target = null;
        $this->child_targets = array();
        $this->child_target_lists = array();
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

    function toString($prefix='') {
        $string = $prefix.'Image '.$this->id.'<br>';
        foreach(array_keys($this->child_target_lists)
                    as $child_target_list_id) {
            $target_list = $this->child_target_lists[$child_target_list_id];
            $string .= $target_list->toString($prefix.'___');
        }
        return $string;
    }
}

class TargetList {
    var $id;
    var $target_numbers;
    var $parent_image_id;
    var $parent_image;
    var $queue_id;
    var $queue;
    var $image_lists;

    function TargetList($array) {
        $this->id = $array['id'];
        $this->parent_image_id =  $array['image_id'];
        $this->queue_id =  $array['queue_id'];
        $this->target_numbers = array();
        $this->parent_image = null;
        $this->queue = null;
        $this->image_lists = array();
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

    function addImageList(&$image_list) {
        $this->image_lists[$image_list->id] = &$image_list;
    }

    function toString($prefix='') {
        $string = $prefix.'TargetList '.$this->id.'<br>';
        foreach(array_keys($this->target_numbers) as $number) {
            $target_number = &$this->target_numbers[$number];
            $string .= $target_number->toString($prefix.'___');
        }
        return $string;
    }
}

class ImageList {
    var $id;
    var $target_list_id;
    var $target_list;

    function ImageList($array) {
        $this->id = $array['id'];
        $this->target_list_id = $array['target_list_id'];
        $this->target_list = null;
    }

    function setTargetList(&$target_list) {
        $this->target_list = &$target_list;
    }

    function toString($prefix='') {
        $string = $prefix.'ImageList '.$this->id.'<br>';
        if(!is_null($this->target_list)) 
            $string .= $this->target_list->toString($prefix.'___');
        return $string;
    }
}

class Queue {
    var $id;
    var $target_lists;

    function Queue($array) {
        $this->id = $array['id'];
        $this->target_lists = array();
    }

    function addTargetList(&$target_list) {
        $this->target_lists[$target_list->id] = &$target_list;
    }

    function toString($prefix='') {
        $string = $prefix.'Queue '.$this->id.'<br>';
        foreach(array_keys($this->target_lists) as $target_list_id) {
            $target_list = &$this->target_lists[$target_list_id];
            $string .= $target_list->toString($prefix.'___');
        }
        return $string;
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
        .' image.`REF|AcquisitionImageTargetData|target` AS target_id'
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

$queue_query = 'SELECT'
        .' queue.DEF_id AS id'
        .' FROM'
        .' QueueData queue'
        .' WHERE'
        .' queue.`REF|SessionData|session`='.$session
        .';';

$mysql = new mysql($DB_HOST, $DB_USER, $DB_PASS, $DB);

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

$query_results = $mysql->getSQLResult($queue_query);
$queues = array();
foreach($query_results as $query_result)
   $queues[$query_result['id']] = &new Queue($query_result);

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
        $parent_target->setChildImage($image);
    }
}

/*
foreach(array_keys($target_lists) as $target_list_id) {
    $target_list = &$target_lists[$target_list_id];
    echo $target_list->toString();
}

foreach(array_keys($queues) as $queue_id) {
    $queue = &$queues[$queue_id];
    echo $queue->toString();
}

foreach(array_keys($image_lists) as $image_list_id) {
    $image_list = &$image_lists[$image_list_id];
    echo $image_list->toString();
}
*/

?>
