<? if ($v1Id!=0) { ?>
<input type="hidden" name = "v1view" value="<?=$v1view?>">
<input type="hidden" name = "v1scalebar" value="<?=$v1scalebar?>">
		<!-- Debut Table View1 -->
		<table class="bgcolor1" border="0" cellspacing="0" cellpadding="1">
		 <tr>

			<td width="16"><a href="javascript:newexp();"
					onmouseover="imageon('v1close', 'close', '')" 
					onmouseout="imageoff('v1close', 'close', '')" 
					onClick="setview('v1', 'off')"
					><img name="v1close" src="img/close_off.gif" border="0" height="16" vspace="0"></a></td>
			<td width="16"><a href="javascript:newexp();"
					onmouseover="imageon('v1open', 'open', '')" 
					onmouseout="imageoff('v1open', 'open', '')" 
					onClick="setview('v1', 'on')"
					><img name="v1open" src="img/open_off.gif" border="0" height="16" vspace="0"></a></td>
	<td width="193" nowrap="nowrap">View 1</td>
			<td width="15"><a href="javascript:toggleimage('v1target_bt', 'target_bt'); newfile();"
					onmouseover="imageonfocus('v1target_bt', 'target_bt', '_over')" 
					onmouseout="imageonfocus('v1target_bt', 'target_bt', '')" 
					><img name="v1target_bt" src="img/target_bt_off.gif" border="0" height="15" vspace="0"></a></td>
			<td width="15"><a href="javascript:toggleimage('v1scale_bt', 'scale_bt'); newfile();"
					onmouseover="imageonfocus('v1scale_bt', 'scale_bt', '_over')" 
					onmouseout="imageonfocus('v1scale_bt', 'scale_bt', '')" 
					><img name="v1scale_bt" src="img/scale_bt_off.gif" border="0" height="15" vspace="0"></a></td>
<? /*
			<td><a href="javacript:void(0)"><img src="img/close_off.gif" border="0" height="16" vspace="0"></a> <a href="javacript:void(0)"><img src="img/open_off.gif" border="0" height="16" vspace="0"></a></td><td>View 1</td>
*/ ?>
		 </tr>
		 <tr>
			<td colspan="5">	
			<input type="hidden" name = "v1sel" value="<?=$v1sel?>">
			<table class="bgcolor0" border="0" cellspacing="0" cellpadding="0">
<? if ($v1view=='on') { ?>
			 <tr>
				<td height="1" width="259">
					<select name = "v1list" onchange = "setlist(); newexp();" > 
<?
					for ($i=0; $i<count($datatypes); $i++) {
						if ($datatypes[$i]==$v1sel) $s='selected'; else $s=''; 	
						echo "<option value=\"$datatypes[$i]\" $s>$datatypes[$i] \n"; 
					}
?>
					</select>
<? /* 
					<label for="tg_id">targets</label>
					<label for="sb_id">scale bar</label>
					<input type="checkbox" id="tg_id" name="f_tg"> 
					<input type="checkbox" id="sb_id" name="f_sb"> 
*/ ?>
				</td>
			 </tr>
			 <tr>
				<td>
<?
$preset=$v1sel;
if ($v1pre==1) {
?>
		<iframe name="ifv1" 
                        src="getpreset.php?id=<?=$fileId[0]?>&preset=<?=$preset?>&vf=1"
			frameborder="0" width="100%" height="50"
			marginheight="1" marginwidth="5"
			scrolling="no" ></iframe>
<?

} else echo "&nbsp;"
?>
				</td>
			 </tr>
			 <tr>
				<td>
<?
$sb = ($v1scalebar) ? '&sb=1' :'';
$imgsrc = "$imgv1?preset=$preset&session=$expId&id=".$fileId[0]."&t=80&s=256&tg=1".$sb;
?>
<a href="javascript:popUp('nw.php?Lv1&preset=<?=$preset?>&session=<?=$expId?>&id=<?=$fileId[0]?>');"><img name="newimgview1" border="0" width="256" src="<?=$imgsrc?>" ></a>
				</td>
			 </tr>
	<? } ?>
			</table>
			</td>
		 </tr>
		</table> 
		<!-- Fin Table View1 -->
<? } ?>
