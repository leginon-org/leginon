<?php
/*
 * Date: 3/10/2011
 * Author: Eric Hou
 * 
 * Test redux url: http://bnc16/redux.php
 * 
 * example: filename=/ami/exdata/leginon/10mar30z/rawdata/Data0308.mrc
 * 					&padshape=4096x4096&power=1&maskradius=50&shape=512x512
 * 					&scaletype=cdf&scalemin=0.8&scalemax=0.98&oformat=JPEG
 */
require_once 'formValidator.php';

define("SERVER_HOST", "");
define("SERVER_POST", "");

$validator = new formValidator();

class redux{
	private $filename;		//input image filename with full location path.
	private $padShape;		// need to be x, y array
	private $padPos;		// need to be x, y array
	private $padValue;		// float
	private $power;			// boolean
	private $maskRadius;	// float 
	private $shape;			// x, y array
	private $lpf;			// low pass filter, float
	private $scaleMin;		// float
	private $scaleMax;		// float
	private $scaleType;		// image scale type [choices ("minmax", "stdev", "cdf")]
	private $oFormat;		// image output format [choices: ('JPEG', 'GIF', 'TIFF', 'PNG', 'MRC')]
	private $errMsg;		// error message array contain name - message pair.
	
	
	/*
	 * default constructor requires at lease image input location
	 * and output format
	 */
	function __construct($filename, $oFormat){
		
		$this->setFilename($filename);	
		$this->setOFormat($oFormat);	
	
	}
	
	/*
	 * Getter for all the local variables
	 */
	function getFilename()		{ return $this->filename; }
	
	function getPadShape(){ 
		return $this->padShape[0] . 'x' . $this->padShape[1];
	}
	
	function getPadPos(){ 
		return $this->padPos[0] . 'x' . $this->padPos[1]; 
	}
	
	function getPadValue() 		{ return $this->padValue; }
	
	function getPower(){
		$str = $this->power ? '1' : '0'; 
		return $str;
	}
	
	function getMaskRadius() 	{ return $this->maskRadius; }
	
	function getShape(){ 
		return $this->shape[0]. 'x' . $this->shape[1]; 
	}
	
	function getLpf() 			{ return $this->lpf; }
	function getScaleMin() 		{ return $this->scaleMin; }
	function getScaleMax() 		{ return $this->scaleMax; }
	function getScaleType() 	{ return $this->scaleType; }
	function getOFormat() 		{ return $this->oFormat; }
	
	function getErrMsg(){ 
		$this->validateInputs();
		return $this->errMsg; 
	}
	
	function setFilename($filename){
		
		global $validator;
		$validator->addValidation("filename", $filename, "file_exist", "MRC image file does not exist.");
		$this->filename = $filename; 
	}
	
	function setPadShape($padShape){ 
		
		global $validator;

		if(!is_array($padShape) || (count($padShape) != 2)) 
			$validator->setErrorMessage("padShape", "Pad shape must be an array and contain two elements (x, y).");
		
		$validator->addValidation("padShapeX", $padShape[0], "num", "Pad shape X value must be a positive integer.");
		$validator->addValidation("padShapeY", $padShape[1], "num", "Pad shape Y value must be a positive integer.");
		$this->padShape = $padShape; 
	}
	
	function setPadPos($padPos){ 
		
		global $validator;
		
		if(!is_array($padPos) || (count($padPos) != 2)) 
			$validator->setErrorMessage("padPos", "Pad position must be an array and contain two elements (x, y).");
		
		$validator->addValidation("padPosX", $padPos[0], "num", "Pad position X value must be a positive integer.");
		$validator->addValidation("padPosY", $padPos[1], "num", "Pad position Y value must be a positive integer.");
		$this->padPos = $padPos; 
	}
	
	function setPadValue($padValue){ 
		
		global $validator;
		$validator->addValidation("padValue", $padValue, "num", "Pad value must be an integer.");
		$this->padValue = $padValue; 
	}
	
	function setPower($power){ 
		
		global $validator;
		if(!is_bool($power))
			$validator->setErrorMessage("power", "The value of power must be boolean (true, flase).");
		
		$this->power = $power; 
	}
	
	function setMaskRadius($maskRadius){ 
		
		global $validator;
		$validator->addValidation("maskRadius", $maskRadius, "float", "Mask Radius value must be a float.");
		$this->maskRadius = $maskRadius; 
	}
	
	function setShape($shape){ 
		
		global $validator;
		
		if(!is_array($shape) || (count($shape) != 2)) 
			$validator->setErrorMessage("shape", "Shape must be an array and contain two elements (x, y).");
			
		$validator->addValidation("shapeX", $shape[0], "num", "Shape X value must be a positive integer.");
		$validator->addValidation("shapeX", $shape[1], "num", "Shape Y value must be a positive integer.");
		$this->shape = $shape; 
	}
	
	function setLpf($lpf){ 
		
		global $validator;
		$validator->addValidation("lpf", $lpf, "float", "lpf value must be a float.");
		$this->lpf = $lpf; 
	}
	
	function setScaleMin($scaleMin){ 
		
		global $validator;
		$validator->addValidation("scaleMin", $scaleMin, "float", "scale minimum value must be a float.");
		$this->scaleMin = $scaleMin; 
	}
	
	function setScaleMax($scaleMax){ 
		
		global $validator;
		$validator->addValidation("scaleMax", $scaleMax, "float", "scale maximum value must be a float.");
		$this->scaleMax = $scaleMax; 
	}
	
	/*
	 * choices ("minmax", "stdev", "cdf")
	 */
	function setScaleType($scaleType){ 
		
		global $validator;
		$validator->addValidation("scaleType", $scaleType, "req", "Image scale type is required.");
		
		switch($scaleType){
			case "minmax":
			case "stdev":
			case "cdf":
				break;
			default:
				$validator->setErrorMessage("scaleType", "Image scale type can only be \"minmax\", \"stdev\", or \"cdf\".");
		}
		
		
		$this->scaleType = $scaleType; 
	}
	
	/*
	 * choices:  {'JPEG': '.jpg', 'GIF': '.gif', 'TIFF': '.tif', 'PNG': '.png', 'MRC': '.mrc'}
	 */
	function setOFormat($oFormat){ 
		
		global $validator;
		$validator->addValidation("oFormat", $oFormat, "req", "Image output format is required.");
		
		switch($oFormat){
			case "JPEG":
			case "GIF":
			case "TIFF":
			case "PNG":
			case "MRC":
				break;
			default:
				$validator->setErrorMessage("oFormat", "Image output format can only be \"JPEG\", \"GIF\", \"TIFF\", \"PNG\", or \"MRC\".");
		}
		$this->oFormat = $oFormat; 
	}
	
	function validateInputs(){
		global $validator;
		$validator->runValidation();
		$this->errMsg = $validator->getErrorMessage();
	}
	
	function requestString(){

		$str = 'filename=' . $this->getFilename();
		$str .= empty($this->padShape) ? '' : '&padshape=' . $this->getPadShape();
		$str .= empty($this->power) ? '' : '&power=' . $this->getPower();
		$str .= empty($this->maskRadius) ? '' : '&maskradius=' . $this->getMaskRadius();
		$str .= empty($this->shape) ? '' : '&shape=' . $this->getShape();
		$str .= empty($this->scaleType) ? '' : '&scaletype=' . $this->getScaleType();
		$str .= empty($this->scaleMin) ? '' : '&scalemin=' . $this->getScaleMin();
		$str .= empty($this->scaleMax) ? '' : '&scalemax=' . $this->getScaleMax();
		$str .= empty($this->oFormat) ? '' : '&oformat=' . $this->getOFormat();
		$str .= empty($this->padPos) ? '' : '&padpos=' . $this->getPadPos();
		$str .= empty($this->padValue) ? '' : '&padvalue=' . $this->getPadValue();	
		$str .= empty($this->lpf) ? '' : '&lpf=' . $this->getLpf();	
		
		return $str;
	}
}

?>