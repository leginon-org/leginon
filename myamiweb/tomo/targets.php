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
    var $target_list;
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
        $this->target_list = null;
        $this->parent_image = null;
        $this->child_image = null;
    }

    function setTargetList(&$target_list) {
        $this->target_list = $target_list;
    }

    function setParentImage(&$parent_image) {
        $this->parent_image = $parent_image;
    }

    function setChildImage(&$child_image) {
        $this->child_image = $child_image;
    }
}
class Image {
    var $id;
    var $preset;
    var $parent_target_id;
    var $parent_target;
    var $child_targets;

    function Image($array) {
        $this->id = $array['id'];
        $this->preset = $array['preset'];
        $this->parent_target_id = $array['target_id'];
        $this->parent_target = null;
        $this->child_targets = array();
    }

    function setParentTarget(&$parent_target) {
        $this->parent_target = $parent_target;
    }

    function addChildTarget(&$child_target) {
        $this->child_targets[$child_target->id] = &$child_target;
    }
}

class TargetList {
    var $id;
    var $targets;

    function TargetList($array) {
        $this->id = $array['id'];
        $this->targets = array();
    }

    function addTarget(&$target) {
        if(!array_key_exists($target->number, $this->targets))
            $this->targets[$target->number] = array();
        $this->targets[$target->number][$target->id] = &$target;
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
        .' target_list.DEF_id AS id'
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
        $target->setTargetList($target_list);
        $target_list->addTarget($target);
    }
    if(!is_null($target->parent_image_id)) {
        $parent_image = &$images[$target->parent_image_id];
        $target->setParentImage($parent_image);
        $parent_image->addChildTarget($target);
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

function printImage(&$image) {
    echo 'Image '.$image->id.'<br>';
    foreach(array_keys($image->child_targets) as $child_target_id) {
        $target = $image->child_targets[$child_target_id];
        printTarget($target);
    }
}

function printTarget(&$target) {
    echo 'Target '.$target->id.'<br>';
    if(!is_null($target->child_image)) {
        printImage($target->child_image);
    }
}

function printTargetList(&$target_list) {
    echo 'TargetList '.$target_list->id.'<br>';
    foreach(array_keys($target_list->targets) as $number) {
        echo '#'.$number.'<br>';
        $list_targets = &$target_list->targets[$number];
        foreach(array_keys($list_targets) as $list_target_id) {
            $list_target = &$list_targets[$list_target_id];
            printTarget($list_target);
        }
    }
}

foreach(array_keys($target_lists) as $target_list_id) {
    $target_list = &$target_lists[$target_list_id];
    printTargetList($target_list);
}

?>
