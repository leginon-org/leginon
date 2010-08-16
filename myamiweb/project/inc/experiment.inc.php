<?

class experimentdata {

	function experimentdata($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
	}

	function getExperimentsSourceIds() {
	}

	function getExperimentsSourceInfo($sourceId) {
	}

	function selectedExperimentsSQL($experimentIds, $name) {
	}

	function getSelectedExperiments($experimentIds) {
		return array();
	}

	function getExperiments() {
		$sqld = new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
		$q = "select DEF_id as `id`, name from SessionData order by DEF_timestamp DESC";
		return $sqld->SQLQuery($q);
	}

	function getNbImages() {
		$sqld = new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
		$qarray = array();
		$qarray[] = "select count(*) from AcquisitionImageData";
		$qarray[] = "select count(*) from AcquisitionFFTData";
		foreach ($qarray as $q) {
			$res = $sqld->SQLQuery($q);
			echo $sqld->getError();
			$row = mysql_fetch_row($res);
			$nb += $row[0];
		}
		return $nb;
	}

}

?>
