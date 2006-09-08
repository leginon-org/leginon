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
}

class TargetList {
    var $id;
    var $target_numbers;
    var $parent_image_id;
    var $parent_image;

    function TargetList($array) {
        $this->id = $array['id'];
        $this->parent_image_id =  $array['image_id'];
        $this->target_numbers = array();
        $this->parent_image = null;
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
        .' target_list.`REF|AcquisitionImageData|image` AS image_id'
        .' FROM'
        .' ImageTargetListData target_list'
        .' WHERE'
        .' target_list.`REF|SessionData|session`='.$session
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
}

foreach(array_keys($images) as $image_id) {
    $image = &$images[$image_id];
    if(!is_null($image->parent_target_id)) {
        $parent_target = &$targets[$image->parent_target_id];
        $image->setParentTarget($parent_target);
        $parent_target->setChildImage($image);
    }
}

function printImage(&$image, $prefix='') {
    echo $prefix.'Image '.$image->id.'<br>';
    foreach(array_keys($image->child_target_lists) as $child_target_list_id) {
        $target_list = $image->child_target_lists[$child_target_list_id];
        printTargetList($target_list, $prefix.'___');
    }
}

function printTarget(&$target, $prefix='') {
    echo $prefix.'Target '.$target->id.'<br>';
    if(!is_null($target->child_image)) {
        printImage($target->child_image, $prefix.'___');
    }
}

function printTargetNumber(&$target_number, $prefix='') {
    echo $prefix.'Target #'.$target_number->number.'<br>';
    foreach(array_keys($target_number->targets) as $target_id) {
        $target = &$target_number->targets[$target_id];
        printTarget($target, $prefix.'___');
    }
}

function printTargetList(&$target_list, $prefix='') {
    echo $prefix.'TargetList '.$target_list->id.'<br>';
    foreach(array_keys($target_list->target_numbers) as $number) {
        $target_number = &$target_list->target_numbers[$number];
        printTargetNumber($target_number, $prefix.'___');
    }
}

foreach(array_keys($target_lists) as $target_list_id) {
    $target_list = &$target_lists[$target_list_id];
    printTargetList($target_list);
}

?>
