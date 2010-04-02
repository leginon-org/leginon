<?
class user {

	function user($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
	}

	function updateUser($userId, $username, $firstname, $lastname, $title, $institution, $dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, $url, $groupId, $chpass, $mypass1, $mypass2) {
		if ($chpass && $mypass1!=$mypass2)
			return false;

		if (!$this->checkUserExistsbyId($userId)) 
			return false;
		$db = DB_LEGINON;
		$table='UserData';
		$data=array();
		$where=array();
		$data['firstname']=$firstname;
		$data['lastname']=$lastname;
		$data['email']=$email;
		$data['REF|GroupData|group']=$groupId;
		$data = $this->addTempUserData($data,$username,$firstname,$lastname);
		$where['DEF_id']=$userId;
		$this->mysql->SQLUpdate($table, $data, $where,$db);
		//Details	
		$db = DB_PROJECT;
		$table="userdetails";
		$wherekey = 'REF|leginondata|UserData|user';
		$wherevalue = $userId;
		$q = 'select `DEF_id` as detailsId from '.$db.'.'.$table.' where `'.$wherekey.'`='.$wherevalue;
		$re = $this->mysql->SQLQueries($q);
		$data=array();
		$where=array();
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
		if (empty($re)) {
			$data[$wherekey]=$wherevalue;
			$userdetailsId =  $this->mysql->SQLInsert($table, $data,$db);
		} else {
			$this->mysql->SQLUpdate($table, $data, $where,$db);
		}	

		if ($chpass) {
			$this->updatePassword($userId, $mypass2);
		}

	}

	function deleteUser($userId) {
		if (!$userId)
			return false;
		
		$q[]='delete from '.DB_LEGINON.'.UserData where `DEF_Id`='.$userId;
		$q[]='delete from '.DB_PROJECT.'.userdetails where `REF|leginondata|UserData|user`='.$userId;
		$q[]='delete from '.DB_PROJECT.'.projectowners where `REF|leginondata|UserData|user`='.$userId;
		$this->mysql->SQLQueries($q);
	}

	function addUser($username, $firstname, $lastname, $title, $institution, $dept, $address, $city, $statecountry, $zip, $phone, $fax, $email, $url, $groupId, $mypass1, $mypass2) {

		if ($mypass1!=$mypass2)
			return false;

		$db=DB_LEGINON;
		$table='UserData';
		$data=array();
		$data['username']=$username;
		$data['firstname']=$firstname;
		$data['lastname']=$lastname;
		$data['email']=$email;
		$data['REF|GroupData|group']=$groupId;
		$data['password']=$mypass2;
		$data = $this->addTempUserData($data,$username,$firstname,$lastname);
		//Check existance
		$re=($this->checkUserExistsbyName($firstname, $lastname) || $this->checkUserExistsbyLogin($username));
		if (1 ||empty($re)) {
			$userId =  $this->mysql->SQLInsert($table, $data,$db);
		} 
		//Details	
		$db=DB_PROJECT;
		$table="userdetails";
		$wherekey = 'REF|leginondata|UserData|user';
		$wherevalue = $userId;
		$data1=array();
		$data1['REF|leginondata|UserData|user']=$userId;
		$data1['title']=$title;
		$data1['institution']=$institution;
		$data1['dept']=$dept;
		$data1['address']=$address;
		$data1['city']=$city;
		$data1['statecountry']=$statecountry;
		$data1['zip']=$zip;
		$data1['phone']=$phone;
		$data1['fax']=$fax;
		$data1['url']=$url;
		$userdetailsId =  $this->mysql->SQLInsert($table, $data1,$db);
		if ($userdetailsId) return $userId;
	}

	function addTempUserData($data,$username,$firstname,$lastname) {
		$data['name'] = $username;
		$data['full name'] = $firstname.' '.$lastname;
		return $data;
	}

	function checkUserExistsbyLogin($username) {
		$q='select `DEF_id` as userId from '.DB_LEGINON.'.UserData where username="'.$username.'"';
		$RuserInfo = $this->mysql->SQLQuery($q);
		$userInfo = mysql_fetch_array($RuserInfo);
		return $userInfo['userId'];
	}

	function checkUserExistsbyName($firstname, $lastname) {
		$q='select `DEF_id` as userId from '.DB_LEGINON.'.UserData where `firstname`="'.$firstname.'" and `lastname` = "'.$lastname.'"';
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
		$q='select `DEF_id` as userId from '.DB_LEGINON.'.UserData where `firstname`="'.$firstname.' and `lastname` = "'.$lastname.'"';
		return $this->mysql->getSQLResult($q);
	}

	function getUsers($orderBy=false){
		$results = array();
		$order = ($orderBy != false) ? "order by `$orderBy`" : "";

		$q='select u.`DEF_id` as userId, u.*, ud.* '
			.'from '.DB_LEGINON.'.UserData u '
			.'left join '.DB_PROJECT.'.userdetails ud on '
			.'u.DEF_id = ud.`REF|leginondata|UserData|user` '
			.$order;

		$r = $this->mysql->getSQLResult($q);
		return $r;
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
		$sqlwhere = (is_numeric($userId)) ? "u.`DEF_id`=$userId" : "u.username='$userId'";
		$q='select u.`DEF_id` as userId, u.*, u.`username` as username, '
			.'g.`DEF_id` as groupId ,g.`name` as groupname '
			.'from ' .DB_LEGINON.'.UserData u '
			.'left join '.DB_LEGINON.'.GroupData g on '
			.'u.`REF|GroupData|group` = g.`DEF_id` '
		  .'where '.$sqlwhere;
		list($r) = $this->mysql->getSQLResult($q);
		return $this -> appendUserDetails($r);
	}

	function updatePassword($userId, $password) {
		$data['password']=$password;
		$where['DEF_id']=$userId;
		return $this->mysql->SQLUpdate('UserData', $data, $where,DB_LEGINON);
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
	
	function getUserIdByUsername($username){
		$q='select `DEF_id` as userId from '.DB_LEGINON.'.UserData 
				where `username`="'.$username. '"';
		
		$result = $this->mysql->getSQLResult($q);
		return $result[0]['userId'];
	}

}

?>
