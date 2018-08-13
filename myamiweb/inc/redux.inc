<?php
/*
 * example: filename=/ami/exdata/leginon/10mar30z/rawdata/Data0308.mrc
 * 					&padshape=4096x4096&power=1&maskradius=50&shape=512x512
 * 					&scaletype=cdf&scalemin=0.8&scalemax=0.98&oformat=JPEG
 */
require_once 'formValidator.php';

$validator = new formValidator();

class redux{
	private $filename;		//input image filename with full location path.
	private $pipeline;		//preset pipeline [choices: ('standard', 'histdata')]
	private $padShape;		// need to be x, y array (need to be bigger than original file size)
	private $padPos;		// need to be x, y array (start positions).
	private $padValue;		// float
	private $power;			// boolean
	private $cacheOff;			// boolean: Force cache off
	private $maskRadius;	// float 
	private $shape;			// x, y array (output size)
	private $frame;		// integer or false (means no frame selection)
	private $histBins;		// integer
	private $histMin;		// float
	private $histMax;		// float
	private $lpf;			// low pass filter, float (the default is not use at all)
	private $scaleMin;		// float
	private $scaleMax;		// float
	private $scaleType;		// image scale type [choices ("minmax", "stdev", "cdf")]
	private $rgb;			// boolean (the default is false and means grayscale if it is an image)
	private $info;			// boolean
	private $oFormat;		// image output format [choices: ('JPEG', 'GIF', 'TIFF', 'PNG', 'MRC')]
	private $errMsg;		// error message array contain name - message pair.
	private $overlay;		// Path to an overlay image
	private $overlayColor;  // Srting representing RGB values for displaying the overlay, ex. "255,0,0"
	
	
	/*
	 * default constructor requires at lease image input location
	 * and output format
	 */
	function __construct($filename, $oFormat=null)
	{
		$this->setFilename($filename);	
		
		// set default output format to JPEG
		$oFormat = (empty($oFormat))? '': $oFormat;
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
	
	function getFrameValue() 		{ return $this->frameValue; }
	
	function getPower(){
		$str = $this->power ? '1' : '0'; 
		return $str;
	}
	
	function getCacheOff(){
		$str = $this->cacheOff ? '1' : '0'; 
		return $str;
	}

	function getCacheOn(){
		$str = ($this->cacheOff === false) ? '0' : '1'; 
		return $str;
	}
	function getRGB(){
		$str = $this->rgb ? '1' : '0'; 
		return $str;
	}
	
	function getInfo(){
		$str = $this->info ? '1' : '0'; 
		return $str;
	}
	
	function getMaskRadius() 	{ return $this->maskRadius; }
	
	function getShape(){ 
		return $this->shape[1]. 'x' . $this->shape[0]; 
	}
	function getShapeValue(){
		return $this->shape;
	}
	
	function getLpf() 			{ return $this->lpf; }
	function getScaleMin() 		{ return $this->scaleMin; }
	function getScaleMax() 		{ return $this->scaleMax; }
	function getScaleType() 	{ return $this->scaleType; }
	function getOFormat() 		{ return $this->oFormat; }
	function getPipeline() 		{ return $this->pipeline; }
	function getHistBins() 		{ return $this->histBins; }
	function getHistMin() 		{ return $this->histMin; }
	function getHistMax() 		{ return $this->histMax; }
	
	function getErrMsg(){ 
		$this->validateInputs();
		return $this->errMsg; 
	}
	
	function setOverlay( $filename='' )
	{	
		if (!empty($filename)) {
			global $validator;
			$validator->addValidation("filename", $filename, "file_exist", "Overlay image file does not exist.");
		}
		$this->overlay = $filename; 
	}
	
	function setOverlayColor( $color=0.1 )
	{	
		$this->overlayColor = $color; 
	}
	
	function setFilename($filename){
		
		global $validator;
		$validator->addValidation("filename", $filename, "file_exist", "MRC image file does not exist.");
		$this->filename = $filename; 
	}
	
	function setHistBins($histBins){
		global $validator;
		$validator->addValidation("histBins", $histBins, "num", "number of bins in histogram must be a positive integer");
		$this->histBins = $histBins; 
	}

	function setHistMin($histMin){
		global $validator;
		$validator->addValidation("histMin", $histMin, "float", "Minimum histogram range must be float");
		$this->histMin = $histMin;
	}

	function setHistMax($histMax){
		global $validator;
		$validator->addValidation("histMax", $histMax, "float", "Maximum histogram range must be float");
		$this->histMax = $histMax; 
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
		$validator->addValidation("padValue", $padValue, "float", "Pad value must be an float.");
		$this->padValue = $padValue; 
	}

	function setFrameValue($frameValue){ 
		# pass boolean false to indicate whole image is read
		# otherwise frame=0 will trigger disable_cache
		if ($frameValue !== false) {	
			global $validator;
			$validator->addValidation("frameValue", $frameValue, "num", "Frame numer value must be an integer.");
		}
		$this->frameValue = $frameValue; 
	}

	function setInfo($infoflag){ 
		
		global $validator;
		if(!is_bool($infoflag))
			$validator->setErrorMessage("info", "The value of info flag must be boolean (true, flase).");
		$this->info = $infoflag; 
	}

	function setCacheOff($cacheOff){ 
		
		global $validator;
		if(!is_bool($cacheOff))
			$validator->setErrorMessage("cacheOff", "The value of cacheOff must be boolean (true, flase).");
		$this->cacheOff = $cacheOff;
	}

	function setPower($power){ 
		
		global $validator;
		if(!is_bool($power))
			$validator->setErrorMessage("power", "The value of power must be boolean (true, flase).");

		/* Special note:
		 * The if statement is to insure when the original image is not square. Need to convert 
		 * to square image's shape for display FFT
		 */
		if($power){
			$shape = $this->getShapeValue();
			$dimMax = max((int)$shape[0], (int)$shape[1]);
			$this->setShape(array($dimMax, $dimMax));			
		}
		$this->power = $power; 

	}
	
	function setMaskRadius($maskRadius){ 
		
		global $validator;
		$validator->addValidation("maskRadius", $maskRadius, "float", "Mask Radius value must be a float.");
		$this->maskRadius = $maskRadius; 
	}
	
	function setRGB($rgb){ 
		
		global $validator;
		if(!is_bool($rgb))
			$validator->setErrorMessage("rgb", "The value of rgb must be boolean (true, flase).");
		$this->rgb = $rgb; 
	}

	function setShape($shape){ 
		
		global $validator;
		
		if(!is_array($shape) || (count($shape) != 2)) 
			$validator->setErrorMessage("shape", "Shape must be an array and contain two elements (x, y).");
			
		$validator->addValidation("shapeX", $shape[1], "num", "Shape X value must be a positive integer.");
		$validator->addValidation("shapeX", $shape[0], "num", "Shape Y value must be a positive integer.");
		$this->shape = $shape; 
	}
	
	function setLpf($lpf){ 
		
		global $validator;
		$validator->addValidation("lpf", $lpf, "float", "LPF value must be a float.");
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
	 * choices ("minmax", "pctminmax, "stdev", "cdf")
	 */
	function setScaleType($scaleType){ 
		
		global $validator;
		$validator->addValidation("scaleType", $scaleType, "req", "Image scale type is required.");
		
		switch($scaleType){
			case "minmax":
			case "pctminmax":
			case "stdev":
			case "cdf":
				break;
			default:
				$validator->setErrorMessage("scaleType", "Image scale type can only be \"minmax\", \"pctminmax\", \"stdev\", or \"cdf\".");
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
			case "JSON":
				break;
			default:
				$validator->setErrorMessage("oFormat", "Image output format can only be \"JPEG\", \"GIF\", \"TIFF\", \"PNG\", or \"MRC\", or \"JSON\".");
		}
		$this->oFormat = $oFormat; 
	}
	
		function setPipeline($pipeline='standard'){ 
		
		global $validator;
		switch($pieline){
			case "standard":
			case "histdata":
				break;
			default:
				$validator->setErrorMessage("pipeline", "Available pipelines are \"standard\" and \"histdata\".");
		}
		$this->pipeline = $pipeline; 
	}
	
	function validateInputs(){
		global $validator;
		$validator->runValidation();
		$this->errMsg = $validator->getErrorMessage();
	}
	
	function constructRequestString(){
		/* Comment out some functions because Redux server has not fully tested yet */
		
		$str .= empty($this->pipeline) ? '' : 'pipeline=' . $this->getPipeline().'&';
		$str .= 'filename=' . $this->getFilename();
		//$str .= empty($this->padShape) ? '' : '&padshape=' . $this->getPadShape();
		$str .= empty($this->power) ? '' : '&power=' . $this->getPower();
		$str .= empty($this->info) ? '' : '&info=' . $this->getInfo();
		if (empty($this->info)) {
			$str .= empty($this->cacheOff) ? '' : '&cache=' . (int) !$this->getCacheOn();
		} else {
			$str .= '&cache=0';
		}
		$str .= empty($this->maskRadius) ? '' : '&maskradius=' . $this->getMaskRadius();
		$str .= empty($this->rgb) ? '' : '&rgb=' . $this->getRGB();
		$str .= empty($this->shape) ? '' : '&shape=' . $this->getShape();
		$str .= empty($this->scaleType) ? '' : '&scaletype=' . $this->getScaleType();
		$str .= !is_numeric($this->scaleMin) ? '' : '&scalemin=' . $this->getScaleMin();
		$str .= !is_numeric($this->scaleMax) ? '' : '&scalemax=' . $this->getScaleMax();
		$str .= empty($this->oFormat) ? '' : '&oformat=' . $this->getOFormat();
		$str .= empty($this->histBins) ? '' : '&histbins=' . $this->getHistBins();
		$str .= !is_numeric($this->histMin) ? '' : '&histmin=' . $this->getHistMin();
		$str .= !is_numeric($this->histMax) ? '' : '&histmax=' . $this->getHistMax();
		//$str .= empty($this->padPos) ? '' : '&padpos=' . $this->getPadPos();
		//$str .= empty($this->padValue) ? '' : '&padvalue=' . $this->getPadValue();	
		# Be more specific about frame since frame=0 triggers disable_cache in redux
		$str .= ($this->frameValue===false || $this->frameValue===null) ? '' : '&frame=' . $this->getFrameValue();	
		$str .= empty($this->lpf) ? '' : '&lpf=' . $this->getLpf();	
		$str .= empty($this->overlay) ? '' : '&overlay=' . $this->overlay;
		$str .= empty($this->overlayColor) ? '' : '&overlaycolor=' . $this->overlayColor;

		return $str;
	}
	
	function requestImage(){

		if (defined('REDUX_AVOID_PATH') && (strpos($this->getFilename(), REDUX_AVOID_PATH) !== false)) {
		//if (false) {
			$reply=$this->filename;
			return $reply;
		}
		$msg = $this->constructRequestString() ."\n";

		$reduxsock = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
		socket_connect($reduxsock, SERVER_HOST, SERVER_PORT);
		socket_write($reduxsock, $msg, strlen($msg));
	
		$reply = "";
		do {
				 $recv = "";
				 $recv = socket_read($reduxsock, 8192);

				 if($recv != "") {
						 $reply .= $recv;
				 }
		} while($recv != ""); 
	
		return $reply;		
	}
}

?>
