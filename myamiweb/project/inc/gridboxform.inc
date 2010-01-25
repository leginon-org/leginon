<form name="gridboxform" action="<?= $PHP_SELF ?>" method="POST">
  <input type="hidden" name="gridboxId" value="<?=$gridboxId?>">
  <table border="0" cellspacing="0" cellpadding="0" >
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2" tabindex="1">Label
          </font><font color=red>*</font>&nbsp;:&nbsp;</div>
      </td>
      <td><font face="Arial, Helvetica, sans-serif" size="2"> 
        <input type="text" name="label" value="<?=$curgridbox[gridboxlabel]?>" class="field" size="40" tabindex="1" />
        </font></td>
    </tr>
    <tr> 
      <td> 
        <div align="right"><font face="Arial, Helvetica, sans-serif" size="2">Type
          </font>&nbsp;:&nbsp;</div>
      </td>
      <td>
	<script>
	imgs = new Array();
	<?  foreach($boxtypes as $bt) {
		$id = $bt[boxtypeId];
		$imgId = 'img'.$id;
		echo	$imgId.' = new Image();'."\n"
			.$imgId.'.src = "img/'.$bt[image_tiny].'";'."\n "
			.'imgs['.$id.'] = '.$imgId.";\n";

	}
	?>

	function updateimg() {
		var cid = document.gridboxform.boxtypeId.options[document.gridboxform.boxtypeId.selectedIndex].value;
		document.fr.src=imgs[cid].src;
	}
		
	
	</script>
	<font face="Arial, Helvetica, sans-serif" size="2"> 
	<select name="boxtypeId" onChange="updateimg()">
	<?  foreach($boxtypes as $bt) {
		$sg = ($bt[boxtypeId]==$boxtypeId) ? 'selected' : '';
		echo'<option value="'.$bt[boxtypeId].'" '.$sg.'>'.$bt[label];
	}
	?>
	</select>
	<br>
	<? $curimg = (empty($curgridbox[image_tiny])) ? $boxtypes[0][image_tiny]
			: $curgridbox[image_tiny];?>
	<img name="fr" src="img/<?=$curimg?>">
        </font>
      </td>
    </tr>
    <tr>
      <td >
        <input type="submit" value="<?=$action?>" name="submit">
      </td>
    </tr>
  </table>
</form>
