<? 

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

if ($mvId!=0) { ?>

		<!-- Debut Table Main View -->
		<table class="bgcolor1" border="0" cellpadding="1" cellspacing="0" >
		 <tr>
			<td>Image Type</td>
		 </tr>
		 <tr>
			<td>
			<table class="bgcolor0" border="0" cellpadding="0" cellspacing="0" >
			 <tr>
				<td>
					<input type="hidden" name = "mvsel" value="">
					<select name = "mlist" onchange = "setlist(); newexp(); " > 
<?
					for ($i=0; $i<count($datatypes); $i++) {
					if ($mvsel=='') {
						if ($datatypes[$i]==$mvImg) $s='selected'; else $s=''; 	
					} else {
						if ($datatypes[$i]==$mvsel) $s='selected'; else $s=''; 	
					}
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
					<input id="filenametext" type="text" name="filename_text" size="<? echo $mvtextsize ?>" onchange = "newenterfile(); newfile(); <? if ($treeframe!=0) echo " GetData();"; ?> " > 
				</td>
			 </tr>
			 <tr>
				<td colspan=4 valign=top height=512 width=512 >
<?
$iframesize = ($_GET["ifs"]==1) ? 'width=100% height=100% ' : 'width="512" height="512"';
$src = "src=\"getimage.php?tmpl=$imgmv&table=$tmv&session=$expId&id=".$fileId[0]."&s=1\"";
?>
<iframe id=iframeimg name="picturebox" <? echo "$iframesize  $src" ?> scrolling="auto" ></iframe>
<?
 /*
			<script> <!--   
			document.writeln(" <A HREF=\"javascript:popUp('nwi.php?Lmv&table="+escape(jstmv)+"');\" >"); 
			document.writeln(" <IMG  NAME = \"newimgmv\" BORDER=\"0\" "); 
			document.writeln(" SRC= \""+jsimgmv+"?table="+escape(jstmv)+"&session="+escape(jsexpId)+"&id="+escape(jsfileId)+"&s=1\"></A>"); 
			document.writeln(" </A>"); 
			//--> </script>
*/ ?>
				</td>
			 </tr>
			</table>
			</td>
	 	 </tr>
		</table>
		<!-- Fin Table Main View -->
<? } else echo "&nbsp;"; ?>
