<?
function blank() {
	header('location: img/blank.png');
}

class gridbox {

	function gridbox($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(PRJ_DB_HOST, PRJ_DB_USER, PRJ_DB_PASS, PRJ_DB);
	}

	function updateGridBox($gridboxId, $label, $boxtypeId, $container) {

		if (!$this->checkGridBoxExistsbyId($gridboxId)) 
			return false;

		$table='gridboxes';
		$data['label']=$label;
		$data['boxtypeId']=$boxtypeId;
		$data['container']=$container;
		$where['gridboxId']=$gridboxId;

		$s = $this->mysql->SQLUpdate($table, $data, $where);
	}

	function deleteGridBox($gridboxId) {
		if (!$gridboxId)
			return false;
		$q[]='delete from gridboxes where gridboxId='.$gridboxId;
		$q[]='delete from gridlocations where gridboxId='.$gridboxId;
		$this->mysql->SQLQueries($q);
	}

	function addGridBox($label, $boxtypeId, $container) {

		if (!$label) return 0;

		$table="gridboxes";
		$data['label']=$label;
		$data['boxtypeId']=$boxtypeId;
		$data['container']=$container;

		$re=$this->checkGridBoxExistsbyName($label);

		if (empty($re)) {
			$id =  $this->mysql->SQLInsert($table, $data);
			return $id;
		}
	}

	function checkGridBoxExistsbyName($label) {
		$q=' select gridboxId from gridboxes where label="'.$label.'"';
		list($gridboxInfo) = $this->mysql->getSQLResult($q);
		$id = $gridboxInfo['gridboxId'];
		if(empty($id))
			return false;
		else
			return $id;
	}

	function checkGridBoxExistsbyId($id) {
		$q=' select gridboxId from gridboxes where gridboxId="'.$id.'"';
		list($gridInfo) = $this->mysql->getSQLResult($q);
		$id = $gridInfo['gridboxId'];
		if(empty($id))
			return false;
		else
			return $id;
	}

	function getGridBoxId($label){
		$q='select gridboxId from gridbox where label="'.$label.'"';
		list($gridboxInfo) = $this->mysql->getSQLResult($q);
		$id = $gridboxInfo['gridboxId'];
	}

	function isGridboxUsed($gridboxId) {
		$locations=array();
		$q=' select location from gridlocations where '
		  .' gridboxId="'.$gridboxId.'" ';
		$r = $this->mysql->getSQLResult($q);
		foreach ((array)$r as $row) {
			$locations[]=$row['location'];
		}
		return $locations;
	}

	function isLocationUsed($gridboxId, $location) {
		$q=' select gridId, gridboxId, location from gridlocations where '
		.' gridboxId="'.$gridboxId.'" and location = "'.$location.'"';
		$Rcheck = $this->mysql->SQLQuery($q);
    if (mysql_num_rows($Rcheck) > 0)
			return true;
		else
			return false;
	}

	function getGridBoxes(){
		$gridboxes=array();
		$q='select gridboxId, label from gridboxes';
		$gridboxes = $this->mysql->getSQLResult($q);
		return $gridboxes;
	}

	function getGridBoxInfo($gridboxId){
		$info=array();
		$q='select gridboxId, '
		  .'g.boxtypeId, '
		  .'g.container, '
		  .'b.image, '
		  .'b.`image_tiny`, '
		  .'b.label as "boxtypelabel", '
		  .'g.label as "gridboxlabel" '
		  .'from gridboxes g '
		  .'left join boxtypes b on (g.boxtypeId = b.boxtypeId) '
		  .'where g.gridboxId="'.$gridboxId.'"';

		list($info) = $this->mysql->getSQLResult($q);
		return $info;
	}

	function getBoxTypes() {
		$boxtypes=array();
		$q='select boxtypeId, label, image, image_tiny from boxtypes';
		$boxtypes = $this->mysql->getSQLResult($q);
		return $boxtypes;
	}

}

class tray extends abstractgridbox {

	var $nbgrids=96;
	var $nbrows=8;
	var $org_x=831;
	var $org_y=76;
	var $ix=67;
	var $iy=67;
	var $grid_img_str='grid_img.gif';
	var $gridbox_img_str='tray.png';
	var $gridtype='tgb';

	function tray($size="") {
		$this->mysql = new mysql(PRJ_DB_HOST, PRJ_DB_USER, PRJ_DB_PASS, PRJ_DB);
		$this->size=$size;
		$this->setSize($size);
		$coords[] = array ($this->org_x, $this->org_y );
		for ($i=0; $i<$this->nbgrids; $i++) {
			$x = ($i==0) ? $coords[0][0] : $x;
			$y = ($i==0) ? $coords[0][1] : $coords[$i-1][1]+$this->iy;
			if ($i % $this->nbrows == 0 && $i>0) {
				$x = $coords[$i-1][0]-$this->ix;
				$y = $coords[0][1];
			}

			$coords[$i] = array ($x,$y);
		}
		$this->coords=$coords;
	}

	function setSize($size) {
		if ($size=='tiny') {
			$this->org_x=410;
			$this->org_y=57;
			$this->ix=31;
			$this->iy=31;
			$this->grid_img_str='grid_img_tiny.gif';
			$this->gridbox_img_str='tray_tiny.png';
			$this->fontsize=2;
			$this->offXfont=0;
			$this->offYfont=10;
			$this->gridsize=8;
			$this->offsetx=6;
			$this->offsety=6;
			$this->offsetcrossX=4;
			$this->offsetcrossY=4;
		}
	}

	function setImages() {
		$this->gridbox_img = imagecreatefrompng($this->image_path.$this->gridbox_img_str);
		$this->gridbox_img_x = imagesx($this->gridbox_img);
		$this->gridbox_img_y = imagesy($this->gridbox_img); 
		$this->grid_img = imagecreatefromgif($this->image_path.$this->grid_img_str);
		$this->grid_img_x = imagesx($this->grid_img);
		$this->grid_img_y = imagesy($this->grid_img); 
	}

	function drawGrids($gridboxId) {
		$gridboxinfo = $this->getGridLocations($gridboxId);
		$gridlocations = array();
		foreach ($gridboxinfo as $gl) {
			$gridlocations[] = $gl[location];
			if ($this->selectedgridId == $gl[gridId])
				$selectedlocation = $gl[location];
				
		}

		$this->setImages();

		$blue = imagecolorallocate($this->gridbox_img, 0, 0, 255);
		$red = imagecolorallocate($this->gridbox_img, 255, 0, 0);
		$green = imagecolorallocate($this->gridbox_img, 0, 255, 0);
		$defaultcolor = imagecolorallocate($this->gridbox_img, 195, 195, 195);
		$t=1;
		$x=$this->offsetcrossX;
		$y=$this->offsetcrossY;
		foreach ($this->coords as $coord) {
		if (in_array($t, $gridlocations)) {
			imagecopymerge($this->gridbox_img,$this->grid_img,$coord[0],$coord[1],0,0,$this->grid_img_x,$this->grid_img_y,100);
			$color = $blue;
			$cx = $coord[0]+$this->grid_img_x/2;
			$cy = $coord[1]+$this->grid_img_y/2;
		
			if ($t != $selectedlocation) {
			imagearc($this->gridbox_img, 
				$cx,
				$cy,
				$this->grid_img_x+3,$this->grid_img_y+3, 0, 360, $defaultcolor);
			imageline($this->gridbox_img, $cx-$x, $cy-$y, $cx+$x, $cy+$y, $defaultcolor);
			imageline($this->gridbox_img, $cx+$x, $cy-$y, $cx-$x, $cy+$y, $defaultcolor);
			}
		} else {
			$color = $defaultcolor;
		} if ($t == $selectedlocation) {
			$color = $red;
			$this->fontsize=3;
			imagearc($this->gridbox_img, 
				$cx,
				$cy,
				$this->grid_img_x+3,$this->grid_img_y+3, 0, 360, $green);
		} else {
			$this->fontsize=2;
		}
		imagestring($this->gridbox_img, $this->fontsize, $coord[0]+$this->offXfont,$coord[1]+$this->offYfont, $t, $color);
		$t++;
		}
	}

	function drawSelectedGrid($gridboxId) {
		$selectedlocation = $this->selectedgridId;
		$gridboxinfo = $this->getGridLocations($gridboxId);
		$gridlocations = array();
		foreach ($gridboxinfo as $gl) {
			$gridlocations[] = $gl[location];
			if ($this->selectedgridId == $gl[gridId])
				$selectedlocation = $gl[location];
		}

		$this->setImages();

		$blue = imagecolorallocate($this->gridbox_img, 0, 0, 255);
		$red = imagecolorallocate($this->gridbox_img, 255, 0, 0);
		$green = imagecolorallocate($this->gridbox_img, 0, 255, 0);
		$defaultcolor = imagecolorallocate($this->gridbox_img, 195, 195, 195);
		$t=1;
		foreach ($this->coords as $coord) {
		if (in_array($t, $gridlocations)) {
			imagecopymerge($this->gridbox_img,$this->grid_img,$coord[0],$coord[1],0,0,$this->grid_img_x,$this->grid_img_y,100);
			$color = $blue;
		} else {
			$color = $defaultcolor;
		} if ($t == $selectedlocation) {
			$color = $red;
			$this->fontsize=3;
			imagearc($this->gridbox_img, 
				$coord[0]+$this->grid_img_x/2,
				$coord[1]+$this->grid_img_y/2,
				$this->grid_img_x+3,$this->grid_img_y+3, 0, 360, $green);
			// imagefilledarc($this->gridbox_img, $coord[0],$coord[1], 100, 50, 0, 45, $green, IMG_ARC_PIE);
		} else {
			$this->fontsize=2;
		}
		imagestring($this->gridbox_img, $this->fontsize, $coord[0]+$this->offXfont,$coord[1]+$this->offYfont, $t, $color);
		$t++;
		}
	}

	function display() {
		header( "Content-type: image/png");
		imagepng($this->gridbox_img);
		imagedestroy($this->gridbox_img);
		imagedestroy($this->grid_img);
	}

}

class drawgridbox extends abstractgridbox {

	var $org_x_1=664;
	var $org_y_1=52;
	var $org_x_2=282;
	var $org_y_2=52;
	var $ix=61;
	var $iy=56;
	var $nbgrids=25;
	var $nbrows=5;
	var $grid_img_str='grid_img.gif';
	var $gridbox_img_str='grid_box.jpg';
	var $gridtype='gb';

	function drawgridbox($size="") {
		$this->mysql = new mysql(PRJ_DB_HOST, PRJ_DB_USER, PRJ_DB_PASS, PRJ_DB);

		$this->size=$size;
		$this->setSize($size);
		$coords[] = array ($this->org_x_1, $this->org_y_1, 1);
		for ($i=0; $i<$this->nbgrids; $i++) {
			$x = ($i==0) ? $coords[0][0] : $x;
			$y = ($i==0) ? $coords[0][1] : $coords[$i-1][1]+$this->iy;
			if ($i % $this->nbrows == 0 && $i>0) {
				$x = $coords[$i-1][0]-$this->ix;
				$y = $coords[0][1];
			}

			$coords[$i] = array ($x,$y, $i+1);
		}
		$coords2[] = array ($this->org_x_2, $this->org_y_2, 1);
		for ($i=0; $i<$this->nbgrids; $i++) {
			$x = ($i==0) ? $coords2[0][0] : $x;
			$y = ($i==0) ? $coords2[0][1] : $coords2[$i-1][1]+$this->iy;
			if ($i % $this->nbrows == 0 && $i>0) {
				$x = $coords2[$i-1][0]-$this->ix;
				$y = $coords2[0][1];
			}

			$coords2[$i] = array ($x,$y,$this->nbgrids+$i+1);
		}
		foreach($coords2 as $c)
			$coords[]=$c;
		$this->coords=$coords;
	}

	function setSize($size) {
		if ($size=='tiny') {
			$this->org_x_1=331;
			$this->org_y_1=25;
			$this->org_x_2=140;
			$this->org_y_2=25;
			$this->ix=30;
			$this->iy=28;
			$this->grid_img_str='grid_img_tiny.gif';
			$this->gridbox_img_str='grid_box_tiny.jpg';
			$this->fontsize=2;
			$this->offXfont=0;
			$this->offYfont=10;
			$this->gridsize=8;
			$this->offsetx=6;
			$this->offsety=6;
			$this->offsetcrossX=4;
			$this->offsetcrossY=4;
		}
	}

	function drawGrids($gridboxId) {
		$gridboxinfo = $this->getGridLocations($gridboxId);
		$gridlocations = array();
		foreach ($gridboxinfo as $gl) {
			$gridlocations[] = $gl[location];
			if ($this->selectedgridId == $gl[gridId])
				$selectedlocation = $gl[location];
				
		}

		$this->setImages();
		$abs1=5;
		$abs2=5;
		$ord1 = array("A","B","C","D","E");
		$ord2 = array("E","D","C","B","A");

		$blue = imagecolorallocate($this->gridbox_img, 0, 0, 255);
		$red = imagecolorallocate($this->gridbox_img, 255, 0, 0);
		$green = imagecolorallocate($this->gridbox_img, 0, 255, 0);
		$defaultcolor = imagecolorallocate($this->gridbox_img, 0, 195, 195);
		$t=1;
		$x=$this->offsetcrossX;
		$y=$this->offsetcrossY;
		foreach ($this->coords as $coord) {
		if (in_array($t, $gridlocations)) {
			imagecopymerge($this->gridbox_img,$this->grid_img,$coord[0],$coord[1],0,0,$this->grid_img_x,$this->grid_img_y,100);
			$color = $blue;
			$cx = $coord[0]+$this->grid_img_x/2;
			$cy = $coord[1]+$this->grid_img_y/2;
		
			if ($t != $selectedlocation) {
			imagearc($this->gridbox_img, 
				$cx,
				$cy,
				$this->grid_img_x+3,$this->grid_img_y+3, 0, 360, $defaultcolor);
			imageline($this->gridbox_img, $cx-$x, $cy-$y, $cx+$x, $cy+$y, $defaultcolor);
			imageline($this->gridbox_img, $cx+$x, $cy-$y, $cx-$x, $cy+$y, $defaultcolor);
			}
		} else {
			$color = $defaultcolor;
		}
		if ($t>25) {
			if (($t-1)%5==0)
				$abs2++;
			$text = $ord2[($t-1)%5].",".($abs2);
		} else {
			$text = $ord1[($t-1)%5].",".($abs1);
			if (($t-1)%5==0) 
				$abs1--;
		}
		if ($t == $selectedlocation ) {
			$color = $red;
			$this->fontsize=3;
			imagearc($this->gridbox_img, 
				$cx,
				$cy,
				$this->grid_img_x+3,$this->grid_img_y+3, 0, 360, $green);
		} else {
			$this->fontsize=2;
		}
		imagestring($this->gridbox_img, $this->fontsize, $coord[0]+$this->offXfont,$coord[1]+$this->offYfont, $text, $color);
		$t++;
		}
	}

	function display() {
		Header( "Content-type: image/png");
		imagepng($this->gridbox_img);
		imagedestroy($this->gridbox_img);
		imagedestroy($this->grid_img);
	}

}

class gridboxcryo extends abstractgridbox {

	var $org_x_1=106;
	var $org_y_1=44;
	var $ix=61;
	var $iy=56;
	var $nbgrids=4;
	var $nbrows=2;
	var $gridtype='cgb';
	var $grid_img_str='grid_img.gif';
	var $gridbox_img_str='grid_box_cryo.jpg';
	var $fontsize=5;
	var $offXfont=0;
	var $offYfont=20;

	function gridboxcryo() {
		$this->mysql = new mysql(PRJ_DB_HOST, PRJ_DB_USER, PRJ_DB_PASS, PRJ_DB);
		$coords[] = array ($this->org_x_1, $this->org_y_1);
		for ($i=0; $i<$this->nbgrids; $i++) {
			$x = ($i==0) ? $coords[0][0] : $x;
			$y = ($i==0) ? $coords[0][1] : $coords[$i-1][1]+$this->iy;
			if ($i % $this->nbrows == 0 && $i>0) {
				$x = $coords[$i-1][0]-$this->ix;
				$y = $coords[0][1];
			}

			$coords[$i] = array ($x,$y);
		}
		$this->coords=$coords;
	}

	function drawGrids($gridboxId) {
		$gridboxinfo = $this->getGridLocations($gridboxId);
		$gridlocations = array();
		foreach ($gridboxinfo as $gl) {
			$gridlocations[] = $gl[location];
			if ($this->selectedgridId == $gl[gridId])
				$selectedlocation = $gl[location];
				
		}

		$this->setImages();
		$abs1=2;
		$ord1 = array("A","B");
		$numvalues = array(1=>2,2=>4,3=>1,4=>3);

		$blue = imagecolorallocate($this->gridbox_img, 0, 0, 255);
		$red = imagecolorallocate($this->gridbox_img, 255, 0, 0);
		$green = imagecolorallocate($this->gridbox_img, 0, 255, 0);
		$defaultcolor = imagecolorallocate($this->gridbox_img, 0, 195, 195);
		$t=1;
		$x=$this->offsetcrossX;
		$y=$this->offsetcrossY;
		foreach ($this->coords as $coord) {
		if (in_array($t, $gridlocations)) {
			imagecopymerge($this->gridbox_img,$this->grid_img,$coord[0],$coord[1],0,0,$this->grid_img_x,$this->grid_img_y,100);
			$color = $blue;
			$cx = $coord[0]+$this->grid_img_x/2;
			$cy = $coord[1]+$this->grid_img_y/2;
		
			if ($t != $selectedlocation) {
			imagearc($this->gridbox_img, 
				$cx,
				$cy,
				$this->grid_img_x+3,$this->grid_img_y+3, 0, 360, $defaultcolor);
			imageline($this->gridbox_img, $cx-$x, $cy-$y, $cx+$x, $cy+$y, $defaultcolor);
			imageline($this->gridbox_img, $cx+$x, $cy-$y, $cx-$x, $cy+$y, $defaultcolor);
			}
		} else {
			$color = $defaultcolor;
		}
//		$text = $ord1[($t-1)%2].",".($abs1);
//		if (($t-1)%2==0 && $t>0)
//			$abs1--;
		$text = $numvalues[$t];

		if ($t == $selectedlocation ) {
			$color = $red;
			imagearc($this->gridbox_img, 
				$cx,
				$cy,
				$this->grid_img_x+3,$this->grid_img_y+3, 0, 360, $green);
		}
		imagestring($this->gridbox_img, $this->fontsize, $coord[0]+$this->offXfont,$coord[1]+$this->offYfont, $text, $color);
		$t++;
		}
	}

	function display() {
		Header( "Content-type: image/png");
		imagepng($this->gridbox_img);
		imagedestroy($this->gridbox_img);
		imagedestroy($this->grid_img);
	}

}

class abstractgridbox {

	var $image_path = 'img/';
	var $offsetcrossX = 8;
	var $offsetcrossY = 8;
	var $fontsize=5;
	var $offXfont=0;
	var $offYfont=20;
	var $gridsize=13;
	var $offsetx=10;
	var $offsety=10;

	function getGridCoords() {
		return $this->coords;
	}

	function getGridImgSize() {
		return array(	$this->grid_img_x,
				$this->grid_img_y
				);
	}

	function getGridLocations($gridboxId) {
		$gridlocations=array();
		$q=' select gridId, location '
		.' from gridlocations '
		.' where gridboxId="'.$gridboxId.'" ';
		return $this->mysql->getSQLResult($q);
	}
	
	function setGridLocation($gridboxId, $gridId, $location) {
		$q=' insert into gridlocations '
		.'(gridboxId, gridId, location)'
		.' values'
		.'("'.$gridboxId.'", "'.$gridId.'", "'.$location.'")'; 
		$locationinfo=$this->checkGridBoxLocationExists($gridboxId, $location);
		if ($locationinfo['locationId'] && $locationinfo['gridId']==$gridId) {
			// --- allow to remove a grid from a gridbox
			$this->deleteGridBoxLocation($gridId); 
			return false;
		} else if ($locationinfo['locationId']) {
			// --- return if location not available
			return false;
		} else {
			// --- delete old location if a new location is available
			$currentgridinfo = $this->checkGridBoxIdExists($gridId, $gridboxId);
			$currentlocation = $currentgridinfo['location'];
			if ($currentlocation != $location)
				$this->deleteGridBoxLocation($gridId); 
			// --- insert new location
			$id =  $this->mysql->SQLQuery($q, true);
			return $id;
		}
	}

	function checkGridBoxIdExists($gridId, $gridboxId="") {
		$gridboxsql = ($gridboxId) ? ' and gridboxId="'.$gridboxId.'" ' : "";
		$q=' select gridboxId, location from gridlocations where '
		  .' gridId="'.$gridId.'" '
		  .$gridboxsql;
		$RgridlocationInfo = $this->mysql->SQLQuery($q);
		$gridlocationInfo = mysql_fetch_array($RgridlocationInfo);
		return array (	'gridboxId' => $gridlocationInfo['gridboxId'],
				'location' => $gridlocationInfo['location'] );
	}

	function checkGridBoxLocationExists($gridboxId, $location) {
		$q=' select gridlocationId, gridId from gridlocations where '
		  .' gridboxId="'.$gridboxId.'" and location="'.$location.'"';
		$RgridlocationInfo = $this->mysql->SQLQuery($q);
		$gridlocationInfo = mysql_fetch_array($RgridlocationInfo);
		return array (	'locationId' => $gridlocationInfo[gridlocationId],
				'gridId' => $gridlocationInfo[gridId] );
	}

	function deleteGridBoxLocation($gridId) {
		if (!$gridId) 
			return false;
		$q = 'delete '
		    .'from gridlocations '
		    .'where gridId="'.$gridId.'" ';
		$this->mysql->SQLQuery($q);
		return true;
	}

	function generateMapE($gridboxId, $gridId="") {
		$link = empty($gridId) ? "" : "&amp;gid=$gridId";
		$link .= empty($gridboxId) ? "" : "&amp;gbid=$gridboxId";
		echo'<map name="gridbox_map">';
		$gcoord=1;
		$coords = $this->getGridCoords();
		foreach($coords as $coord) {
		$str = '
			<area shape="circle" href="'.$PHP_SELF.'?g='.$gcoord.$link.'" '.
			'coords="'.($coord[0]+$this->offsetx).', '.($coord[1]+$this->offsety).', '.$this->gridsize.'" '.
			'alt="grid '.$gcoord.'" >';
		echo $str;
		$gcoord++;
		}
		echo'</map>';
		echo'<img alt="grid box" border="0" usemap="#gridbox_map" src="drawgridbox.php?size=';
		echo $this->size.'&amp;type='.$this->gridtype
			.'&amp;gl='.$gridboxId
			.'&amp;gid='.$gridId
			.'&amp;rd='.rand()
			.'">';
	}

	function generateMap($gridboxId, $gridId="") {
		$gridlocations = $this->getGridLocations($gridboxId);
		$lgridboxId = "&amp;gbid=".$gridboxId;
		echo'<map name="gridbox_map">';
		$gcoord=1;
		$coords = $this->getGridCoords();
		foreach ($gridlocations as $k=>$gridlocation) {
		$location = $gridlocation['location'];
		$lgridId = "&amp;gid=".$gridlocation['gridId'];
		$lspId =  (func_num_args()>2) ? "&amp;spid=".func_get_arg(2) : '';
		$str = '
			<area shape="circle" href="'.$PHP_SELF.'?g='.$gcoord.$lgridId.$lgridboxId.$lspId.'" '.
			'coords="'.($coords[$location-1][0]+$this->offsetx).', '.($coords[$location-1][1]+$this->offsety).', '.$this->gridsize.'" '.
			'alt="grid '.$gcoord.'" >';
		echo $str;
		$gcoord++;
		}
/*
		foreach($coords as $coord) {
		$str = '
			<area shape="circle" href="'.$PHP_SELF.'?gl='.$gcoord.$link.'" '.
			'coords="'.($coord[0]+$this->offsetx).', '.($coord[1]+$this->offsety).', '.$this->gridsize.'" '.
			'alt="grid '.$gcoord.'" >';
		echo $str;
		$gcoord++;
		}
*/
		echo'</map>';
		echo'<img alt="grid box" border="0" usemap="#gridbox_map" src="drawgridbox.php?size=';
		echo $this->size.'&amp;type='.$this->gridtype
			.'&amp;gl='.$gridboxId
			.'&amp;gid='.$gridId
			.'">';
	}

	function selectedGrid($gridId) {
		$this->selectedgridId = $gridId;
	}

	function setImages() {
		$this->gridbox_img = imagecreatefromjpeg($this->image_path.$this->gridbox_img_str);
		$this->gridbox_img_x = imagesx($this->gridbox_img);
		$this->gridbox_img_y = imagesy($this->gridbox_img); 
		$this->grid_img = imagecreatefromgif($this->image_path.$this->grid_img_str);
		$this->grid_img_x = imagesx($this->grid_img);
		$this->grid_img_y = imagesy($this->grid_img); 
	}

}

?>
