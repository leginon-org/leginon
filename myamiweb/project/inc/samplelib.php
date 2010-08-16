<?php
/**
 *
 *	table: nsample class:Sample 
 *
 */

class Sample {

	var $fieldc=10;
	var $fields=array('sampleId', 'packageId', 'number', 'label', 'volume', 'description', 'concentration1', 'concentration2', 'stored', 'notes');

	function Sample($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
	}

	function getSamples($where=array(), $fields=array()) {
		if (!$fields)
			$fields=$this->fields;
		$fields['number']="CONCAT('S', LPAD(`number`, 3,'0')) `number`";
		$params["table"]="nsample";
		$params["field"]=$fields;
		$params["where"]=$where;

		$info = $this->mysql->getData($params);
		return $info;
	}

	function getSampleInfo($sampleId) { 
		$where["sampleId"]=$sampleId;
		$params["table"]="nsample";
		$params["field"]=$this->fields;
		$params["where"]=$where;

		list($info) = $this->mysql->getData($params);
		return $info;
	}

	function addSample($projectId, $packageId, $number, $label, $volume, $description, $concentration1, $concentration2, $stored, $notes) { 
		$table="nsample";
		$data["projectId"]=$projectId;
		$data["packageId"]=$packageId;
		$data["number"]=$number;
		$data["label"]=$label;
		$data["volume"]=$volume;
		$data["description"]=$description;
		$data["concentration1"]=$concentration1;
		$data["concentration2"]=$concentration2;
		$data["stored"]=$stored;
		$data["notes"]=$notes;

		$id =  $this->mysql->SQLInsert($table, $data);
		return $id;
	} 

	function updateSample($sampleId, $packageId, $label, $volume, $description, $concentration1, $concentration2, $stored, $notes) { 
		$table="nsample";
		$data["packageId"]=$packageId;
		$data["label"]=$label;
		$data["volume"]=$volume;
		$data["description"]=$description;
		$data["concentration1"]=$concentration1;
		$data["concentration2"]=$concentration2;
		$data["stored"]=$stored;
		$data["notes"]=$notes;

		$where["sampleId"]=$sampleId;

		$s = $this->mysql->SQLUpdate($table, $data, $where);
	} 

	function deleteSample($sampleId) { 
		$table="nsample";
		if (!$sampleId)
			return false;
		$q[]="delete from nsample where sampleId=".$sampleId;
		$this->mysql->SQLQueries($q);
	}

	function checkSampleExistsbyId($sampleId) {
		$q="select sampleId from nsample where sampleId=".$sampleId;
		list($info) = $this->mysql->getSQLResult($q);
		$id = $info['sampleId'];
		return 	(empty($id)) ? false : $id;
	}

	function getNextNumber($packageId, $projectId='') {
		$p['table']="nsample";
		$p['field']=array('sampleId');
		$where['packageId']=$packageId;
		if (is_numeric($projectId)) {
			$where['projectId']=$projectId;
		}
		$p['where']=$where;
		$n=$this->mysql->getData($p, $numrows=true);
		return $n+1;
	}

	function format_number($int){
		$newnumberstr="S".str_pad($int, 3, 0, STR_PAD_LEFT);
		return $newnumberstr;
	}

	function hasInternalPackage($projectId) {
		$p['table']="nsample";
		$p['field']=array('sampleId');
		$where['packageId']=null;
		$where['projectId']=$projectId;
		$p['where']=$where;
		$n=$this->mysql->getData($p, $numrows=true);
		return $n;
	}

}
?>
