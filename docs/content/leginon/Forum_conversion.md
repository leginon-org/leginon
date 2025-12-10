Notes on porting the Leginon BB to Redmine

1.  Add Forums
    1.  create new colum for bb forum id
    2.  insert the bb forums
2.  Add column to redmine message db for bb post id
3.  Import all posts to current forums (map forum id's), saving bb post id to new column
4.  enter messages parent ids
5.  edit posts to put into new forum
6.  delete unwanted forums

## Redmine DB Tables

[Messages]{.underline}

id board_id parent_id subject content author_id replies_count last_reply_id created_on updated_on locked sticky

[Boards]{.underline}

id project_id name description position topics_count messages_count last_message_id

[Users]{.underline}

id login hashed_password firstname lastname mail mail_notification admin status last_login_on language auth_source_id created_on updated_on type identity_url

## BB DB Tables

[Notre_forums]{.underline}

forum_id parent_id left_id right_id forum_parents forum_name forum_desc forum_desc_bitfield forum_desc_options forum_desc_uid forum_link forum_password forum_style forum_image forum_rules forum_rules_link forum_rules_bitfield forum_rules_options forum_rules_uid forum_topics_per_page forum_type forum_status forum_posts forum_topics forum_topics_real forum_last_post_id forum_last_poster_id forum_last_post_subject forum_last_post_time forum_last_poster_name forum_last_poster_colour forum_flags display_subforum_list display_on_index enable_indexing enable_icons enable_prune prune_next prune_days prune_viewed prune_freq

[Notre_posts]{.underline}

post_id topic_id forum_id poster_id icon_id poster_ip post_time post_approved post_reported enable_bbcode enable_smilies enable_magic_url enable_sig post_username post_subject post_text post_checksum post_attachment bbcode_bitfield bbcode_uid post_postcount post_edit_time post_edit_reason post_edit_user post_edit_count post_edit_locked

[Notre_topics]{.underline}

topic_id forum_id icon_id topic_attachment topic_approved topic_reported topic_title topic_poster topic_time topic_time_limit topic_views topic_replies topic_replies_real topic_status topic_type topic_first_post_id topic_first_poster_name topic_first_poster_colour topic_last_post_id topic_last_poster_id topic_last_poster_name topic_last_poster_colour topic_last_post_subject topic_last_post_time topic_last_view_time topic_moved_id topic_bumped topic_bumper poll_title poll_start poll_length poll_max_options poll_last_vote poll_vote_change

[Notre_users]{.underline}

user_id user_type group_id user_permissions user_perm_from user_ip user_regdate username username_clean user_password user_passchg user_pass_convert user_email user_email_hash user_birthday user_lastvisit user_lastmark user_lastpost_time user_lastpage user_last_confirm_key user_last_search user_warnings user_last_warning user_login_attempts user_inactive_reason user_inactive_time user_posts user_lang user_timezone user_dst user_dateformat user_style user_rank user_colour user_new_privmsg user_unread_privmsg user_last_privmsg user_message_rules user_full_folder user_emailtime user_topic_show_days user_topic_sortby_type user_topic_sortby_dir user_post_show_days user_post_sortby_type user_post_sortby_dir user_notify user_notify_pm user_notify_type user_allow_pm user_allow_viewonline user_allow_viewemail user_allow_massemail user_options user_avatar user_avatar_type user_avatar_width user_avatar_height user_sig user_sig_bbcode_uid user_sig_bbcode_bitfield user_from user_icq user_aim user_yim user_msnm user_jabber user_website user_occ user_interests user_actkey user_newpasswd user_form_salt

## Conversion tables

### Redmine Users

Search for the user to have an existing entry, if not their posts will be assigned to anonymous.

  Redmine Entry       BB Entry
  ------------------- --------------------------
  id                  
  login               notre_users->username
  hashed_password     
  firstname           
  lastname            
  mail                notre_users->user_email
  mail_notification   
  admin               
  status              
  last_login_on       
  language            notre_users->user_lang
  auth_source_id      
  created_on          
  updated_on          
  type                
  identity_url        

### Redmine Boards

We will create these from scratch - Development, Using Leginon, Using Appion, Tomography, Installation, Administration Tools

  Redmine Entry     BB Entry
  ----------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
  id                
  project_id        (the leginon id)
  name              notre_forums->forum_name
  description       notre_forums->forum_desc
  position          
  topics_count      notre_forums->forum_topics
  messages_count    notre_forums->forum_posts
  last_message_id   After all messages are ported add: notre_forums~~[forum_last_post_id]{style="text-align:right;"}~~>Redmine Messages~~[bb_post_id]{style="text-align:right;"}~~>id
  bb_forum_id       notre_forums->forum_id

### Redmine Messages

  Redmine Entry   BB Entry
  --------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  id              
  board_id        notre_posts~~[forum_id]{style="text-align:right;"}~~>Redmine Boards~~[bb_forum_id]{style="text-align:right;"}~~>id
  parent_id       Add these as second step after all posts moved over, notre_posts~~[topic_id]{style="text-align:right;"}~~>notre_topics~~[topic_first_post_id]{style="text-align:right;"}~~>Redmine Messages~~[bb_post_id]{style="text-align:right;"}~~>id
  subject         notre_posts->post_subject
  content         notre_posts->post_text (need to get BLOB)
  author_id       notre_posts~~[poster_id]{style="text-align:right;"}~~>notre_users~~[user_email]{style="text-align:right;"}~~>Users~~[mail]{style="text-align:right;"}~~>Users->id, if does not exist assign to anonymous
  replies_count   Set all to 0 then check Notre_topics~~[topic_first_post_id and update that message with notre_topics]{style="text-align:right;"}~~>topic_replies
  last_reply_id   Set all to NULL then check notre_topics~~[topic_first_post_id]{style="text-align:right;"}~~>Redmine Messages~~[bb_post_id]{style="text-align:right;"}~~>id and update that message with notre_topics~~[topic_last_post_id]{style="text-align:right;"}~~>Redmine Messages~~[bb_post_id]{style="text-align:right;"}~~>id
  created_on      notre_posts->post_time (may need a conversion)
  updated_on      notre_posts->post_edit_time (may need a conversion)
  locked          notre_posts->post_edit_locked
  sticky          0
  bb_post_id      notre_posts->post_id

## Commands

### Make backups

First backup the tables that we will be modifying:

> mysqldump -u amber -p ---skip-lock-tables ---extended-insert redmine boards > boards-preport.sql

> mysqldump -u amber -p ---skip-lock-tables ---extended-insert redmine messages > messages-preport.sql

### Add temporary columns to the boards and messages tables

    ALTER TABLE boards
    ADD bb_forum_id int(11);

    ALTER TABLE messages
    ADD bb_post_id int(11);

### Add forums

    INSERT INTO ami_redmine.boards (project_id, name, description, topics_count, messages_count, bb_forum_id)
    SELECT ami_redmine.projects.id, bb2.notre_forums.forum_name, bb2.notre_forums.forum_desc, bb2.notre_forums.forum_topics, bb2.notre_forums.forum_posts, bb2.notre_forums.forum_id
    FROM ami_redmine.projects, bb2.notre_forums
    WHERE ami_redmine.projects.identifier="leginon" 

Inserts 9 rows.

### Add Messages

    INSERT INTO ami_redmine.messages (board_id, subject, content,  locked, sticky, bb_post_id)
    SELECT ami_redmine.boards.id, bb2.notre_posts.post_subject, bb2.notre_posts.post_text, bb2.notre_posts.post_edit_locked, 0, bb2.notre_posts.post_id
    FROM bb2.notre_posts, ami_redmine.boards
    WHERE bb2.notre_posts.forum_id = ami_redmine.boards.bb_forum_id;   

inserted 603 rows.

### Add parent_id to messages

    UPDATE ami_redmine.messages AS redMess1, ami_redmine.messages AS redMess2, bb2.notre_topics, bb2.notre_posts
    SET redMess1.parent_id=redMess2.id
    WHERE redMess1.bb_post_id = bb2.notre_posts.post_id
    AND bb2.notre_posts.topic_id = bb2.notre_topics.topic_id
    AND bb2.notre_topics.topic_first_post_id = redMess2.bb_post_id
    AND redMess1.id != redMess2.id;

### Add author_id to messages

    UPDATE ami_redmine.messages, ami_redmine.users, bb2.notre_users, bb2.notre_posts
    SET ami_redmine.messages.author_id=redmine.users.id
    WHERE ami_redmine.messages.bb_post_id = bb2.notre_posts.post_id
    AND bb2.notre_posts.poster_id=bb2.notre_users.user_id
    AND bb2.notre_users.user_email = ami_redmine.users.mail;

For the messages from people who are not registered in redmine, set the author_id to 2 which is the anonymous user.

    UPDATE ami_redmine.messages
    SET ami_redmine.messages.author_id=2
    WHERE ami_redmine.messages.author_id IS NULL;

Updates 290 entries.

### Add replies_count to messages

    UPDATE ami_redmine.messages, bb2.notre_topics, bb2.notre_posts
    SET ami_redmine.messages.replies_count = bb2.notre_topics.topic_replies
    WHERE ami_redmine.messages.parent_id IS NULL
    AND ami_redmine.messages.bb_post_id = bb2.notre_posts.post_id
    AND bb2.notre_posts.topic_id = bb2.notre_topics.topic_id;

### Add last_reply_id to messages

    UPDATE ami_redmine.messages AS redMess1, ami_redmine.messages AS redMess2, bb2.notre_topics, bb2.notre_posts
    SET redMess1.last_reply_id = redMess2.id
    WHERE redMess1.parent_id IS NULL
    AND redMess1.bb_post_id = bb2.notre_posts.post_id
    AND bb2.notre_posts.topic_id = bb2.notre_topics.topic_id
    AND bb2.notre_topics.topic_last_post_id = redMess2.bb_post_id;

### Convert Unix timestamps to ISO 8601 and add to messages

http://dev.mysql.com/doc/refman/5.1/en/date-and-time-functions.html#function_from-unixtime
http://aruljohn.com/timestamp2date.html

    UPDATE ami_redmine.messages,  bb2.notre_posts
    SET ami_redmine.messages.created_on = FROM_UNIXTIME(bb2.notre_posts.post_time)
    WHERE ami_redmine.messages.bb_post_id = bb2.notre_posts.post_id;

    UPDATE ami_redmine.messages,  bb2.notre_posts
    SET ami_redmine.messages.updated_on = FROM_UNIXTIME(bb2.notre_posts.post_edit_time)
    WHERE ami_redmine.messages.bb_post_id = bb2.notre_posts.post_id
    AND bb2.notre_posts.post_edit_time != 0;

### Add last_reply_id to boards

    UPDATE ami_redmine.boards, ami_redmine.messages, bb2.notre_forums
    SET ami_redmine.boards.last_message_id = ami_redmine.messages.id
    WHERE ami_redmine.boards.bb_forum_id = bb2.notre_forums.forum_id
    AND bb2.notre_forums.forum_last_post_id = ami_redmine.messages.bb_post_id;

### Create a backup of the tables

> mysqldump -u amber -p ---skip-lock-tables ---extended-insert redmine boards > boards-postport.sql

> mysqldump -u amber -p ---skip-lock-tables ---extended-insert redmine messages > messages-postport.sql

### Remove the temporary columns

    ALTER TABLE boards
    DROP COLUMN bb_forum_id;

    ALTER TABLE messages
    DROP COLUMN bb_post_id;

### For testing content conversion

Get the original content:

    UPDATE ami_redmine.messages,  bb2.notre_posts
    SET ami_redmine.messages.content = bb2.notre_posts.post_text
    WHERE ami_redmine.messages.bb_post_id = bb2.notre_posts.post_id;
