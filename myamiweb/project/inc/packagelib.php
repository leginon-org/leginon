<?php
/**
 *
 *	table: npackage class:Package 
 *
 */

class Package {

	var $fieldc=19;
	var $fields=array('packageId', 'projectId', 'confirmId', 'number', 'label', 'expdate', 'expcarrier', 'carriernumber', 'expnumaliquots', 'sampledescription', 'expnote', 'arrivedate', 'arrivetime', 'condition', 'shipmethod', 'temp', 'numaliquots', 'notified', 'note');

	function Package($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
	}

	function getPackages($where=array(), $fields=array()) {
		if (!$fields)
			$fields=$this->fields;
		$fields['number']="CONCAT('P', LPAD(`number`, 3,'0')) `number`";
		$params["table"]="npackage";
		$params["field"]=$fields;
		$params["where"]=$where;

		$info = $this->mysql->getData($params);
		return $info;
	}

	function getPackageInfo($packageId) { 
		$where["packageId"]=$packageId;
		$params["table"]="npackage";
		$params["field"]=$this->fields;
		$params["where"]=$where;

		list($info) = $this->mysql->getData($params);
		return $info;
	}

	function addPackage($projectId, $confirmId, $number, $label, $expdate, $expcarrier, $carriernumber, $expnumaliquots, $sampledescription, $expnote, $arrivedate, $arrivetime, $condition, $shipmethod, $temp, $numaliquots, $notified, $note) { 
		$table="npackage";
		$data["projectId"]=$projectId;
		$data["confirmId"]=$confirmId;
		$data["number"]=$number;
		$data["label"]=$label;
		$data["expdate"]=$expdate;
		$data["expcarrier"]=$expcarrier;
		$data["carriernumber"]=$carriernumber;
		$data["expnumaliquots"]=$expnumaliquots;
		$data["sampledescription"]=$sampledescription;
		$data["expnote"]=$expnote;
		$data["arrivedate"]=$arrivedate;
		$data["arrivetime"]=$arrivetime;
		$data["condition"]=$condition;
		$data["shipmethod"]=$shipmethod;
		$data["temp"]=$temp;
		$data["numaliquots"]=$numaliquots;
		$data["notified"]=$notified;
		$data["note"]=$note;

		$id =  $this->mysql->SQLInsert($table, $data);
		return $id;
	} 

	function updatePackage($packageId, $projectId, $confirmId, $label, $expdate, $expcarrier, $carriernumber, $expnumaliquots, $sampledescription, $expnote, $arrivedate, $arrivetime, $condition, $shipmethod, $temp, $numaliquots, $notified, $note) { 
		$table="npackage";
		$data["projectId"]=$projectId;
		$data["confirmId"]=$confirmId;
		$data["label"]=$label;
		$data["expdate"]=$expdate;
		$data["expcarrier"]=$expcarrier;
		$data["carriernumber"]=$carriernumber;
		$data["expnumaliquots"]=$expnumaliquots;
		$data["sampledescription"]=$sampledescription;
		$data["expnote"]=$expnote;
		$data["arrivedate"]=$arrivedate;
		$data["arrivetime"]=$arrivetime;
		$data["condition"]=$condition;
		$data["shipmethod"]=$shipmethod;
		$data["temp"]=$temp;
		$data["numaliquots"]=$numaliquots;
		$data["notified"]=$notified;
		$data["note"]=$note;

		$where["packageId"]=$packageId;

		$s = $this->mysql->SQLUpdate($table, $data, $where);
	} 

	function deletePackage($packageId) { 
		$table="npackage";
		if (!$packageId)
			return false;
		$q[]="delete from npackage where packageId=".$packageId;
		$this->mysql->SQLQueries($q);
	}

	function checkPackageExistsbyId($packageId) {
		$q="select packageId from npackage where packageId=".$packageId;
		list($info) = $this->mysql->getSQLResult($q);
		$id = $info['packageId'];
		return 	(empty($id)) ? false : $id;
	}

	function getNextNumber($projectId) {
		$p['table']="npackage";
		$p['field']=array('packageId');
		$p['where']=array('projectId'=>$projectId);
		$n=$this->mysql->getData($p, $numrows=true);
		return $n+1;
	}

	function format_number($int){
		$newnumberstr="P".str_pad($int, 3, 0, STR_PAD_LEFT);
		return $newnumberstr;
	}

}
?>
