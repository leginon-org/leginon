<?php


class histogram {

	var $minval;
	var $maxval;
	var $interval;
	var $nbbars = 50;
	var $maxcount = 1;
	var $data = array();
	var $debug = false;
	var $histogramdata = array();

	function histogram($data) {
		$this->data = $data;
		$this->minval = min($data);
		$this->maxval = max($data);
		$this->calculInterval();
	}

	function calculInterval() {
		$this->interval = ($this->maxval - $this->minval) / $this->nbbars;
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
		$start = microtime(true);
		for($k=0; $k<=$this->nbbars; $k++ ) {
			$classes[$k] = 0;
		}
		foreach($this->data as $datapt) {
			$k = (int) floor(($datapt - $this->minval)/$this->interval);
			//echo $k."<br/>\n";
			$classes[$k]++;
		}
		if ($classes)
			foreach ($classes as $k=>$nb) {
				if ($nb > $this->maxcount)
					$this->maxcount = $nb;
				$this->histogramdata['x'][] = $this->minval + ($k)*$this->interval;
				$this->histogramdata['y'][] = $nb;
			}

		$this->idealminx = (float) $this->minval-$this->interval;
		$this->idealmaxx = (float) $this->maxval+$this->interval;
		## find power of ten
		$this->factor = (int) pow(10, floor(log10($this->maxcount)-1));
		## set max based on power, e.g., 13426 -> 15000, 52 -> 70, or 425 -> 600
		if ($this->factor < 1) $this->factor=1;
		$this->idealmaxy = (int) ceil($this->maxcount/$this->factor+1)*$this->factor;


		if ($this->debug) {
			$end = microtime(true);
			echo "Min x ".$this->minval."<br/>\n";
			echo "Ideal min x ".$this->idealminx."<br/>\n";
			echo "Max x ".$this->maxval."<br/>\n";
			echo "Ideal max x ".$this->idealmaxx."<br/>\n";
			echo "Max y ".$this->maxcount."<br/>\n";
			echo "Max y factor ".$this->factor."<br/>\n";
			echo "Ideal max y ".$this->idealmaxy."<br/>\n";
			echo "#Bars ".$this->nbbars."<br/>\n";
			echo "Interval ".$this->interval."<br/>\n";
			echo "<br/>\n";
			echo print_r($this->data)."<br/><br/>\n";
			echo print_r($this->histogramdata['x'])."<br/><br/>\n";
			echo print_r($this->histogramdata['y'])."<br/><br/>\n";
			echo "TOTAL TIME: ".round(($end-$start)*1000, 3)." ms<br/><br/>\n";
			exit(1);
		}
	}

}
?>
