<? if ($v2Id!=0) { ?>
<input type="hidden" name = "v2view" value="<?=$v2view?>">
		<!-- Debut Table View1 -->
		<table class="bgcolor1" border="0" cellspacing="0" cellpadding="1">
		 <tr>

			<td width="16"><a href="javascript:newexp();"
					onmouseover="imageon('v2close', 'close', '')"
					onmouseout="imageoff('v2close', 'close', '')" 
					onclick="setview('v2', 'off');"
					><img name="v2close" src="img/close_off.gif" border="0" height="16" vspace="0"></a></td>
			<td width="16"><a href="javascript:newexp();"
					onmouseover="imageon('v2open', 'open', '')" 
					onmouseout="imageoff('v2open', 'open', '')" 
					onclick="setview('v2', 'on');"
					><img name="v2open" src="img/open_off.gif" border="0" height="16" vspace="0"></a></td>
	<td width="193" nowrap="nowrap">View 2</td>
			<td width="15"><a href="javascript:toggleimage('v2target_bt', 'target_bt'); newfile();"
					onmouseover="imageonfocus('v2target_bt', 'target_bt', '_over')" 
					onmouseout="imageonfocus('v2target_bt', 'target_bt', '')" 
					><img name="v2target_bt" src="img/target_bt_off.gif" border="0" height="15" vspace="0"></a></td>
			<td width="15"><a href="javascript:toggleimage('v2scale_bt', 'scale_bt'); newfile();"
					onmouseover="imageonfocus('v2scale_bt', 'scale_bt', '_over')" 
					onmouseout="imageonfocus('v2scale_bt', 'scale_bt', '')" 
					><img name="v2scale_bt" src="img/scale_bt_off.gif" border="0" height="15" vspace="0"></a></td>
<? /*
			<td><a href="javacript:void(0)"><img src="img/close_off.gif" border="0" height="16" vspace="0"></a> <a href="javacript:void(0)"><img src="img/open_off.gif" border="0" height="16" vspace="0"></a></td><td>View 1</td>
*/ ?>
		 </tr>
		 <tr>
			<td colspan="5">	
			<input type="hidden" name = "v2sel" value="<?=$v2sel?>">
			<table class="bgcolor0" border="0" cellspacing="0" cellpadding="0">
<? if ($v2view=='on') { ?>
			 <tr>
				<td height="1" width="259">
					<select name = "v2list" onchange = "setlist(); newexp();" > 
<?
					for ($i=0; $i<count($datatypes); $i++) {
						if ($datatypes[$i]==$v2sel) $s='selected'; else $s=''; 	
						echo "<option value=\"$datatypes[$i]\" $s>$datatypes[$i] \n"; 
					}
?>
					</select>
				</td>
			 </tr>
			 <tr>
				<td>
<?
$preset=$v2sel;
if ($v2pre==1) {
?>
		<iframe name="ifv2" 
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
$imgsrc = "$imgv2?preset=$preset&session=$expId&id=".$fileId[0]."&t=80&s=256&tg=1";
?>
<a href="javascript:popUp('nw.php?Lv2&preset=<?=$preset?>&session=<?=$expId?>&id=<?=$fileId[0]?>');"><img name="newimgview2" border="0" width="256" src="<?=$imgsrc?>" ></a>
				</td>
			 </tr>
	<? } ?>
			</table>
			</td>
		 </tr>
		</table> 
		<!-- Fin Table View1 -->
<? } ?>
