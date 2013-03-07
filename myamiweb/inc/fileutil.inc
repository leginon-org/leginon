<?php
require_once "inc/jpgraph_utils.inc.php";

class fileDataRead {
	var $aFile = '';
	var $aSepChar = ',';
	var $col_width = 1;

	function setFile($aFile,$aSepChar,$col_width) {
		if (!is_file($aFile)) return false;
		$this->aFile = $aFile;
		$this->aSepChar = $aSepChar;
		$this->col_width = $col_width;
		return true;
	}

	function getColumnFromArray($ar,$col_width,$col) {
		$outarray = array();
		foreach (range(0, count($ar)-1,$col_width) as $i) {
			$outarray[] = $ar[$i+$col];
		}
		return $outarray;
	}

	function getColumnFromCSV($col) {
		$jrf = new ReadFileData();
		$maxlength = 1024;
		$count = $jrf ->FromCSV($this->aFile,$aData,$this->aSepChar,$aMaxLineLength=$maxlength);
		return $this->getColumnFromArray($aData,$this->col_width,$col);
	}

}

?>
