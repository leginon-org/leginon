<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

class mrc {
	var $MRC_HEADER_SIZE = 1024;
	var $MRC_BYTE_PER_PIX = 4;
	function imagecreatefromMRC ($file, $width="", $height="", $minpix="", $maxpix="", $quality="") {
		$opts = array();
		if ($width && $height)
			$opts[]="--size=".$width."x".$height;
		if ($minpix)
			$opts[]="--min=$minpix";
		if ($maxpix)
			$opts[]="--max=$maxpix";
		if ($quality)
			$opts[]="--quality=$quality";
			
		$img_cmd = "python -OO ./py/mrc2jpg2out.py ".implode(" ",$opts)." \"$file\"";
		// --- copy $pic into a buffer $imgbuffer
		ob_start();
		passthru($img_cmd);
		$imgbuffer = ob_get_contents();
		ob_end_clean();

		// --- create an image resource from $imgbuffer
		$img = imagecreatefromstring($imgbuffer);
		unset($imgbuffer);
		return $img;
	}

	function imagecreatefromMRC2 ($file, $width="", $height="", $minpix="", $maxpix="", $quality="") {
		$opts = array();
		if ($width && $height)
			$opts[]="--size=".$width."x".$height;
		if ($minpix)
			$opts[]="--min=$minpix";
		if ($maxpix)
			$opts[]="--max=$maxpix";
		if ($quality)
			$opts[]="--quality=$quality";
			
		$img_cmd = "python -OO ./py/mrc2jpg2out_new.py ".implode(" ",$opts)." \"$file\"";

		// --- copy $pic into a buffer $imgbuffer
		ob_start();
		passthru($img_cmd);
		$imgbuffer = ob_get_contents();
		ob_end_clean();

		// --- create an image resource from $imgbuffer
		$img = imagecreatefromstring($imgbuffer);
		unset($imgbuffer);
		return $img;
	}

	function getSize($file) {
		$hs = $this->MRC_HEADER_SIZE;
		$bs = $this->MRC_BYTE_PER_PIX;
		$fs = filesize($file);
		$mrcsize = floor(sqrt(($fs-$hs)/$bs));
		return $mrcsize;
	}
}
$mrc = new mrc
?>
