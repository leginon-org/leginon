<? if ($mvId!=0) { ?>
		<!-- Debut Table Main View -->
		<table class="bgcolor1" border="0" cellpadding="1" cellspacing="0" >
		 <tr>
			<td nowrap="nowrap">Main View</td>
			<td width="35" nowrap="nowrap"><a href="javascript:toggleimage('mvtarget_bt', 'target_bt'); newfile();"
					onmouseover="imageonfocus('mvtarget_bt', 'target_bt', '_over')" 
					onmouseout="imageonfocus('mvtarget_bt', 'target_bt', '')" 
					><img name="mvtarget_bt" src="img/target_bt_off.gif" border="0" height="15" vspace="0" hspace="0"></a>
			<a href="javascript:toggleimage('mvscale_bt', 'scale_bt'); newfile();"
					onmouseover="imageonfocus('mvscale_bt', 'scale_bt', '_over')" 
					onmouseout="imageonfocus('mvscale_bt', 'scale_bt', '')" 
					><img name="mvscale_bt" src="img/scale_bt_off.gif" border="0" height="15" vspace="0" hspace="0"></a></td>
			<td width="400">&nbsp;</td>
		 </tr>
		 <tr>
			<td colspan="3">
			<table class="bgcolor0" border="0" cellpadding="0" cellspacing="0" >
			 <tr>
				<td>
					<input type="hidden" name = "mvsel" value="">
					<select name = "mlist" onchange = "setlist(); newexp(); " > 
<?
					for ($i=0; $i<count($datatypes); $i++) {
						if ($datatypes[$i]==$mvsel) $s='selected'; else $s=''; 	
						echo "<option value=\"$datatypes[$i]\" $s>$datatypes[$i] \n"; 
					}
?>
					</select>
				</td>
				<td>
					<input id=backbutton type=button name=back value =" Back " onclick = "decIndex(); newfile(); getdata(); updatemap();" > 
				</td>
				<td>
					<input id=nextbutton type=button name=next value =" Next " onclick = "incIndex(); newfile(); getdata(); updatemap();" >
				</td>
				<td>
					<a href="javascript:downloadfile();" ><img src="img/download.gif" border="0" vspace="0" ></a></td>
				<td>
					<input id="filenametext" type="text" name="filename_text" size="<? echo $mvtextsize ?>" onchange = "newenterfile(); newfile(); <? if ($treeframe!=0) echo " GetData();"; ?> " > 
				</td>
			 </tr>
			 <tr>
				<td colspan="5">
<?
$preset=$mvsel;
if ($mvpre==1) {
?>
	
		<iframe	class=textarea name="ifmv" 
                        src="getpreset.php?id=<?=$fileId[0]?>&preset=<?=$preset?>"
			frameborder="0" width="100%" height="20"
			marginheight="1" marginwidth="5"
			scrolling="no" ></iframe>
<?	 

} else echo "&nbsp;"
?>
				</td>
			 </tr>
			 <tr>
				<td colspan="5" valign=top height="278" width="421" rowspan="6">
<?
$imgsrc = "$imgmv?preset=$preset&session=$expId&id=".$fileId[0]."&t=80&s=512&tg=1";
?>
<a href="javascript:popUp('nw.php?Lmv&preset=<?=$preset?>&session=<?=$expId?>&id=<?=$fileId[0]?>');"><img name="newimgmv" border="0" width="512" src="<?=$imgsrc?>" ></a>
				</td>
			 </tr>
			</table>
			</td>
	 	 </tr>
		</table>
		<!-- Fin Table Main View -->
<? } else echo "&nbsp;"; ?>
