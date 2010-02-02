<?php
// --- access to share database --- //


class share {

	function share($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
	}

	function is_shared($sessionId) {
		$q = "select DEF_id as id from shareexperiments where `REF|projectexperiments|experiment`=$sessionId";
		$r = $this->mysql->getSQLResult($q);
		if (empty($r))
			return false;
		return true;
	}

	function get_share_info($experiments) {
		$q="select concate(u.`firstname`,' ',`lastname`) as name, u.username as username, s.`REF|projectexperiments|experiment` as experimentId "
			."from shareexperiments s "
			."left join ".DB_LEGINON.".UserData u on (u.`DEF_id`=s.`REF|leginondata|UserData|user`) "
			."where s.`REF|projectexperiments|experiment` in (".implode(',',$experiments).") "
			."order by u.username";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}
	
	function share_session_add($userId, $sessionId) {
		$q = "select DEF_id from shareexperiments where "
			."`REF|projectexperiments|experiment` ='".$sessionId."' and `REF|leginondata|UserData|user` ='".$userId."'";
		$r = $this->mysql->getSQLResult($q);
		if (empty($r)) {
			$q = 	"insert into shareexperiments (`REF|projectexperiments|experiment`, `REF|leginondata|UserData|user`) "
				."values ('$sessionId', '$userId')";
			$lastId = $this->mysql->SQLQuery($q, true);
		echo $this->mysql->getError();
		}
	}

	function share_session_del($users=array(), $sessionId) {
		foreach ($users as $userId_to_del) {
			$sql_del_users[] = "`REF|leginondata|UserData|user`='".$userId_to_del."'";
		}
		if ($sql_del_users) {
		$q = 	"delete from shareexperiments where "
			."`REF|projectexperiments|experiment`='".$sessionId."' and ( ".join(' OR ', $sql_del_users)." )";
		$this->mysql->SQLQuery($q);
		}
	}

	function add_experiments($usrId, $allexp) {

		$query = "select id from datalib_login where id = '$usrId'";
		$result = mysql_num_rows($query);

		if (is_array($allexp))
		foreach($allexp as $exp) {

			$q = "select experimentId from shareexperiments where experimentId='$exp' and  userId='$usrId' ";
			$result = mysql_num_rows($q);
			if ($result == 0) {
				$is_success_first = mysql_query("insert into shareexperiments (experimentId, userId) values ('$exp', '$usrId')");
			}
		}
		return 2;
	}
	
}
