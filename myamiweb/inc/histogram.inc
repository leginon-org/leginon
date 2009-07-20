<?php


class histogram {

	var $minval;
	var $maxval;
	var $interval;
	var $nbbars = 50;
	var $data = array();
	var $histogramdata = array();

	function histogram($data) {
		$this->data = $data;
		$this->minval = min($data);
		$this->maxval = max($data);
		$this->calculInterval();
	}

	function calculInterval() {
		$this->interval = ($this->maxval - $this->minval) / ($this->nbbars-1);
	}

	function setInterval($n) {
		$this->interval = $n;
	}

	function setBarsNumber($n) {
		if ($n>0)
			$this->nbbars = $n;
		$this->calculInterval();
	}

	function getData() {
		$this->generateData();
		return $this->histogramdata;
	}

	function generateData() {
		for($k=0; $k<$this->nbbars; $k++ ) {
			$classes[$k] = 0;
			foreach($this->data as $data) {
				$i1 = ($this->minval+($k-1)*$this->interval);
				$i2 = ($this->minval+$k*$this->interval);
				if ($data > $i1 && $data <= $i2)
					$classes[$k]++;
			}
		}
		if ($classes)
			foreach ($classes as $k=>$nb) {
				$this->histogramdata['x'][] = $this->minval+$k*$this->interval;
				$this->histogramdata['y'][] = $nb;
			}
	}

}
?>
