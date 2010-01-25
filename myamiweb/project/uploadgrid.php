<?
require "inc/project.inc.php";
require "inc/gridbox.inc.php";
require "inc/grid.inc.php";
require "inc/readfile.inc.php";
require "inc/util.inc";
require "inc/mysql.inc";

$error = false;
$warning = false;
$error_msg = array();

$projectdata=new project();
$projects=$projectdata->getProjects();

if($_POST) {
	$filesize  = $_FILES['grid_file']['size'];
	$filename  = $_FILES['grid_file']['name'];
	$filetype  = $_FILES['grid_file']['type'];
	$tmpfile   = $_FILES['grid_file']['tmp_name'];
	$projectId = $_POST['projectId'];
	if (is_file($_POST['tmpfile'])) {
		$tmpfile = $_POST['tmpfile'];
	}

	if(!$traylabel = $_POST['traylabel']) {
		$error_msg[] = " - enter a label for the tray";
		$error = true;
	}

	$gridbox = new gridbox();
	$grid = new grid();
	// --- check grid box exist --- //
	$confirm=false;
	$unlink=false;
	if ($id = $gridbox->checkGridBoxExistsbyName($traylabel)) {
		$warning = true;
		$gbinfo = $gridbox->getGridBoxInfo($id);
		$warn_msg[] = " - gridbox <b>".$gbinfo['gridboxlabel']."</b> already exists ";
		$gridboxId = $id;
		$confirm=true;
	}
	if ($curlocations=$gridbox->isGridboxUsed($gridboxId)) {
		$warning = true;
		$warn_msg[] = " - gridbox <b>".$gbinfo['gridboxlabel']."</b> is not empty";
		$confirm=true;
	}

	if ($_POST['confirm']==1) {
		$confirm=false;
		$unlink=true;
	}

	if (!$info = readtxtfile($tmpfile)) {
		$error_msg[] = " - invalid filename ";
		$error = true;
	}

		$fields = array();
		$data = array();
		$fields = $info['fields'];
		$data = $info['data'];


		$grid_fields = array ('label', 'prepdate', 'specimen', 'preparation', 'number', 'concentration', 'fraction', 'note' );
		$required_fields = array ('label', 'location');
		foreach ($required_fields as $field) {
			if (!in_array($field, $fields)) {
				$error=true;
				$error_msg[]=" - field: <b>$field</b> is missing in $filename";
			}
		}
		$gridlocation_fields = array ('location');

		// --- Check file syntax
		$labels=array();
		$locations=array();
		$curgrids=$grid->getGrids($projectId);
		$cproject=$curgrids[0]['project'];
		foreach($curgrids as $k=>$cg) {
			$curgridlabels[$k]=$cg['label'];
		}
		if (!$error) {
		foreach ((array)$data as $d) {
			$label=$d['label'];
			$location=$d['location'];
			if ($date=$d['prepdate']) {
				if (!strtotime($date)) {
					$error=true;
					$error_msg[]=" - prepdate: <b>$date</b> wrong format: yyyymmddhhiiss";
				}
			}
			if (in_array($label, $labels)) {
				$error=true;
				$error_msg[]=" - label: <b>$label</b> not unique";
			}
			if (in_array($location, $locations)) {
				$error=true;
				$error_msg[]=" - location: <b>$location</b> not unique";
			}
			if (in_array($location, (array)$curlocations)) {
				$error=true;
				$error_msg[]=" - location: <b>$location</b> not available";
			}
			if (in_array($label, (array)$curgridlabels)) {
				$error=true;
				$error_msg[]=" - label: <b>$label</b> exits in project <b>$cproject</b>";
			}
			$labels[]=$label;
			$locations[]=$location;
		}
		}

	if ($confirm && !$error) {
	// --- copy tmp file to new one
		$newfile=tempnam('/tmp','dbem');
		copy($tmpfile, $newfile);
	}
	if ($unlink) {
		unlink($tmpfile);
	}

	if (!$error && !$confirm) {
	// --- create new tray
	if (!$gridbox->checkGridBoxExistsbyName($traylabel)) {
		$gridboxId = $gridbox->addGridBox($traylabel, 3, '');
		$gbinfo = $gridbox->getGridBoxInfo($gridboxId);
	}

		$gridnb = 0;
		foreach ($data as $d) {
			$griddata = array();
			$gridlocationdata = array();
			foreach ($d as $k=>$v) {
				if (in_array($k, $grid_fields))
					$griddata[$k] = $v;
				else
				if (in_array($k, $gridlocation_fields))
					$gridlocationdata[$k] = $v;
			}
			$griddata['projectId'] = $projectId;
			$griddata['boxId'] = $gridboxId;
			$q = getsqlinsert('grids', $griddata);
			$gridId =  $grid->mysql->SQLQuery($q, true);
			$gridnb++;
			$gridlocationdata['gridboxId'] = $gridboxId;
			$gridlocationdata['gridId'] = $gridId;
			$q = getsqlinsert('gridlocations', $gridlocationdata);
			$grid->mysql->SQLQuery($q, true);

		}
	}


}



project_header("Upload grids");
if ($error || $warning) {
	echo '<div style="border: #CCCCCC solid 1px;padding: 5px">';
if ($warning) {
	$warning_icon='<img alt="warning" src="img/warning.png">';
	foreach ($warn_msg as $w)
		echo $warning_icon.' '.$w.'<br>';
}

if ($error) {
	$error_icon='<img alt="error" src="img/error.png">';
	foreach ($error_msg as $e)
		echo $error_icon.' '.$e.'<br>';
}
	echo "</div>";
	echo "<p>";
}
if (!$error && !$confirm && $_POST) {
	echo '<div style="border: #CCCCCC solid 1px;padding: 5px">';
	echo 'Tray <b>'.$gbinfo['gridboxlabel']."</b> successfully created<br>";
	$gstr = ($gridnb>0) ? $gridnb.' grids successfully inserted' : 'no grid inserted';
	echo $gstr.'<br>';
	if (!empty($existing_grids)) {
	echo '<br>existing grids: <br>';
		foreach($existing_grids as $g)
			echo " - $g <br>";
	}
	if (!empty($existing_gridlocations)) {
	echo '<br>existing gridlocations <br>';
		foreach($existing_gridlocations as $k=>$gl) {
			echo "grid: <b>".$k."</b> location: <b>".$gl."</b><br>";
		}
	}
		
	echo "</div>";
	echo "<p>";
} else {
?>
<form method="post" name="noteform" action="<?=$_SERVER['PHP_SELF']?>" enctype="multipart/form-data" >
	<input type="hidden" name="redirect" value="<?=$redirect?>">
	<input type="hidden" name="confirm" value="<?=$confirm?>">
	<input type="hidden" name="tmpfile" value="<?=$newfile?>">
	<input type="hidden" name="MAX_FILE_SIZE" value="50000000">
  <table border="0" cellspacing="0" cellpadding="3" width=500>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Project
          </font><font color=red>*</font>&nbsp;:&nbsp;</div>
      </td>
      <td><font face="Arial, Helvetica, sans-serif" size="2"> 
				<select name="projectId" tabindex="1" >
				<?php
				foreach ($projects as $project) {
					$id = $project['projectId'];
					$s = ($id==$projectId) ? "selected" : "";
					echo '<option value="'.$id.'" '.$s.' >'.$project['name']."</option>\n";
				}
				?>
				</select>
        </font></td>
    </tr>
    <tr> 
      <td> 	
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2" >Tray Label
          </font><font color=red>*</font>&nbsp;:&nbsp;</div>
      </td>
      <td><font face="Arial, Helvetica, sans-serif" size="2"> 
        <input class="field" type="text" name="traylabel" value="<?=$traylabel?>" size="20" tabindex="2" />
        </font></td>
    </tr>
    <tr> 
      <td> 	
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2" >Grid file
          </font><font color=red>*</font>&nbsp;:&nbsp;</div>
      </td>
      <td>
				<?php
				if ($tmpfile && !$error) {
					echo $filename;
				} else { ?>
				<font face="Arial, Helvetica, sans-serif" size="2"> 
        <input class="field" type="file" name="grid_file" tabindex="3" ><br>
        </font>
				<?php } ?>
			</td>
    </tr>
    <tr>
      <td> 	
      </td> 	
      <td> 	
			<?php
				$action=($confirm && !$error) ? "Import Anyway" : "Import";
			?>
				<input type="submit" name="add_grids" tabindex="4" value="<?=$action?>" />
      </td> 
    </tr>
  </table>
</form>
<font color=red>*</font>
<font face="Arial, Helvetica, sans-serif" size="2">: required fields</font>
<p>
<font face="Arial, Helvetica, sans-serif" size="2">required file format :</font>
<ul>
	<li>- text file, use <b>&lt;TAB&gt;</b> as a field separator
	<li>- first line contains field names (<b>label</b> and <b>location</b> are required)
</ul>
i.e: <a class="header" href="grids.txt">grids.txt</a>
<p>
<pre>
<?=file_get_contents("grids.txt");?>
</pre>
<?
}
project_footer();
?>
