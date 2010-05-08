<?
class grid extends abstractgridbox {

	function grid($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
	}

	function format_date($mdy) {
		// --- month/day/year => YearMonthDay
		$date = explode('/', $mdy);
		return $date[2].'/'.$date[0].'/'.$date[1];
	}

	function updateGrid($gridId, $boxId, $projectId, $label, $prepdate, $specimen, $preparation, $number, $note) {

		if (!$this->checkGridExistsbyId($gridId)) 
			return false;

		$prepdate = $this->format_date($prepdate);

		$table="grids";
		$data['boxId']=$boxId;
		$data['projectId']=$projectId;
		$data['label']=$label;
		$data['prepdate']=$prepdate;
		$data['specimen']=$specimen;
		$data['preparation']=$preparation;
		$data['number']=$number;
		$data['note']=$note;

		$where['gridId']=$gridId;

		$s = $this->mysql->SQLUpdate($table, $data, $where);
	}

	function updateGridbox($gridId, $boxId) {

		$table="grids";
		$data['boxId']=$boxId;
		$where["gridId"]=$gridId;

		$s = $this->mysql->SQLUpdate($table, $data, $where);
	}

	function deleteGrid($gridId) {
		if (!$gridId)
			return false;
		$q[]='delete from grids where gridId='.$gridId;
		$q[]='delete from gridlocations where gridId='.$gridId;
		$this->mysql->SQLQueries($q);
	}

	function addGrid($boxId, $projectId, $label, $prepdate, $specimen, $preparation, $number, $note) {

		if (!$label) return 0;

		$prepdate = $this->format_date($prepdate);

		$table="grids";
		$data['boxId']=$boxId;
		$data['projectId']=$projectId;
		$data['label']=$label;
		$data['prepdate']=$prepdate;
		$data['specimen']=$specimen;
		$data['preparation']=$preparation;
		$data['number']=$number;
		$data['note']=$note;

		$re=$this->checkGridExistsbyName($label, $projectId);

		if (empty($re)) {
			$id =  $this->mysql->SQLInsert($table, $data);
			return $id;
		}
		return $re;
	}

	function checkGridExistsbyId($id) {
		$q=' select gridId from '.DB_PROJECT.'.grids where gridId="'.$id.'"';
		list($gridInfo) = $this->mysql->getSQLResult($q);
		$id = $gridInfo['gridId'];
		if(empty($id))
			return false;
		else
			return $id;
	}

	function checkGridExistsbyName($label, $projectId='') {
		$pjwhere = ($projectId>0) ? ' and projectId="'.$projectId.'"' : "";
		$q=' select gridId from grids where label="'.$label.'" '.$pjwhere;
		list($gridInfo) = $this->mysql->getSQLResult($q);
		return $gridInfo['gridId'];
	}

	function checkGridStored($id) {
		$q=' select gridboxId, location from gridlocations where '
		  .' gridId="'.$id.'" ';
		return $this->mysql->getSQLResult($q);
	}

	function syncGridLocations() {
		$q = 'select gridId from gridlocations';
		$locations=$this->mysql->getSQLResult($q);
		$del=array();
		foreach ($locations as $l) {
			$gridId = $l['gridId'];
			if (!$this->checkGridExistsbyId($gridId)) {
				$del[]='delete from gridlocations where gridId="'.$gridId.'"';
			}
		}
		$this->mysql->SQLQueries($del);
	}

	function getGridId($label){
		$q='select gridId from grid where label="'.$label.'"';
		return $this->mysql->getSQLResult($q);
	}

	function getGrids($projectId=0, $userId=""){
		if ($projectId > 0) {
				$where = ' p.`DEF_id`="'.$projectId.'"';
				$where .= ($userId) ? 'and po.`REF|leginondata|UserData|user`='.$userId : " ";
				$ujoin = ($userId) ? 'left join projectowner po on p.`DEF_id`=po.`REF|projects|project` ' :" ";
		} else {
			$where .= ($userId) ? ' po.`REF|leginondata|UserData|user`='.$userId : " 1";
			$ujoin = ($userId) ? 'left join projectowners po on p.`DEF_id`=po.`REF|projects|project` ' :" ";
		}
		$grids=array();
		$q=' select p.Name as project, g.gridId, g.label from grids g '
			.' left join projects p '
			.' on (p.`DEF_id`=g.projectId) '.$ujoin.' where '.$where
			.' or g.projectId = 0 ';
		$grids = $this->mysql->getSQLResult($q);
		return $grids;
	}

	function getGridInfo($gridId){
		$q='select g.gridId, label as "label", '
		  .'date_format(g.prepdate,"%m/%e/%Y") as prepdate, '
		  .'g.projectId, '
		  .'g.specimen, '
		  .'g.preparation, '
		  .'g.number, '
		  .'g.note, '
		  .'g.boxId, '
		  .'l.location, '
		  .'g.projectId '
		  .'from grids g '
		  .'left join gridlocations l '
		  .'on (l.gridId = g.gridId) '
		  .'where g.gridId="'.$gridId.'"';

		list($info) = $this->mysql->getSQLResult($q);
		return $info;
	}

}
?>
