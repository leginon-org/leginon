<form name="userform" action="<?=$_SERVER['PHP_SELF'] ?>" method="POST">
  <input type="hidden" name="userId" value="<?=$userId?>">
  <table border=0 cellspacing=0 cellpadding=2>
	<tr>
	<td>
		<label for="username">username: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$username?>" name="username" id="username" size="15" ><br>
	</td>
	<td>
		<?=($checkpass) ? "<br />" : "" ?>
		<label for="mypass1">password:</label><br />
		<label for="mypass2">confirm:</label><br />
	</td>
	<td>
		<? if ($nopass) { ?>
		<font color="red">no password set</font><br />
		<? } else if ($checkpass) { ?>
		<font color="red">check to change</font>:<input type="checkbox" name="chpass"><br />
		<? } ?>
		<input class="field" type="password" value=".<?$password?>." name="mypass1" size="15" ><br />
		<input class="field" type="password" value="" name="mypass2" size="15" ><br />
	</td>
	</tr>
	<tr>
	<td>
		<label for="email">Email: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$email?>" name="email" id="email"><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="Firstname">firstname: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$first_name?>" name="firstname" id="firstname" size="15" ><br>
	</td>
	<td>
		<label for="Lastname">lastname: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$last_name?>" name="lastname" id="lastname" size="15" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="title">Title: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=htmlentities($title)?>" name="title" id="title" size="20" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="institution">Institution: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=htmlentities($institution)?>" name="institution" id="institution" size="25" ><br>
	</td>
	<td>
		<label for="dept">Dept: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=htmlentities($dept)?>" name="dept" id="dept" size="20" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="address">Address: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=htmlentities($address)?>" name="address" id="address" size="25" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="city">City: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$city?>" name="city" id="city" size="10" ><br>
	</td>
	<td>
		<label for="statecountry">State/Country: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$statecountry?>" name="statecountry" id="statecountry" size="10" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="zip">Zip: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$zip?>" name="zip" id="zip" size="10" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="phone">Phone: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$phone?>" name="phone" id="phone" size="15" ><br>
	</td>
	<td>
		<label for="fax">Fax: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$fax?>" name="fax" id="fax" size="15" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="url">URL: </label>
	</td>
	<td>
	
		<input class="field" type="text" value="<?=$url?>" name="url" id="url"><br>
	</td>
	</tr>
	<tr>
	<td colspan="2">
	<fieldset>
	<legend><b>Group:</b></legend>
<?
if ($login_is_admin) {
?>
	<select size="1" name="group" > 
	<?php foreach ($groups as $group) {
		$s = ($groupId == $group['DEF_id'] ) ? 'selected' : '';
		echo "<option value='".$group['DEF_id']."' $s >".$group['name']."</option>\n";
		}
	?>
	</select>
<?
} else {
	echo $groupname;
}
?>
	</fieldset>
	</td>
	</tr>
	<tr>
	<td>
		<input type="submit" value="<?=$action?>" name="submit">
	</td>
	</tr>
  </table>
</form>
