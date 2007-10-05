<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/jpgraph.php";
require "inc/jpgraph_line.php";
require "inc/jpgraph_scatter.php";
require "inc/jpgraph_bar.php";
require "inc/histogram.inc";
require "inc/image.inc";

class dbemGraph {

	var $width=600;
	var $height=400;
	var $datax=array();
	var $datay=array();
	var $scatterplot=true;
	var $lineplot=true;

	function dbemGraph($data, $xname, $yname) {
		$this->data=&$data;
		$this->xname=$this->xaxistitle=$xname;
		$this->yname=$this->yaxistitle=$yname;
		foreach($data as $t) {
			$this->datax[] = $t[$xname];
			$this->datay[] = $t[$yname];
		}
	}

	function scale(&$d) {
		$d=array_map(array($this, 'scale_map'), $d);
	}

	function scale_map($val) {
		$scale=($this->scalefactor) ? $this->scalefactor : 1;
		return $val/$scale;
	}

	function scalex($factor) {
		$this->scalefactor=$factor;
		$this->scale($this->datax);
	}

	function scaley($factor) {
		$this->scalefactor=$factor;
		$this->scale($this->datay);
	}

	function dim($w,$h) {
		$this->resample_width=$w;
		$this->resample_height=$h;
	}

	function dumpData($keys="") {
		if (!$keys)
			$keys=array($this->xname, $this->yname);
		echo dumpData($this->data, $keys);
		exit;
	}

	function graph() {
		if (!$this->datay) {
			$this->resample_width = 12;
			$this->resample_height = 12;
			$source = blankimage($this->resample_width,$this->resample_height);
		} else {
		$graph = new Graph($this->width, $this->height,"auto");    
		if ($this->histogram) {
			$histogram = new histogram($this->datay);
			$histogram->setBarsNumber(50);
			$rdata = $histogram->getData();

			$rdatax = $rdata['x'];
			$rdatay = $rdata['y'];

			$graph->SetScale("linlin");
			$graph->img->SetMargin(40,30,20,40);

			$bplot = new BarPlot($rdatay, $rdatax);
			$graph->Add($bplot);

			$graph->title->Set("histogram: ".$this->title);
			$graph->xaxis->title->Set($this->yaxistitle);
			$graph->yaxis->title->Set("Frequency");
		} else {
			$graph->img->SetMargin(50,30,30,60);
			$graph->title->Set($this->title);
			$graph->SetAlphaBlending();
			$graph->SetScale("linlin"); 
			$xname=$this->xaxistitle;
			if ($this->xname=="unix_timestamp") {
				$graph->xaxis->SetLabelFormatCallback('timeCallback');
				$xname="time";
			}
			$graph->xaxis->SetPos("min");
			$graph->xaxis->SetLabelAngle(90);
			$graph->xaxis->SetTitlemargin(25);
			$graph->xaxis->title->Set($xname);
			$graph->yaxis->SetTitlemargin(35);
			$graph->yaxis->title->Set($this->yaxistitle);
			$graph->yaxis->SetTextLabelInterval(3);
			if ($scientic_notation)
				$graph->yaxis->SetLabelFormatCallback('sciCallback');

			if ($this->scatterplot) {
				$sp1 = new ScatterPlot($this->datay,$this->datax);
				$sp1->mark->SetType(MARK_CIRCLE);
				$sp1->mark->SetColor('red');
				$sp1->mark->SetWidth(4);
				$graph->Add($sp1);
			}

			if ($this->lineplot) {
				$p1 = new LinePlot($this->datay,$this->datax);
				$p1->SetColor("blue");
				$graph->Add($p1);
			}
		}
		$source = $graph->Stroke(_IMG_HANDLER);
		}
		resample($source, $this->resample_width, $this->resample_height);
	}
}

function timeCallback($timestamp) {
	return date('H:i',$timestamp);
}

function sciCallback($n) {
	return format_sci_number($n,$decimal=2,true);
}

?>
