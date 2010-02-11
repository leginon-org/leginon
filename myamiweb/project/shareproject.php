<?
require("inc/project.inc.php");
require("inc/leginon.inc");
#require("inc/user.inc.php");
require("inc/share.inc.php");
#require_once("inc/mysql.php");
if ($_GET[pId])
	$projectId=$_GET[pId];
if ($_POST[currentproject])
	$projectId=$_POST[currentproject];
$project = new project();
project_header("Share Project");
checkProjectAccessPrivilege($projectId);
$is_admin = checkProjectAdminPrivilege($projectId);
?>

<form method="POST" name="projectform" action="<?=$_SERVER['REQUEST_URI'] ?>">
<input type="hidden" name="projectId" value="">
<?
if ($is_admin) {
// --- add something for admin only
}
?>
<table class="tableborder" border="1" valign="top">
<?
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
<h3>Share info </h3>
<p>
<?
	if ($is_admin) {
?>
<img src="img/info.png"> Users with no password set won't be listed; go
to <a class="header" href="user.php">[user]</a> to update user's profile.
</p>
<?
	};
	$db = $project->mysql;
	$userId = $_POST['userId'];
	if ($_POST['bt']=="add") {
		if ($userId && $projectId) {
			$project->addProjectOwner($userId, $projectId);
		}
	} else if ($_POST['bt']=="del" && $_POST['ck']) {
		$project->removeProjectOwner($_POST['ck'], $projectId);
	}


	$q = "select u.`DEF_id` as userId, u.* from UserData u "
			."where "
			."u.password<>'' "
			."order by `full name`";
	$users = $leginondata->mysql->getSQLResult($q);
	if ($is_admin) {
	$bt_add= "<input class='bt1' type='submit' name='bt' value='add'>";
	?>
	<select name="userId">
	<?
		echo "<option value='default' > -- select user -- </option>";
		foreach($users as $user) {
			$s = ($user['userId']==$_POST['userId']) ? "selected" : "";
			$o = ($user['full name']) ? $user['full name'] : $user['name'];
			echo "<option value='".$user['userId']."' $s >"
					.$o
					."</option>\n";
			
		}
	?>
	</select>
	<?
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
		foreach ($owners as $v) {
			$ck = "<input type='checkbox' name='ck[]' value='".$v['userId']."'>";
			$cuser = ($v['full name']);
#			$cuser = ($v['lastname']||$v['firstname']) ? $v['lastname']." ".$v['firstname']:$v['login'];
			echo "<tr>";
			echo "<td>";
			echo " - ".$cuser;
			echo "</td>";
			if ($is_admin) {
				echo "<td>";
				echo $ck;
				echo "</td>";
			}
			echo "</tr>";
		}
		echo "</table>";
		echo "<br>";
		if ($is_admin) {
			echo "delete selected: ".$bt_del;
		}
	}
	echo "<pre>";
		// print_r($r);
	echo "</pre>";
	
?>
</form>
<?
project_footer();
?>
