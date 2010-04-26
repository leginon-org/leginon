<?php
require_once "inc/dbemauth.php";
require_once "inc/admin.inc";
require_once "inc/user.inc.php";


admin_header('onload="init()"');

$login_check = $dbemauth->is_logged();
$is_admin = (privilege('users')>3);

$userId = $_GET['userId'];
$groups = $leginondata->getGroups('name');
$userdata = new user();

	// if userId is not null, setup variables for edit user.
	// otherwise setup variable for add new user
	if($userId){
		$action="update";
		$userinfo = $userdata->getUserInfo($userId);

	}else
		$action="add";
	
	$checkpass=true;

	echo "<h3>Users Detail ($action user):</h3>";
if($_POST){
	
	// setup variables
	foreach($_POST as $k=>$v)
		if ($k!='submit'){
			$v = trim($v);
			$$k = addslashes($v);
			$userinfo[$k] = addslashes($v);
		}

	if(!haspass)
		$chpass=true;
	
	if($_POST['submit']=='update'){
			
		$updateProfile=$dbemauth->updateUser($userId, $username, $firstname, $lastname, $title, $institution, 
											$dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, 
											$url, $chpass, $mypass1, $mypass2, $groupId);
	}else{
		$updateProfile = $dbemauth->adminRegister($username, $firstname, $lastname, $title, $institution, 
											$dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, 
											$url, $mypass1, $mypass2, $groupId);
		
	}
	if ($updateProfile != 2) {
		$submitResult = '<p><font face="Arial, Helvetica, sans-serif" size="4" color="#FF2200">'.$updateProfile.'</font></p>';
	}
	else{
		$submitResult = '<p><font face="Arial, Helvetica, sans-serif" size="4" color="#FF2200">Your update has been submitted.</font></p>';
		$userId = $userdata->getUserIdByUsername($username);
		$userinfo = $userdata->getUserInfo($userId);
	}
			
	echo $submitResult;
}
?>
<form name="userform" action="<?=$_SERVER['PHP_SELF'] ?>?id=<?=$userId?>" method="POST">
  <input type="hidden" name="userId" value="<?=$userId?>">
  <table border=0 cellspacing=0 cellpadding=2>
	<tr>
	<td>
		<label for="username">User name: <?php if(empty($userId)) echo "<font color='red'>*</font>"; ?></label><br />
		<label for="groupname">Group Name</label><br />
	</td>
	<td>
		<?php if($action=='update'){
				 echo '<b>' . $userinfo['username'] . '</b><br />';
			  }else{
			  	 echo "<input class='field' type='text' value='". $username . "' name='username' id='username'><br />";
			  }
		?>
		
		<select name="groupId">
		<?php 
			foreach($groups as $group){
				$groupName = $group['name'];
				$groupListId = $group['DEF_id'];
				
				if($userinfo['groupId']==$groupListId)
					echo "<option selected value='$groupId'>$groupName</option>";
				else
					echo "<option value='$groupListId'>$groupName</option>";
			}
		?>
		</select>
	</td>
	<?php if($action=='update'){ ?>
	<td>
		<?=($checkpass) ? "<br />" : "" ?>
		<label for="mypass1">Password:</label><br />
		<label for="mypass2">confirm:</label><br />
	</td>
	<td>
		<? if ($checkpass) { ?>
		<input type="checkbox" name="chpass"><font color="red">Change Password</font><br />
		<? } ?>
		<input class="field" type="password" value="" name="mypass1" size="15" ><br />
		<input class="field" type="password" value="" name="mypass2" size="15" ><br />
	</td>
	<?php }else{ ?>
	<td>
		<label for="mypass1">Password: <font color="red">*</font></label><br />
		<label for="mypass2">confirm: <font color="red">*</font></label><br />
	</td>
	<td>
		<input class="field" type="password" value="" name="mypass1" size="15" ><br />
		<input class="field" type="password" value="" name="mypass2" size="15" ><br />
	</td>	
	<?php } ?>
	</tr>
	<tr>
	<td>
		<label for="Firstname">First name: <font color="red">*</font></label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['firstname']; ?>" name="firstname" id="firstname" size="15" ><br>
	</td>
	<td>
		<label for="Lastname">Last name: <font color="red">*</font></label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['lastname']; ?>" name="lastname" id="lastname" size="15" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="title">Email: <font color="red">*</font></label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['email']; ?>" name="email" id="email" size="20" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="title">Title: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['title']; ?>" name="title" id="title" size="20" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="institution">Institution: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['institution']; ?>" name="institution" id="institution" size="25" ><br>
	</td>
	<td>
		<label for="dept">Dept: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['dept']; ?>" name="dept" id="dept" size="20" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="address">Address: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['address']; ?>" name="address" id="address" size="25" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="city">City: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['city']; ?>" name="city" id="city" size="10" ><br>
	</td>
	<td>
		<label for="statecountry">State/Country: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['statecountry']; ?>" name="statecountry" id="statecountry" size="10" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="zip">Zip: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['zip']; ?>" name="zip" id="zip" size="10" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="phone">Phone: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['phone']; ?>" name="phone" id="phone" size="15" ><br>
	</td>
	<td>
		<label for="fax">Fax: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?php echo $userinfo['fax']; ?>" name="fax" id="fax" size="15" ><br>
	</td>
	</tr>
	<tr>
	<td>
		<label for="url">URL: </label>
	</td>
	<td>
	
		<input class="field" type="text" value="<?php echo $userinfo['url']; ?>" name="url" id="url"><br>
	</td>
	</tr>
	<tr>
	<td>
		<input type="submit" value="<?=$action?>" name="submit">
	</td>
	</tr>
  </table>
</form>
<?php 
/* footer comment */
admin_footer();
?>
