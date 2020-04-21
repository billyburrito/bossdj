CREATE TABLE `tracks` (
  `track_id` int(10) unsigned NOT NULL auto_increment,
  `path` varchar(400) NOT NULL,
  `artist_id` int(10) NOT NULL,
  `album_id` int(10) default NULL,
  `genre_id` int(10) default NULL,
  `track_num` int(4) default NULL,
  `track_title` varchar(200) NOT NULL,
  `play_count` int(5) default NULL,
  `date_last_played` datetime default NULL,
  `date_added` datetime NOT NULL,
  PRIMARY KEY  (`track_id`),
  UNIQUE KEY `track_id` (`track_id`),
  UNIQUE KEY `path` (`path`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;


CREATE TABLE `artist` (
  `artist_id` int(10) unsigned NOT NULL auto_increment,
  `artist_title` varchar(100) NOT NULL,
  PRIMARY KEY  (`artist_id`),
  UNIQUE KEY `artist_id` (`artist_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;


CREATE TABLE `album` (
  `album_id` int(10) unsigned NOT NULL auto_increment,
  `album_title` varchar(100) default NULL,
  `album_year` int(4) default NULL,
  PRIMARY KEY  (`album_id`),
  UNIQUE KEY `album_id` (`album_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

CREATE TABLE `genre` (
  `genre_id` int(10) unsigned NOT NULL auto_increment,
  `genre_title` varchar(50) NOT NULL,
  PRIMARY KEY  (`genre_id`),
  UNIQUE KEY `genre_id` (`genre_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

