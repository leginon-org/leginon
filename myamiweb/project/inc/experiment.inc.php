<?

class experimentdata {

	function experimentdata($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB);
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

	function getExperiments($sourceId) {
	}

	function getNbImages($sourceId) {
	}

}

?>
