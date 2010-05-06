<?php
class ViewerPreference{

	function ViewerPreference() {
		$this->mysql = &new mysql(DB_HOST, DB_USER, DB_PASS, DB);
	}

	function add_comment_setting($username, $name) {
		$q = "SELECT * from `viewer_pref_comment` "
		."WHERE name='$name' AND username='$username'";
		list($r) = $this->mysql->getSQLResult($q);
		if ($r['name']!=$name) {
			$q = "INSERT INTO `viewer_pref_comment` "
			." (username, name) VALUE ('$username', '$name') ";
			$this->mysql->SQLQuery($q);
		}
	}

	function get_comment_setting($username) {
		$q = "SELECT * from `viewer_pref_comment` "
		."WHERE username='$username' ";
		return $this->mysql->getSQLResult($q);
	}

	function get_comment_info($id) {
		$q = "SELECT * from `viewer_pref_comment` "
		."WHERE id='$id' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}
		

	function add_category($commentId, $name) {
		$q = "SELECT * from `viewer_pref_category` "
		."WHERE name='$name' AND commentId='$commentId'";
		list($r) = $this->mysql->getSQLResult($q);
		if ($r['name']!=$name) {
			$q = "INSERT INTO `viewer_pref_category` "
			." (commentId, name) VALUE ('$commentId', '$name') ";
			$this->mysql->SQLQuery($q);
		}
	}
	
	function get_category($commentId) {
		$q = "SELECT * from `viewer_pref_category` "
		."WHERE commentId='$commentId' "
		."ORDER by id ASC";
		return $this->mysql->getSQLResult($q);
	}
	
	function get_categoryId($name, $commentId) {
		$q = "Select id from `viewer_pref_category` "
		."WHERE commentId='$commentId' AND name='$name'";
		list($r)=$this->mysql->getSQLResult($q);
		return $r['id'];
	}

	function del_category($id) {
		$q = "DELETE from `viewer_pref_category` "
		."WHERE id='$id' ";
		return $this->mysql->SQLQuery($q);
	}

	function del_comment_setting($id) {
		$q[] = "DELETE from `viewer_pref_comment` "
		."WHERE id='$id' ";
		$q[] = "DELETE from `viewer_pref_category` "
		."WHERE commentId='$id' ";
		return $this->mysql->SQLQueries($q);
	}

	function get_comment_sessions($username, $commentId) {
		$q = "SELECT * from `viewer_pref_session` "
		."WHERE commentId='$commentId' AND username='$username' ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function get_comment_session($username, $sessionId) {
		$q = "SELECT * from `viewer_pref_session` "
		."WHERE username='$username' "
		."AND sessionId ='$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function add_comment_session($username, $commentId, $sessionId) {
		$q = "SELECT * from `viewer_pref_session` "
		."WHERE commentId='$commentId' AND username='$username' "
		."AND sessionId ='$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		if (!$r['id']) {
			$q = "INSERT INTO `viewer_pref_session` "
			."(username, commentId, sessionId) VALUE ('$username', '$commentId', '$sessionId') ";
			$this->mysql->SQLQuery($q);
		}
	}

	function del_comment_session($id) {
		$q[] = "DELETE from `viewer_pref_session` "
		."WHERE id='$id' ";
		return $this->mysql->SQLQueries($q);
	}

	function update_pref($username, $viewcomment, $viewmyexp, $viewstat) {
		$r = $this->get_pref($username);
		$table = "viewer_pref";
		$data['viewcomment'] = ($viewcomment=='Y') ? 'Y' : 'N';
		$data['viewmyexp'] = ($viewmyexp=='Y') ? 'Y' : 'N';
		$data['viewstat'] = ($viewstat=='Y') ? 'Y' : 'N';

		if ($r['id']) {
			$where['id']=$r['id'];
			return $this->mysql->SQLUpdate($table, $data, $where);
		} else {
			$data['username'] = $username;
			return $this->mysql->SQLInsert($table, $data);
		}
	}

	function get_pref($username) {
		$q = "SELECT * from `viewer_pref` "
		."WHERE username='$username'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function del_pref($username) {
		$q[] = "DELETE from `viewer_pref` "
		."WHERE id='$username' ";
		return $this->mysql->SQLQueries($q);
	}

}
?>
