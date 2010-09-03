<?php

// --- Manual Picker color --- //
$pick_colors = array (
	'ff0000',
	'00ff00',
	'0000ff',
	'ffff00',
	'ff00ff',
	'00ffff',
	'808000',
	'ff8080'
);

class colorpick {

	var $color = "#FFFFFF";
	var $colors = array ( 
		array('000000', '993300', '333300', '003300', '003366', '000080', '333399', '333333'),
		array('800000', 'ff6600', '808000', '008000', '008080', '0000ff', '666699', '808080'),
		array('ff0000', 'ff9900', '99cc00', '339966', '33cccc', '3366ff', '800080', '999999'),
		array('ff00ff', 'ffcc00', 'ffff00', '00ff00', '00ffff', '00ccff', '993366', 'c0c0c0'),
		array('ff99cc', 'ffcc99', 'ffff99', 'ccffcc', 'ccffff', '99ccff', 'cc99ff', 'ffffff')
		);
	
	function colorpick($name, $color='') {
		$this->name = $name;
		$this->formname = $name.'name';
		$this->fieldname = $name.'field';
		if ($color)
			$this->color=$color;
		
	}

	function add() {
		$name = $this->name;
		$html = '<a href="javascript:pickColor(\''.$name.'\');" '
			.'id="'.$name.'" style="border: 1px solid #000000; '
			.'font-family:Verdana; font-size:10px; text-decoration: none;">'
			.'&nbsp;&nbsp;&nbsp;</a>';
		return $html;
	}

	function getJavascript() {
		foreach($this->colors as $rows) {
			foreach($rows as $color) {
				$javascript .= "colorArray[colorArray.length] = '#$color';\n";
			}
		}
		return $javascript;
	}

	function getInitJavascript() {
		$javascript =	'setColorbyId("'.$this->name.'", "'.$this->color.'" );'."\n";
		return $javascript;
	}

	function getFormInput() {
		$html = '<input id="'.$this->fieldname.'" type="hidden" '
			.'name="'.$this->formname.'" value="'.$this->color.'">';
		return $html;
	}

	function setColor($color) {
		if ($color)
			$this->color = $color;
	}


}

class targetpick {

	var $targets = array ( 
				'cross1' => 'getimgtarget.php?target=cross1',
				'cross2' => 'getimgtarget.php?target=cross2',
				'cir1' => 'getimgtarget.php?target=cir1', 
				'box1' => 'getimgtarget.php?target=box1' 
			);

	var $target = "cross1"; 
	
	function targetpick($name, $target='') {
		$this->name = $name;
		$this->formname = $name.'name';
		$this->fieldname = $name.'field';
		if ($target)
			$this->target = $this->targets[$target];
		
	}

	function add() {
		$name = $this->name;
		$img = $this->targets[$this->target];
		$html = '<a href="javascript:pickTarget(\''.$name.'\');" >'
			.'<img border="0" id="'.$name.'" src="'.$img.'"></a>';
		return $html;
	}

	function getJavascript() {
		foreach($this->targets as $key=>$img) {
			$javascript .= "targetArray[targetArray.length] = '$key';\n";
			$javascript .= "targetImageArray[targetImageArray.length] = '$img';\n";
		}
		return $javascript;
	}

	function getInitJavascript() {
		$javascript =	'setTargetbyId("'.$this->name.'", "'.$this->target.'" );'."\n";
		return $javascript;
	}

	function getFormInput() {
		$html = '<input id="'.$this->fieldname.'" type="hidden" '
			.'name="'.$this->formname.'" value="'.$this->target.'">';
		return $html;
	}

	function setTarget($target) {
		if ($target)
			$this->target = $target;
	}


}
?>
