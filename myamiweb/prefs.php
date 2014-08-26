<?php
require_once "inc/leginon.inc";
require_once "inc/login.inc";
require_once "inc/pref.inc";

if (!$login_check = $dbemauth->is_logged()) {
	header('Location: '.BASE_URL);
}

/**
 * [0] => username
 * [1] => userid
 * [2] => privilege
 */
$username = $login_check[0];
$userId = $login_check[1];

login_header("My Preferences");
?>
<h3>My Profile</h3>
<?
$haspass = $dbemauth->hasPassword($username);
if ($_POST) {
	if ($_POST['submit']=='update') {
		$chpass=false;
		foreach($_POST as $k=>$v)
			if ($k!='submit'){
				$v = trim($v);
				$$k = addslashes($v);
			}
		//can not use addslashes on checkbox value
		$advanced = ($_POST['advanced']=='on') ? 1:0;
			
		if (!$haspass)
			$chpass=true;

		$newProfile=$dbemauth->updateUser($userId, $username, $firstname, $lastname, $title, $institution, $dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, $url, $chpass, $mypass1, $mypass2, $groupId=null, $noleginon=0, $advanced);

		if ($newProfile!=2) {
			echo '<p><font face="Arial, Helvetica, sans-serif" size="4" color="#FF2200">'.$newProfile.'</font></p>';
		}
		else{
			echo '<p><font face="Arial, Helvetica, sans-serif" size="4" color="#FF2200">Your update has been submitted.</font></p>';
		}
	}
}
$userinfo = $dbemauth->getUserInfo($username);

$action="update";
$checkpass=true;
$advancedval = ($userinfo['advanced'] == 1) ? "CHECKED":"";
?>
<form name="userform" action="<?=$_SERVER['PHP_SELF'] ?>" method="POST">
  <input type="hidden" name="userId" value="<?=$userId?>">
  <table border=0 cellspacing=0 cellpadding=2>
	<tr>
	<td>
		<label for="username">User name: </label><br />
		<label for="groupname">Group Name</label><br />
	</td>
	<td>
		<b><?php echo $userinfo['username']; ?></b><br />
		<b><?php echo $userinfo['name']; ?></b><br />
	</td>
	<td>
		<?=($checkpass) ? "<br />" : "" ?>
		<label for="mypass1">Password:</label><br />
		<label for="mypass2">confirm:</label><br />
	</td>
	<td>
		<? if (!$haspass) { ?>
		<font color="red">no password set</font><br />
		<? } else if ($checkpass) { ?>
		<input type="checkbox" name="chpass"><font color="red">Change Password</font><br />
		<? } ?>
		<input class="field" type="password" value="" name="mypass1" size="15" ><br />
		<input class="field" type="password" value="" name="mypass2" size="15" ><br />
	</td>
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
		<input type="checkbox" name="advanced" <?=$advancedval?> >
		<label for="advanced">Always show advanced options</label><br />
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
// stop the script for now, and figure out what below code does later.
// not super important for now.
exit(); 

?>
<h3>My Preferences</h3>
<? if (!$username)
	exit;

$comment_pref = new ViewerPreference;
$commentId = $_POST['commentId'];
$categoryId = $_POST['categoryId'];

$viewcomment = $_POST['viewcomment'];
$viewmyexp = $_POST['myexponly'];
$viewstat = $_POST['viewstat'];

if ($_POST['v']=="save") {
	if ($username)
		$comment_pref->update_pref($username, $viewcomment, $viewmyexp, $viewstat);
}

if ($_POST['p']=="Del") {
	$comment_pref->del_comment_setting($commentId);
}
if ($_POST['c']=="Add") {
	$name = $_POST['cat_lbl'];
	$comment_pref->add_category($commentId, $name);
}
if ($_POST['p']=="Add") {
	$name = $_POST['comment_name'];
	if($username && $name)
		$comment_pref->add_comment_setting($username, $name);
}
if ($_POST['c']=='Del') {
	if($username && $categoryId)
		$comment_pref->del_category($categoryId);
}
$addsession = $_POST['addsession'];
$delsession = $_POST['delsession'];
$sessionId = $_POST['sessionId'];
$commentsessionId = $_POST['commentsessionId'];
if ($addsession && $sessionId && $username && $commentId) {
	$comment_pref->add_comment_session($username, $commentId, $sessionId);
} else 
if ($delsession && $commentsessionId && $username && $commentId) {
	$comment_pref->del_comment_session($commentsessionId);
} 

$mypref = $comment_pref->get_pref($username);
$commentinfo = $comment_pref->get_comment_info($commentId);
$mycategory = $comment_pref->get_category($commentId);
$mycommentpref = $comment_pref->get_comment_setting($username);
$commentsessions = $comment_pref->get_comment_sessions($username, $commentId);
$sessions = $leginondata->getSessions('description', $projectId);
$viewstat_ck = ($mypref['viewstat']=='Y') ? 'checked' : '';
$viewcomment_ck = ($mypref['viewcomment']=='Y') ? 'checked' : '';
$viewmyexp_ck = ($mypref['viewmyexp']=='Y') ? 'checked' : '';
?>
<form method="POST" action="<?=$_SERVER['REQUEST_URI']?>" name="pref">
<table border=0>
<tr valign=top>
	<td>
<?  echo divtitle("Main Page"); ?>
	</td>
</tr>
<tr>
	<td>
View Stats:
<input class="bt1" type="checkbox" <?=$viewstat_ck?> value='Y' name="viewstat" >
	</td>
</tr>
<tr valign=top>
	<td>
<?  echo divtitle("Viewer"); ?>
View comment
<input class="bt1" type="checkbox" <?=$viewcomment_ck?> value='Y' name="viewcomment" ><br>
View my experiment only 
<input class="bt1" type="checkbox" <?=$viewmyexp_ck?> value='Y' name="myexponly" ><br>
<br>
<input class="bt1" type="submit" name="v" value="save">
	</td>
</tr>
<tr valign=top>
	<td>
<?  echo divtitle("Comment Setup"); ?>
	</td>
</tr>
<tr>
	<td>
<table>
	<tr>
	<td>
<table>
	<tr>
	<td colspan="2">
	Create your comment label (i.e. : mycomment1 ): <br>
	<input class="field" name="comment_name" value="" size="15">
	<input class="bt1" type="submit" name="p" value="Add">
	</td>
	</tr>
	<tr>
	<td>
<?
if ($mycommentpref) {
	echo '<select name="commentId" size="5" >';
	foreach ($mycommentpref as $pref) {
		$s = ($pref['id']==$_POST['commentId']) ? "selected" : "";
		echo "<option value='".$pref['id']."' $s >".$pref['name']."</option>\n";
	}
	echo '</select>';
echo '
	</td>
	<td>
	Edit property:
	<input class="bt1" type="submit" name="p" value="Edit"><br>
	<input class="bt1" type="submit" name="p" value="Del">
';
}
?>
	</td>
	</tr>
</table>
	</td>
	<td>
<? if ($commentId) { ?>
<table>
	<tr>
	<td colspan="2">
Category for <b>"<?=$commentinfo['name']?>"</b> (i.e. : A, Good, Ok):<br>
<input class='field' type='text' size='15' name='cat_lbl'>
<input class="bt1" type="submit" name="c" value="Add">
	</td>
	</tr>
	<tr>
	<td>
<? if ($mycategory) { 
echo '<select name="categoryId" size="5" >';
foreach ($mycategory as $category) {
	echo "<option value='".$category['id']."' >".$category['name']."</option>\n";
}
echo '</select>';
echo '
	</td>
	<td>
<input class="bt1"  type="submit" name="c" value="Del">
';
} ?>
	</td>
	</tr>
</table>
	</td>
	</tr>
	<tr>
	<td colspan="2">
	<table>
		<tr>
		<td>

<?
echo 'Add Sessions to comment type <b>"'.$commentinfo['name'].'"</b><br>';
echo '<select style="width: 500" name="sessionId" size="5" >';
foreach ($sessions as $session) {
	$maxlength=50;
	$sessionname=$session['name'];
	if (strlen($sessionname)>$maxlength) {
		$sessionname=substr($sessionname,0,$maxlength)."... ";
	}
	echo "<option value='".$session['id']."' >".$sessionname."</option>\n";
}
echo '</select>';
echo '</td><td>';
echo '<input class="bt1"  type="submit" name="addsession" value="&gt;&gt;">';
echo '<br><br>';
echo '<input class="bt1"  type="submit" name="delsession" value="&lt;&lt;">';
echo '</td><td>';
echo 'selected Sessions<br>';
echo '<select name="commentsessionId" size="5" >';
foreach ($commentsessions as $commentsession) {
	$info=$leginondata->getSessionInfo($commentsession['sessionId']);
	$sessionname=$info['Name'];
	echo "<option value='".$commentsession['id']."' >".$sessionname."</option>\n";
}
echo '</select>';
?>
		</td>
		</tr>
	</table>
<? } ?>
	</td>
	</tr>
</table>
	</td>
</tr>
</table>
</form>
<?
login_footer();

function add_cat($name) {
	$html = "Label $name <input class='field' type='text' size='10' name='$name'>";
	$html .="<br>";
	return $html;
}


?>
