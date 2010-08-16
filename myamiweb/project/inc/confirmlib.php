<?php
/**
 *
 *	table: confirm class:Confirm 
 *
 */

class Confirm {

	var $fieldc=9;
	var $fields=array('confirmId', 'projectId', 'duedate', 'deliverables', 'confirmnum', 'note', 'samplerequest', 'experimentrequest');

	function Confirm($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
	}

	function getConfirms($where=array()) {
		$params["table"]="confirm";
		$params["field"]=$this->fields;
		$params["where"]=$where;

		$info = $this->mysql->getData($params);
		return $info;
	}

	function getConfirmInfo($confirmId) { 
		$where["confirmId"]=$confirmId;
		$params["table"]="confirm";
		$params["field"]=$this->fields;
		$params["where"]=$where;

		list($info) = $this->mysql->getData($params);
		return $info;
	}

	function addConfirm($projectId, $duedate, $deliverables, $confirmnum, $note, $samplerequest, $experimentrequest) { 
		$table="confirm";
		$data["projectId"]=$projectId;
		$data["duedate"]=$duedate;
		$data["deliverables"]=$deliverables;
		$data["confirmnum"]=$confirmnum;
		$data["note"]=$note;
		$data["samplerequest"]=$samplerequest;
		$data["experimentrequest"]=$experimentrequest;
echo 'addconfirm';
print_r($data);
		$id =  $this->mysql->SQLInsert($table, $data);
		return $id;
	} 

	function updateConfirm($confirmId, $projectId, $duedate, $deliverables, $confirmnum, $note, $samplerequest, $experimentrequest) { 
		$table="confirm";
		$data["projectId"]=$projectId;
		$data["duedate"]=$duedate;
		$data["deliverables"]=$deliverables;
		$data["confirmnum"]=$confirmnum;
		$data["note"]=$note;
		$data["samplerequest"]=$samplerequest;
		$data["experimentrequest"]=$experimentrequest;

		$where["confirmId"]=$confirmId;
echo 'addconfirm';
print_r($data);

		$s = $this->mysql->SQLUpdate($table, $data, $where);
	} 

	function deleteConfirm($confirmId) { 
		$table="confirm";
		if (!$confirmId)
			return false;
		$q[]="delete from confirm where confirmId=".$confirmId;
		$this->mysql->SQLQueries($q);
	}

	function checkConfirmExistsbyId($confirmId) {
		$q="select confirmId from confirm where confirmId=".$confirmId;
		list($info) = $this->mysql->getSQLResult($q);
		$id = $info['confirmId'];
		return 	(empty($id)) ? false : $id;
	}

	function getNextNumber($projectId) {
		$p['table']='confirm';
		$p['field']=array('confirmId');
		$p['where']=array('projectId'=>$projectId);
		$n=$this->mysql->getData($p, $numrows=true);
		return $n+1;
	}

	function format_number($int){
		$newnumberstr="C".str_pad($int, 3, 0, STR_PAD_LEFT);
		return $newnumberstr;
	}

}
?>
