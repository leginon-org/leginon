<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

define(MIN_PIXEL_VAL, 0); 
define(MAX_PIXEL_VAL, 255); 

class filter {


	var $filter_types = array (
				'default' => 'Default',
				'smooth1' => 'Smooth 1',
				'smooth2' => 'Smooth 2',
				'smooth3' => 'Smooth 3',
				'smooth4' => 'Smooth 4'
			);

	var $binning_types = array (
				'auto' => 'auto',
				1 => 1,
				2 => 2,
				3 => 3,
				4 => 4,
				5 => 5
			);

	function filter($filename="", $minpix="", $maxpix="", $binning=1) {
		$this->filename = $filename;
		$this->minpix = ($minpix) ? $minpix : MIN_PIXEL_VAL;
		$this->maxpix = ($maxpix) ? $maxpix : MAX_PIXEL_VAL;
		$this->binning = ($binning) ? $binning : 1;
	}

	function getFilterTypes() {
		return $this->filter_types;
	}

	function getBinningTypes() {
		return $this->binning_types;
	}

	function setFilename($filename) {
		$this->filename = $filename;
	}

	function setMinPixel($minpix) {
		$this->minpix = $minpix;
	}

	function setMaxPixel($maxpix) {
		$this->maxpix = $maxpix;
	}

	function setBinning($binning) {
		$this->binning = $binning;
	}

	function getFilter($type) {
		if (!is_file($this->filename))
			return false;
		if (!array_key_exists($type, $this->filter_types))
			return false;



		switch ($type) {
			case 'default':
				$img = imageCreateFromMRC (
						$this->filename, $this->minpix,
						$this->maxpix, $this->binning
						);
				break;

			case 'smooth1':
				$kernel = 5;
				$sigma = 2.73;
				$img = imageFilteredCreateFromMRC (
						$this->filename, $this->minpix,
						$this->maxpix, $this->binning,
						$kernel, $sigma
						);
				break;

			case 'smooth2':
				$kernel = 5;
				$sigma = 1;
				$img = imageFilteredCreateFromMRC (
						$this->filename, $this->minpix,
						$this->maxpix, $this->binning,
						$kernel, $sigma
						);
				$kernel = 3;
				$sigma = 2.12;
				imagefiltergaussian($img, $kernel, $sigma);
				break;

			case 'smooth3':
				$kernel = 3;
				$sigma = 1;
				$img = imageFilteredCreateFromMRC (
						$this->filename, $this->minpix,
						$this->maxpix, 2,
						$kernel, $sigma
						);
				imagescale($img, .5);
				$kernel = 3;
				$sigma = 1;
				imagefiltergaussian($img, $kernel, $sigma);
				break;

			case 'smooth4':
				$kernel = 5;
				$sigma = 1;
				$img = imageFilteredCreateFromMRC (
						$this->filename, $this->minpix,
						$this->maxpix, 1,
						$kernel, $sigma
						);
				imagescale($img, .5);
				break;

		}

		return $img;
	}

}
