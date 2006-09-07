<?php

require_once('../config.php');
require_once('../inc/mysql.inc');

$session = $_GET['sessionId'];
if(!$session)
   exit('no session specified');

$mysql = new mysql($DB_HOST, $DB_USER, $DB_PASS, $DB);

$query = 'SELECT'
        .' target.DEF_id AS id,'
        .' target.status AS status,'
        .' target.number AS number,'
        .' target.version AS version,'
        .' target.type AS type,'
        .' target.`REF|ImageTargetListData|list` AS list,'
        .' image.DEF_id AS image,'
        .' image.`REF|AcquisitionImageTargetData|target` AS parent,'
        .' preset.name AS preset'
        .' FROM'
        .' AcquisitionImageTargetData target'
        .' LEFT JOIN'
        .' PresetData preset'
        .' ON'
        .' target.`REF|PresetData|preset`=preset.DEF_id'
        .' LEFT JOIN'
        .' AcquisitionImageData image'
        .' ON'
        .' target.`REF|AcquisitionImageData|image`=image.DEF_id'
        .' WHERE'
        .' target.`REF|SessionData|session`='.$session
        .';';

$results = $mysql->getSQLResult($query);

function getTargetLists(&$results) {
    $target_lists = array();
    foreach($results as $result) {
        $list = $result['list'];
        $number = $result['number'];
        if(is_null($list) or is_null($number))
            continue;
        $id = $result['id'];
        if(!array_key_exists($list, $target_lists))
            $target_lists[$list] = array();
        if(!array_key_exists($number, $target_lists[$list]))
            $target_lists[$list][$number] = array();
        $target_lists[$list][$number][] = $id;
    }
    return $target_lists;
}

$indexed_targets = array();
foreach($results as $result)
    $indexed_targets[$result['id']] = $result;

$target_lists = getTargetLists($results);

$latest_target_ids = array();
foreach($target_lists as $list_id => $list)
   foreach($list as $number => $target_list)
      $latest_target_ids[] = end($target_list);

class Target {
    var $list_id;
    var $number;
    var $parent;
    var $children;
    var $ids;

    function Target($list_id, $number) {
        $this->list_id = $list_id;
        $this->number = $number;
        $this->parent = null;
        $this->children = array();
        $this->ids = array();
    }

    function addChild(&$child) {
       $this->children[] = $child;
    }

    function setParent(&$parent) {
       $this->parent = $parent;
    }

    function addIDs(&$ids) {
       $this->ids = array_merge($this->ids, $ids);
    }

    function getColorTag($status) {
        $colors = array(
            'new' => 'green',
            'processing' => 'orange',
            'aborted' => 'red',
            'done' => 'blue',
            null => 'black',
        );
        if(array_key_exists($status, $colors))
           $color = $colors[$status];
        else
           $color = $colors[null];
        return '<font color="'.$color.'">';
    }

    function toString($prefix, &$indexed) {
        $string = '';
        if(is_null($prefix)) {
            $prefix = '';
        } else {
           $status = $indexed[end($this->ids)]['status'];
           $type = null;
           $preset = null;
           foreach($this->ids as $id) {
               if(is_null($type))
                   $type = $indexed[$id]['type'];
               elseif($type != $indexed[$id]['type']) {
                   $type = null;
                   break;
               }
               if(is_null($preset))
                   $preset = $indexed[$id]['preset'];
               elseif($preset != $indexed[$id]['preset']) {
                   $preset = null;
                   break;
               }
           }
           $string .= $this->getColorTag($status);
           $string .= $prefix;
           $string .= 'List ID: '.$this->list_id;
           $string .= ' #'.$this->number;
           $string .= ' Status: '.$status;
           if(!is_null($type))
               $string .= ' Type: '.$type;
           if(!is_null($preset))
               $string .= ' Preset: '.$preset;
           /*
           $string .= ' (';
           foreach($this->ids as $id) {
               $string .= ' ID: '.$id;
               $string .= ' Status: '.$indexed[$id]['status'];
               if(is_null($type))
                   $string .= ' Type: '.$indexed[$id]['type'];
               if(is_null($preset))
                   $string .= ' Preset: '.$indexed[$id]['preset'];
           }
           $string .= ' )';
           */
           $string .= '<br>';
           $prefix .= '________';
           $string .= '</font>';
       }
       foreach($this->children as $child)
          $string .= $child->toString($prefix, $indexed);
       return $string;
    }
}

function buildTargetListTree(&$parent_object, &$lists, &$indexed) {
    foreach(array_keys($lists) as $list_id) {
        foreach(array_keys($lists[$list_id]) as $number) {
            $ids = $lists[$list_id][$number];
            $parent_id = null;
            foreach($ids as $id) {
                $target = $indexed[$id];
                if(is_null($parent_id))
                    $parent_id = $target['parent'];
                elseif($parent_id != $target['parent'])
                    exit('parent target mismatch');
            }

            if(is_null($parent_id)) {
                if(!is_null($parent_object->list_id))
                  continue;
            } else {
                $parent = $indexed[$parent_id];
                $parent_list_id = $parent['list'];
                $parent_number = $parent['number'];
                if($parent_object->list_id != $parent_list_id)
                    continue;
                if($parent_object->number  != $parent_number)
                    continue;
            }

            $object = new Target($list_id, $number);
            $object->addIDs($ids);
            buildTargetListTree($object, $lists, $indexed);
            $object->setParent($parent_object);
            $parent_object->addChild($object);
        }
    }
}

$root = new Target(null, null);
buildTargetListTree($root, $target_lists, $indexed_targets);
$string = $root->toString(null, $indexed_targets);

?>
<html>
<head>
<title>
Target Test
</title>
</head>
<body>
<tt>
<?php echo $string; ?>
</tt>
</body>
</html>
