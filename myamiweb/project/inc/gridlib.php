<?php
/**
 *
 *	table: ngrid class:Grid 
 *
 */

class Grid {

	var $fieldc=23;
	var $fields=array('gridId', 'projectId', 'sampleId', 'number', 'grsubstrate', 'volume', 'datemade', 'comments', 'dilution', 'type', 'plasma', 'vitrobotblot', 'vitrobotoffset', 'vitrobottemp', 'vitrobotrh', 'stored', 'stain', 'stainconc', 'waterwash', 'stainwash', 'stainvolume', 'grbox', 'grboxslot');



	function Grid($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
	}

	function getGrids($where=array(), $fields=array()) {
		if (!$fields)
			$fields=$this->fields;
		$fields['number']="CONCAT(`TYPE`, LPAD(`number`, 3,'0')) `number`";
		$fields['grbox']="CONCAT(if(`TYPE`='V','G','B'), LPAD(`grbox`, 3,'0')) `grbox`";
		$params["table"]="ngrid";
		$params["field"]=$fields;
		$params["where"]=$where;

		$info = $this->mysql->getData($params);
		return $info;
	}

	function getGridInfo($gridId) { 
		$where["gridId"]=$gridId;
		$params["table"]="ngrid";
		$params["field"]=$this->fields;
		$params["where"]=$where;

		list($info) = $this->mysql->getData($params);
		return $info;
	}

	function addGrid($projectId, $sampleId, $number, $grsubstrate, $volume, $datemade, $comments, $dilution, $type, $plasma, $vitrobotblot, $vitrobotoffset, $vitrobottemp, $vitrobotrh, $stored, $stain, $stainconc, $waterwash, $stainwash, $stainvolume, $grbox, $grboxslot) { 
		$table="ngrid";
		$data["projectId"]=$projectId;
		$data["sampleId"]=$sampleId;
		$data["number"]=$number;
		$data["grsubstrate"]=$grsubstrate;
		$data["volume"]=$volume;
		$data["datemade"]=$datemade;
		$data["comments"]=$comments;
		$data["dilution"]=$dilution;
		$data["type"]=$type;
		$data["plasma"]=$plasma;
		$data["vitrobotblot"]=$vitrobotblot;
		$data["vitrobotoffset"]=$vitrobotoffset;
		$data["vitrobottemp"]=$vitrobottemp;
		$data["vitrobotrh"]=$vitrobotrh;
		$data["stored"]=$stored;
		$data["stain"]=$stain;
		$data["stainconc"]=$stainconc;
		$data["waterwash"]=$waterwash;
		$data["stainwash"]=$stainwash;
		$data["stainvolume"]=$stainvolume;
		$data["grbox"]=$grbox;
		$data["grboxslot"]=$grboxslot;

		$id =  $this->mysql->SQLInsert($table, $data);
		return $id;
	} 

	function updateGrid($gridId, $sampleId, $number, $grsubstrate, $volume, $datemade, $comments, $dilution, $type, $plasma, $vitrobotblot, $vitrobotoffset, $vitrobottemp, $vitrobotrh, $stored, $stain, $stainconc, $waterwash, $stainwash, $stainvolume, $grbox, $grboxslot) { 
		$table="ngrid";
		$data["sampleId"]=$sampleId;
		$data["number"]=$number;
		$data["grsubstrate"]=$grsubstrate;
		$data["volume"]=$volume;
		$data["datemade"]=$datemade;
		$data["comments"]=$comments;
		$data["dilution"]=$dilution;
		$data["type"]=$type;
		$data["plasma"]=$plasma;
		$data["vitrobotblot"]=$vitrobotblot;
		$data["vitrobotoffset"]=$vitrobotoffset;
		$data["vitrobottemp"]=$vitrobottemp;
		$data["vitrobotrh"]=$vitrobotrh;
		$data["stored"]=$stored;
		$data["stain"]=$stain;
		$data["stainconc"]=$stainconc;
		$data["waterwash"]=$waterwash;
		$data["stainwash"]=$stainwash;
		$data["stainvolume"]=$stainvolume;
		$data["grbox"]=$grbox;
		$data["grboxslot"]=$grboxslot;

		$where["gridId"]=$gridId;

		$s = $this->mysql->SQLUpdate($table, $data, $where);
	} 

	function deleteGrid($gridId) { 
		$table="ngrid";
		if (!$gridId)
			return false;
		$q[]="delete from ngrid where gridId=".$gridId;
		$this->mysql->SQLQueries($q);
	}

	function checkGridExistsbyId($gridId) {
		$q="select gridId from ngrid where gridId=".$gridId;
		list($info) = $this->mysql->getSQLResult($q);
		$id = $info['gridId'];
		return 	(empty($id)) ? false : $id;
	}

	function getNextNumber($sampleId, $gridtype, $gbox=false) {
		$where = array('sampleId'=>$sampleId, 'type'=>$gridtype);
		if ($gbox)
			$where['grbox']=$gbox;
		$p['table']="ngrid";
		$p['field']=array('gridId');
		$p['where']=$where;
		$n=$this->mysql->getData($p, $numrows=true);
		return $n+1;
	}

	function getNextGridBoxNumber($sampleId, $type='V') {
		$p['table']="ngrid";
		$p['field']=array('grbox'=>"max(grbox) as `n`");
		$p['where']=array('sampleId'=>$sampleId, 'type'=>$type);
		list($r)=$this->mysql->getData($p);
		return $r['n']+1;
	}

	function format_number($int, $prefix="G"){
		$newnumberstr=$prefix.str_pad($int, 3, 0, STR_PAD_LEFT);
		return $newnumberstr;
	}

	function getGridId($info) {
		$name=$info['Name'];
		list($proj, $packagenb, $samplenb, $grbox, $gnumber) = explode(".", $info['Purpose']);
		$packagenb = (int) ereg_replace("P", "", $packagenb);
		$samplenb = (int) ereg_replace("S", "", $samplenb);
		$grboxnb = (int) ereg_replace("^[[:alpha:]]{1}", "", $grbox);
		if (ereg("(^[[:alpha:]]{1})([0-9]{1,})", $gnumber, $r)) {
			$type=$r[1];
			$gnumber=(int)$r[2];
		}
		$q='select g.gridId '
		.'from project.ngrid g '
		.'left join project.nsample s on (s.sampleId=g.sampleId)
		left join project.npackage p on (p.packageId=s.packageId)
		left join project.projects pr on (pr.projectId=p.projectId)
		left join project.projectexperiments pe on (pe.projectId=pr.projectId)
		where
		pe.name="'.$name.'"
		and p.`number`="'.$packagenb.'"
		and s.`number`="'.$samplenb.'"
		and g.`grbox`="'.$grboxnb.'"
		and g.`type`="'.$type.'"
		and g.`number`="'.$gnumber.'"
		';
		list($res)=$this->mysql->getSQLResult($q);
		return $res['gridId'];
	}

	function getGridsFromPackage($packageId) {
		$fields=$this->fields;
		$fields['number']="CONCAT(`TYPE`, LPAD(g.`number`, 3,'0')) `number`";
		$fields['grbox']="CONCAT(if(`TYPE`='V','G','B'), LPAD(`grbox`, 3,'0')) `grbox`";
		$sqlselect = $this->mysql->array_to_select($fields, 'g');
		$q='select '.$sqlselect.' '
		.'from '.DB_PROJECT.'.ngrid g '
		.'left join '.DB_PROJECT.'.nsample s on (s.sampleId=g.sampleId) '
		.'where '
		.'s.`packageId`="'.$packageId.'"';
		return $this->mysql->getSQLResult($q);
	}
}
?>
