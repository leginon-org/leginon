<<<<<<< HEAD
<?php
=======
<?
>>>>>>> origin/trunk
require_once("inc/project.inc.php");
require_once("inc/leginon.inc");
require_once("inc/share.inc.php");

if ($_GET['projectId'])
	$projectId=$_GET['projectId'];
if ($_POST['currentproject'])
	$projectId=$_POST['currentproject'];
$project = new project();
project_header("Project Owners");
checkProjectAccessPrivilege($projectId);
$is_admin = checkProjectAdminPrivilege($projectId);
?>

<<<<<<< HEAD
<form method="POST" name="projectform" action="<?php $_SERVER['REQUEST_URI'] ?>">
<input type="hidden" name="projectId" value="">
<?php
=======
<form method="POST" name="projectform" action="<?=$_SERVER['REQUEST_URI'] ?>">
<input type="hidden" name="projectId" value="">
<?
>>>>>>> origin/trunk
if ($is_admin) {
// --- add something for admin only
}
?>
<h3>Selected Project</h3>

<table class="tableborder" border="1" valign="top">
<<<<<<< HEAD
<?php
=======
<?
>>>>>>> origin/trunk
	$info = $project->getProjectInfo($projectId);
	$keys_to_display = array('Name');
	foreach ($info as $k=>$v) {
	if (!in_array($k, $keys_to_display))
		continue;
	echo "<tr> ";
	echo "<td> ";
	echo $k;
	echo "</td> ";
	echo "<td> ";
	echo $v;
	echo "</td> ";
	echo "</tr>\n";
	}
?>
</table>
<h3>Select an owner to add to this project:</h3>
<<<<<<< HEAD
<?php
=======
<?
>>>>>>> origin/trunk
	if ($is_admin) {
?>
<p>
<img src="img/info.png"> Users with no password set won't be listed; go
<<<<<<< HEAD
to <a class="header" href="<?php echo BASE_URL.'user.php'; ?>">[user]</a> to update user's profile.
</p>
<?php
	};
	$db = $project->mysql;
	$loginId = getLoginUserId();
	$userId = $_POST['userId']; //User to add
=======
to <a class="header" href="<? echo BASE_URL.'user.php'; ?>">[user]</a> to update user's profile.
</p>
<?
	};
	$db = $project->mysql;
	$userId = $_POST['userId'];
>>>>>>> origin/trunk
	if ($_POST['bt']=="add") {
		if ($userId && $projectId) {
			$project->addProjectOwner($userId, $projectId);
		}
	} else if ($_POST['bt']=="del" && $_POST['ck']) {
<<<<<<< HEAD
		$is_self = false;
		if ($loginId !== true && privilege('projects') < 4) {
			foreach ($_POST['ck'] as $cki) {
				if ($cki == $loginId ) $is_self = true;
			}
		}
		if ( $is_self ) {
			$error = "<p> Error: Can not remove self. Ask for administrative asistance. </p>";
		} else {
			$project->removeProjectOwner($_POST['ck'], $projectId);
			$error = '';
		}
=======
		$project->removeProjectOwner($_POST['ck'], $projectId);
>>>>>>> origin/trunk
	}


	$q = "select u.`DEF_id` as userId, u.* "
			.",concat(u.firstname,' ',u.lastname) as `full name` "
			."from UserData u "
			."where "
			."u.password<>'' "
			."order by u.`lastname`";
	$users = $leginondata->mysql->getSQLResult($q);
	if ($is_admin) {
	$bt_add= "<input class='bt1' type='submit' name='bt' value='add'>";
	?>
	<select name="userId">
<<<<<<< HEAD
	<?php
=======
	<?
>>>>>>> origin/trunk
		echo "<option value='default' > -- select user -- </option>";
		foreach($users as $user) {
			$s = ($user['userId']==$_POST['userId']) ? "selected" : "";
			$firstname = $user['firstname'];
			$lastname = $user['lastname'];
			echo "<option value='".$user['userId']."' $s >"
					.$firstname
					." "
					.$lastname
					."</option>\n";
			
		}
	?>
	</select>
<<<<<<< HEAD
	<?php
=======
	<?
>>>>>>> origin/trunk
	echo $bt_add;
	if ($ln=$_GET['ln']) {
		echo "<a class=\"header\" href=\"$ln\"> Back to project list</a>";
	}
	} else {
	echo '<font color="red">[Login as owner or admin to change sharing]</font>';
	}
	echo "<br />";
	$owners = $project->getProjectOwners($projectId);
	echo "<br>";
	echo "Project owned by: <br>";
	$bt_del = "<input class='bt1' type='submit' name='bt' value='del'>";
	echo "<table>";
	if ($owners) {
<<<<<<< HEAD
		$loginId = getLoginUserId();
=======
>>>>>>> origin/trunk
		foreach ($owners as $v) {
			$ck = "<input type='checkbox' name='ck[]' value='".$v['userId']."'>";
			$cuser = ($v['lastname']||$v['firstname']) ? $v['firstname']." ".$v['lastname']:$v['username'];
			echo "<tr>";
			echo "<td>";
			echo " - ".$cuser;
			echo "</td>";
<<<<<<< HEAD
			if ($is_admin && count($owners) >= 1) {
				echo "<td>";
				if ($loginId !== true && privilege('projects') < 4 && count($owners)==1) {
					//Do not allow removing last owner when a user is logged in
					//with lower project administrator privilege.
					echo '';
				} else {
					echo $ck;
				}
=======
			if ($is_admin && count($owners) > 1) {
				echo "<td>";
				echo $ck;
>>>>>>> origin/trunk
				echo "</td>";
			}
			echo "</tr>";
		}
		echo "</table>";
		echo "<br>";
<<<<<<< HEAD
		if ($is_admin && count($owners) >= 1) {
			echo $error;
=======
		if ($is_admin && count($owners) > 1) {
>>>>>>> origin/trunk
			echo "delete selected: ".$bt_del;
		}
	}
	echo "<pre>";
		// print_r($r);
	echo "</pre>";
	
?>
</form>
<<<<<<< HEAD
<?php
=======
<?
>>>>>>> origin/trunk
project_footer();
?>
