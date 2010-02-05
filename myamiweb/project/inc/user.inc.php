<?
class user {

	function user($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
	}

	function updateUser($userId, $username, $firstname, $lastname, $title, $institution, $dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, $url, $chpass, $mypass1, $mypass2, $priv="") {


		if ($chpass && $mypass1!=$mypass2)
			return false;

		if (!$this->checkUserExistsbyId($userId)) 
			return false;
		$db = DB_LEGINON;
		$table='UserData';
		$data=array();
		$data['firstname']=$firstname;
		$data['lastname']=$lastname;
		$data['email']=$email;
		$where['DEF_id']=$userId;
		$this->mysql->SQLUpdate($table, $data, $where, $db);
		
		$table="userdetails";
		$wherekey = 'REF|leginondata|UserData|user';
		$wherevalue = $userId;
		$q = 'select `DEF_id` as detailsId from '.$table.' where `'.$wherekey.'`='.$wherevalue;
		$re = $this->mysql->SQLQueries($q);
		$data=array();
		$data['title']=$title;
		$data['institution']=$institution;
		$data['dept']=$dept;
		$data['address']=$address;
		$data['city']=$city;
		$data['statecountry']=$statecountry;
		$data['zip']=$zip;
		$data['phone']=$phone;
		$data['fax']=$fax;
		$data['url']=$url;

		$where[$wherekey]=$wherevalue;
		if (1 ||empty($re)) {
			$data[$wherekey]=$wherevalue;
			$userId =  $this->mysql->SQLInsert($table, $data);
		} else {
			$this->mysql->SQLUpdate($table, $data, $where);
		}	
		$info = $this->getLoginInfo($userId);
		if (!$info) {
			#$this->addLogin($userId, $username, "", $priv);
		} else {
			$this->updatePrivilege($userId, $priv);
			$this->updateLogin($userId, $username);
		}

		if ($chpass) {
			$this->updatePassword($userId, $mypass2);
		}

	}

	function deleteUser($userId) {
		if (!$userId)
			return false;
		$q[]='delete from users where userId='.$userId;
		$q[]='delete from login where userId='.$userId;
		$this->mysql->SQLQueries($q);
	}

	function addUser($username, $firstname, $lastname, $title, $institution, $dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, $url, $mypass1, $mypass2, $priv="") {

		if ($mypass1!=$mypass2)
			return false;

		$data=array();
		$data['username']=$username;
		$data['firstname']=$firstname;
		$data['lastname']=$lastname;
		$data['title']=$title;
		$data['institution']=$institution;
		$data['dept']=$dept;
		$data['address']=$address;
		$data['city']=$city;
		$data['statecountry']=$statecountry;
		$data['zip']=$zip;
		$data['phone']=$phone;
		$data['fax']=$fax;
		$data['email']=$email;
		$data['url']=$url;

		$re=$this->checkUserExistsbyName($firstname, $lastname);

		if (1 ||empty($re)) {
			$userId =  $this->mysql->SQLInsert("users", $data);
			$this->addLogin($userId, $username, $mypass2, $priv);
			return $userId;
		} 
	}

	function checkUserExistsbyLogin($username) {
		$q='select `DEF_id` as userId from '.DB_LEGINON.'.UserData where username="'.$username.'"';
		$RuserInfo = $this->mysql->SQLQuery($q);
		$userInfo = mysql_fetch_array($RuserInfo);
		return $userInfo['userId'];
	}

	function checkUserExistsbyName($firstname, $lastname) {
		$q='select `DEF_id` as userId from '.DB_LEGINON.'UserData where `firstname`="'.$firstname.' and `lastname` = "'.$lastname.'"';
		$RuserInfo = $this->mysql->SQLQuery($q);
		$userInfo = mysql_fetch_array($RuserInfo);
		return $userInfo['userId'];
	}

	function checkUserExistsbyId($id) {
		$q='select `DEF_id` as userId from '.DB_LEGINON.'.UserData where `DEF_id`="'.$id.'"';
		$RuserInfo = $this->mysql->SQLQuery($q);
		$userInfo = mysql_fetch_array($RuserInfo);
		$id = $userInfo['userId'];
		if(empty($id))
			return false;
		else
			return $id;
	}

	function getUserId($firstname, $lastname){
		$q='select `DEF_id` as userId from '.DB_LEGINON.'UserData where `firstname`="'.$firstname.' and `lastname` = "'.$lastname.'"';
		return $this->mysql->getSQLResult($q);
	}

	function getUsers($order=false){
		$results = array();
		$order = ($order) ? "order by u.`lastname`" : "";
		$q='select u.`DEF_id` as userId, u.* '
			.'from '.DB_LEGINON.'.UserData u '
			.$order;

		$r = $this->mysql->getSQLResult($q);
		foreach ($r as $u) {
			$results[] = $this->appendUserDetails($u);
		}
		return $results;
	}

	function appendUserDetails($userInfo) {
		$q = 'select * from userdetails '
			.'where '
			.'`REF|leginondata|UserData|user` = '.$userInfo['userId'];
		list($dr) = $this->mysql->getSQLResult($q);
			if (!empty($dr)) 
				$userInfo = array_merge($dr,$userInfo);
		return $userInfo;
	}

	function getUserInfo($userId){
		$userId=trim($userId);
		$sqlwhere = (is_numeric($userId)) ? "u.`DEF_id`=$userId" : "u.name='$userId'";
		$q='select u.`DEF_id` as userId, u.*, u.`name` as username, '
			.'g.`DEF_id` as groupId ,g.`name` as groupname '
			.'from ' .DB_LEGINON.'.UserData u '
			.'left join '.DB_LEGINON.'.GroupData g on '
			.'u.`REF|GroupData|group` = g.`DEF_id` '
		  .'where '.$sqlwhere;
		list($r) = $this->mysql->getSQLResult($q);
		return $this -> appendUserDetails($r);
	}

	function getLoginInfo($userId) {
		$sqlwhere = (is_numeric($userId)) ? "u.`DEF_id`=$userId" : "u.name='$userId'";
		$q='select g.`DEF_id` as groupId, u.*, g.* from '
			.DB_LEGINON.'.UserData u left join '.DB_LEGINON.'.GroupData g '
			.'on u.`REF|GroupData|group` = g.`DEF_id` '
		  .'where '.$sqlwhere;
		return $this->mysql->getSQLResult($q);
	}

	function updateLogin($userId, $username) {
		$data['name']=$username;
		$where['DEF_id']=$userId;
		return $this->mysql->SQLUpdate(DB_LEGINON.'UserData', $data, $where);
	}

	function updatePassword($userId, $password) {
		$data['password']=$password;
		$where['DEF_id']=$userId;
		return $this->mysql->SQLUpdate(DB_LEGINON.'UserData', $data, $where);
	}

	function addLogin($userId, $username, $mypass, $priv=false) {
			if ($priv) {
				$q = 'select g.`DEF_id` groupId from '.DB_LEGINON.'.GroupData '
					.'where g.privilege = '.$priv;
				$r = $this->mysql->SQLQuery($q);
			}
			
			$data=array();
			$data['DEF_id']=$userId;
			$data['name']=$username;
			$data['password']=$mypass;
			if ($priv)
				$data['REF|GroupData|group']=$r[0]['groupId'];
			$id=$this->mysql->SQLInsert(DB_LEGINON.'UserData', $data);
			return $id;
	}

	function updatePrivilege($userId, $privilege) {
		$data['privilege']=$privilege;
		$where['userId']=$userId;
		return $this->mysql->SQLUpdate('login', $data, $where);
	}

	function getName($info) {
		$name=$info['username'];
		if(!$fname=trim($info['firstname']))
			$fname="";
		if (!$lname=trim($info['lastname']))
			$lname="";
		if ($lname || $fname) {
			$name=$lname." ".$fname;
		}
		return $name;
	}

}

?>
