<form name="gform" action="<?=$_SERVER['PHP_SELF']?>" method="POST">
  <input type="hidden" name="gridId" value="<?=$gridId?>">
  <table border="0" cellspacing="0" cellpadding="1" >
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Project
          </font><font color=red>*</font>&nbsp;:&nbsp;</div>
      </td>
      <td><font face="Arial, Helvetica, sans-serif" size="2"> 
				<select name="projectId">
				<?php
				foreach ($projects as $project) {
					$id = $project['projectId'];
					$s = ($id==$curgrid['projectId']) ? "selected" : "";
					echo '<option value="'.$id.'" '.$s.' >'.$project['name']."</option>\n";
				}
				?>
				</select>
        </font></td>
    </tr>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Label
          </font><font color=red>*</font>&nbsp;:&nbsp;</div>
      </td>
      <td><font face="Arial, Helvetica, sans-serif" size="2"> 
        <input class="field" type="text" name="label" value='<?=$curgrid['label']?>' size="40" tabindex="1" >
        </font></td>
    </tr>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Date
          </font>&nbsp;:&nbsp;</div>
      </td>
      <td>
	<font face="Arial, Helvetica, sans-serif" size="2"> 
	<input type="text" name="prepdate" value="<?=$f_prepdate;?>" size="40" maxlength="100" class="field" tabindex="2" >
        </font>
      </td>
    </tr>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Specimen
          </font>&nbsp;:&nbsp;</div>
      </td>
      <td>
	<font face="Arial, Helvetica, sans-serif" size="2"> 
	<input type="text" name="specimen" value="<?=$curgrid['specimen']?>" size="40" maxlength="100" class="field" tabindex="3" >
        </font>
      </td>
    </tr>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Preparation
          </font>&nbsp;:&nbsp;</div>
      </td>
      <td>
	<font face="Arial, Helvetica, sans-serif" size="2"> 
	<input type="text" name="preparation" value="<?=$curgrid['preparation']?>" size="40" maxlength="100" class="field" tabindex="4" >
        </font>
      </td>
    </tr>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Number
          </font>&nbsp;:&nbsp;</div>
      </td>
      <td>
	<font face="Arial, Helvetica, sans-serif" size="2"> 
	<input type="text" name="number" value="<?=$curgrid['number']?>" size="40" maxlength="100" class="field" tabindex="5" >
        </font>
      </td>
    </tr>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Note
          </font>&nbsp;:&nbsp;</div>
      </td>
      <td>
	<font face="Arial, Helvetica, sans-serif" size="2"> 
	<textarea class="textarea" name="note" rows="7" cols="40" tabindex="6"><?=$note?></textarea>
	</font>
      </td>
    </tr>
    <tr>
      <td >
        <input type="submit" value="<?=$action?>" name="submitgrid">
      </td>
    </tr>
<? if ($gridId) { ?>
		<tr>
			<td colspan=2>
				<hr/>
			</td>
		</tr>
    <tr>
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Grid Box
          </font>&nbsp;:&nbsp;</div>
      </td>
      <td>
	
<?
$gridboxes = $gridboxdata->getGridBoxes();
?>
<input type="hidden" name="gridId" value="<?=$gridId?>">
<select size="1" name="currentgridbox" onchange="onChangeGridBoxType()">
<option value="none">-- none --</option>
<?
$selectedgridboxId = ($_POST['currentgridbox']) ? $_POST['currentgridbox'] : $boxId;
foreach ($gridboxes as $gridbox) {
    $s = ($gridbox['gridboxId']==$selectedgridboxId) ? 'selected' : '';
    echo "<option value=",$gridbox['gridboxId']," $s >",$gridbox['label']."</option>\n";
}
?>
</select>
      </td>
    </tr>
<? } ?>
  </table>
</form>
<?

if ($gridId) {
	$gridboxId=$selectedgridboxId;
	$gridboxinfo = $gridboxdata->getGridBoxInfo($gridboxId);
	if ($gridboxinfo) {
?>
		<h4> Click at the position where you want the grid to be stored </h4>
		<p> No need to click on the update button </p>
<?
	}
	switch ($gridboxinfo['boxtypeId']) {
		case '1':
			$cryobox = new gridboxcryo(); 
			if ($g=$_GET['g']) {
				$gridlocations[]=(int)$g;
				$cryobox->setGridLocation($gridboxId, $gridId, $g);
			}
			$cryobox->generateMapE($gridboxId,$gridId);
			break;
		case '2':
			$size='tiny';
			$gridbox = new drawgridbox($size);
			if ($g=$_GET['g']) {
				$gridlocations[]=(int)$g;
				$gridbox->setGridLocation($gridboxId, $gridId, $g);
			}
			$gridbox->generateMapE($gridboxId,$gridId);
			break;
		case '3':
			$size='tiny';
			$tray = new tray($size);
			if ($g=$_GET['g']) {
				$gridlocations[]=(int)$g;
				$tray->setGridLocation($gridboxId, $gridId, $g);
			}
			$tray->generateMapE($gridboxId,$gridId);
			break;
	}
}
?>
