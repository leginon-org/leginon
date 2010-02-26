<?php

require_once "inc/admin.inc";
require_once "inc/user.inc.php";
require_once "inc/utilpj.inc.php";

admin_header('onload="init()"');

$login_check = $dbemauth->is_logged();
$is_admin = (privilege('users')>3);

$orderBy = $_GET['sort'];
$userdata = new user();
$allUsers = $userdata->getUsers($orderBy);

foreach ($allUsers as $k=>$p) {
	$email = $p['email'];
	$pId = $p['userId'];
	if ($is_admin) {
		$users[$k]["edit"]="<a href='adduser.php?id=$pId'><img border='0' src='project/img/edit.png'></a>";
		//$users[$k]["del"]="<a href='deleteuser.php?id=$pId'><img border='0' src='img/del.png'></a>";
	}
	//$users[$k]["name"]=$p['lastname'].(($p['firstname'])? ', '.$p['firstname']:'');
	$users[$k]["lastname"]=$p['lastname'];
	$users[$k]["firstname"]=$p['firstname'];
	$users[$k]["username"]=$p['username'];
	$users[$k]["email"]="<a href='mailto:$email'>".$p['email']."</a>";
	$users[$k]["institution"]=$p['institution']." ".$p['dept']." ".$p['address'];
	$users[$k]["phone"]=$p['phone'];

}

$columns=array(
	'lastname'=>'Lastname',
	'firstname' => 'Firstname',
	'email'=>'Email',
	'username'=>'Username',
	'institution'=>'Institution',
	'phone'=>'Phone');

if ($is_admin) {
	$columns=array_merge(array('edit'=>''), $columns);
}


echo "<h3>Users Overview:</h3>";
if ($is_admin) {
	echo "<a class='header' href='adduser.php'>Add new user</a>"; 
}
echo " - currently ".count($users)." users";
$display_header=true;

echo data2table($users, $columns, $display_header);
/* footer comment */
admin_footer();
?>
