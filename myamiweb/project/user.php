<?
require "inc/project.inc.php";
require("inc/leginon.inc");
require "inc/user.inc.php";
require "inc/utilpj.inc.php";
if ($_GET['cp'])
	$selectedprojectId=$_GET['cp'];
if ($_POST['currentproject'])
	$selectedprojectId=$_POST['currentproject'];
$login_check = $dbemauth->is_logged();

$is_admin = privilege();
login_header('User');
$userdata = new user();
$users = $userdata->getUsers(true);

foreach ($users as $k=>$p) {
	$email = $p['email'];
	$pId = $p['userId'];
	if ($is_admin) {
		$users[$k]["edit"]="<a href='updateuser.php?id=$pId'><img border='0' src='img/edit.png'></a>";
		$users[$k]["del"]="<a href='deleteuser.php?id=$pId'><img border='0' src='img/del.png'></a>";
	}
	$users[$k]["name"]=$p['name'];
	$users[$k]["email"]="<a href='mailto:$email'>".$p['email']."</a>";
	$users[$k]["institution"]=$p['institution']." ".$p['dept']." ".$p['address'];
	$users[$k]["phone"]=$p['phone'];
}

$columns=array(
	'name'=>'Name', 'email'=>'Email',
	'username'=>'username',
	'institution'=>'Institution',
	'phone'=>'Phone');
$columns=array(
	'firstname'=>'First Name', 'lastname'=>'Last Name',
	'name' =>'Login Name',
	'email' => 'Email'
	);
$display_header=true;

if ($is_admin) {
	$columns=array_merge(array('edit'=>'', 'del'=>''), $columns);
}

project_header("Users");
if ($is_admin) {
	echo "<a class='header' href='updateuser.php'>Add new user</a>"; 
}
echo " - currently ".count($users)." users";
echo data2table($users, $columns, $display_header);
project_footer();
?>
