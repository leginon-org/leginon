<?php
require_once 'config.php';
require_once 'inc/util.inc';

define('XML_DATA', $XML_DATA);


class xmldata {

	var $xmlsessiondata = array();
	var $xmlsessioninfo = array();
	var $sessiondata = array();
	var $sessioninfo = array();
	var $xmlvalues = array();
	var $xmltags = array();

	function xmldata($inputdata) {
	// --- try to read a XML file or a XML string
	$data = (@is_file($inputdata)) ? implode("",file($inputdata)) : $inputdata;
	$parser = xml_parser_create();
        xml_parser_set_option($parser,XML_OPTION_CASE_FOLDING,0);
        xml_parser_set_option($parser,XML_OPTION_SKIP_WHITE,1);
	xml_parse_into_struct($parser,$data,$values,$tags);
	xml_parser_free($parser);
	$this->xmlvalues=$values;
	$this->xmltags=$tags;

		if ($val=$tags["info"]){
			$offset=$val[0];
			$length= ($val[1]) ? $val[1]-$offset:$offset;
			$this->xmlsessioninfo=(array_slice($values,$offset,$length));
		}
		if ($val=$tags["data"]){
			$offset=$val[0];
			$length= ($val[1]) ? $val[1]-$offset:$offset;
			$this->xmlsessiondata=(array_slice($values,$offset,$length));
		}

		$this->sessioninfo=$this->__to_sessioninfo();
		$this->sessiondata=$this->__to_sessiondata();
	}

	function __to_sessioninfo() {
		$info = array();
		if (is_array($this->xmlsessioninfo)) {
			foreach($this->xmlsessioninfo as $k=>$i)
				if ($k)
					$info[$i['tag']]=$i['value'];
		}
		return $info;
	}

	function __to_sessiondata() {
		/**
		 * $data[uid] = array(
		 *		'imagedata'=>imagedata,
		 *		'preset'=>data
		 *		)
		 */
		$data = array();
		foreach($this->xmlsessiondata as $k=>$i) {
			if($k) {
				if ($i['tag']=='imagedata' && $i['type']=='open') {
					$newimage=true;
					if (is_array($i['attributes']))
						$imagedata=$i['attributes'];

				}
				if ($newimage) {
					if ($i['tag']=='preset') {
						if (is_array($i['attributes']))
							$presetdata=$i['attributes'];
					}
				}
				if ($i['tag']=='imagedata' && $i['type']=='close') {
					$newimage=false;

					$data[$imagedata['uid']] = array (
						'imagedata'=>$imagedata,
						'presetdata'=>$presetdata
						);
				}
			}
		}
		return $data;
	}

	function getSessionInfo() {
		return $this->sessioninfo;
	}

	function getSessionData() {
		return $this->sessiondata;
	}

	function getFilenames() {
		$filenames = array();
		foreach ($this->sessiondata as $uid=>$d)
			$filenames[]=array(
				'id'=>$uid,
				'name'=>$d['imagedata']['filename']);
		return $filenames;
	}

	function getImagepath() {
		$imagepath = $this->__get_tag_value('imagepath');
		return formatPath($imagepath);
	}

	function getFilenamefromId($id) {
		$data = $this->sessiondata;
		return $data[$id]['imagedata']['filename'];
	}

	function getImageInfo($id) {
		$data = $this->sessiondata;
		return $data[$id]['imagedata'];
	}

	function getPresetData($id) {
		$data = $this->sessiondata;
		return $data[$id]['presetdata'];
	}

	function getLastFilenameId() {
		return end(array_keys($this->getFilenames()));
	}

	function getSessionId() {
		list($session) = $this->__get_tag_value('session','attributes');
		return $session['id'];
	}

	function __get_tag_value($tag,$type='value') {
		$values = array();
		$indexes = $this->xmltags[$tag];
		if (is_array($indexes))
		foreach ($indexes as $k=>$index) {
			$value = $this->xmlvalues[$index];
			if ($v=$value[$type])
				$values[]=$v;
		}
		if ($k)
			return $values;
		else
			return $values[0];

	}

	function formatDefocus(&$defocus) {
		$defocus = format_micro_number($defocus);
		return $defocus;
	}

	function formatPixelsize(&$pixelsize) {
		$pixelsize = format_nano_number($pixelsize);
		return $pixelsize;
	}

	function formatDose(&$dose) {
		$dose = ($dose) ? number_format(($dose/1e20), 4,'.','').' e¯/Å²' : 'none' ;
		return $dose;
	}

	function formatHighTension(&$ht) {
		$ht .= " V";
		return $ht;
	}

	function formatMatrixValue(&$val) {
		$val = (empty($val)) ? $val : format_sci_number($val, 4); 
		return $val;
	}


}

?>
