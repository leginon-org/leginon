<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/jpgraph.php";
require_once "inc/jpgraph_line.php";
require_once "inc/jpgraph_scatter.php";
require_once "inc/jpgraph_bar.php";
require_once "inc/jpgraph_log.php";
require_once "inc/histogram.inc";
require_once "inc/image.inc";

class dbemGraph {

	var $width=600;
	var $height=400;
	var $datax=array();
	var $datay=array();
	var $scatterplot=true;
	var $lineplot=true;
	var $markstart=false;
	var $extend2last=false;
	var $lastx=0.0;
	var $lasty=0.0;
	var $baselineplot=false;
	var $baselinevalue=0;
	var $manualscale=false;
	var $scaletype='linlin';

	function __construct($data, $xname, $yname) {
		$this->data=&$data;
		$this->xname=$this->xaxistitle=$xname;
		$this->yname=$this->yaxistitle=$yname;
		foreach($data as $t) {
			$this->datax[] = $t[$xname];
			$this->datay[] = $t[$yname];
		}
	}

	function proportion($margin,$intlimit=true) {
		$show_datax = $this->datax;
		$show_datay = $this->datay;
		if ($this->extend2last == true) {
			$show_datax[] = $this->lastx;
			$show_datay[] = $this->lasty;
		}
		$xmin = ($intlimit) ? floor(min($show_datax)):min($show_datax);
		$ymin = ($intlimit) ? floor(min($show_datay)):min($show_datay);
		$xmax = ($intlimit) ? ceil(max($show_datax)):max($show_datax);
		$ymax = ($intlimit) ? ceil(max($show_datay)):max($show_datay);
		$xrange = ($intlimit) ? ceil(($xmax-$xmin)/2)*2: $xmax-$xmin;
		$yrange = ($intlimit) ? ceil(($ymax-$ymin)/2)*2: $ymax-$ymin;
		$range = max($xrange,$yrange);
		$this->manualscale = true;
		$xmid = $xmin + $xrange / 2;
		$ymid = $ymin + $yrange / 2;
		$this->xmin = $xmid - $range * (0.5 + $margin);
		$this->ymin = $ymid - $range * (0.5 + $margin);
		$this->xmax = $xmid + $range * (0.5 + $margin);
		$this->ymax = $ymid + $range * (0.5 + $margin);
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

	function setScaleType($xtype='lin', $ytype='lin') {
		$this->scaletype = $xtype.$ytype;
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
			$bars_number = intval(sqrt(count($this->datax))) + 10;
			$histogram->setBarsNumber($bars_number);
			$rdata = $histogram->getData();
			$rdatax = $rdata['x'];
			$rdatay = $rdata['y'];

			$graph->SetScale("linlin");
			$left_margin = 45;
			$right_margin = 30;
			$graph->img->SetMargin($left_margin,$right_margin,25,40);

			$bplot = new BarPlot($rdatay, $rdatax);
			$bwidth = $histogram->getBarWidth($this->width,$left_margin,$right_margin);
			$bplot->SetWidth($bwidth);
			$bplot->SetFillColor('#B0C4DE');
			$graph->Add($bplot);

			$graph->title->Set("histogram: ".$this->title);
			$graph->xaxis->title->Set($this->yaxistitle);
			$graph->yaxis->title->Set("Frequency (".$bars_number." bars)");
		} else {
			// x,y plot
			$graph->img->SetMargin(50,30,30,60);
			$graph->title->Set($this->title);
			$graph->subtitle->Set($this->subtitle);
			$graph->SetAlphaBlending();

			$graph->SetScale($this->scaletype); 
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

			if ($this->manualscale)
				$graph->SetScale($this->scaletype,$this->ymin,$this->ymax,$this->xmin,$this->xmax);
			if ($this->extend2last) {
				$c = count($this->datay);
				$yarray = array_merge($this->datay,array($this->lasty));
				$xarray = array_merge($this->datax,array($this->lastx));
				$p3 = new LinePlot($yarray,$xarray);
				$p3->SetColor("blue");
				$p3->SetStyle("dotted");
				$graph->Add($p3);
				// last point
				$sp3 = new ScatterPlot(array($this->lasty),array($this->lastx));
				$sp3->mark->SetType(MARK_FILLEDCIRCLE);
				$sp3->mark->SetColor('red');
				$sp3->mark->SetFillColor('red');
				$sp3->mark->SetWidth(3);
				$graph->Add($sp3);
			}
			if ($this->xname!="unix_timestamp") {
				$xscale = $this->xmax-$this->xmin;
				$xscale = ($xscale == 0) ? max($this->datax) - min($this->datax):$xscale;
			}
			$yscale = $this->ymax-$this->ymin;
			$yscale = ($yscale == 0) ? max($this->datay) - min($this->datay):$yscale;
			if ($xscale >=10 && $xscale < 100) {
				//This get around a bug in jpgraph that shows numbers as 0f in this scale range.
				$graph->xaxis->SetLabelFormatString('%0.0f');
			}
			if ($yscale >=10 && $yscale < 100) {
				//This get around a bug in jpgraph that shows numbers as 0f in this scale range.
				$graph->yaxis->SetLabelFormatString('%0.0f');
			}

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

			if ($this->baselineplot) {
				$yarray = array($this->baselinevalue,$this->baselinevalue);
				$xarray = array(min($this->datax),max($this->datax));
				$p2 = new LinePlot($yarray,$xarray);
				$p2->SetColor("blue");
				$graph->Add($p2);
			}

			if ($this->markstart) {
				$sp2 = new ScatterPlot(array($this->datay[0]),array($this->datax[0]));
				$sp2->mark->SetType(MARK_FILLEDCIRCLE);
				$sp2->mark->SetColor('blue');
				$sp2->mark->SetWidth(4);
				$graph->Add($sp2);
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
