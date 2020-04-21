#!/usr/bin/perl

use strict;

# TODO prepend "stream_" or s_ to user stream tables

# Our modules we need
use CGI::Pretty;
use Data::Dumper;
use MP3::Info;
use DBI;


main();

sub _init{
    
    # Db info
    my $user     = "bossdj";
    my $password = "bossdj";
    
    my $database = "bossdj";
    my $driver   = "mysql";
    
    # put our database handle in our global
    my $dbh = DBI->connect("DBI:$driver:$database", $user, $password,
            { RaiseError => 1, AutoCommit => 0 });
            
    my $cgi     = new CGI;
    my $qs      = $cgi->Vars();
    my $self    = $cgi->script_name();
    
    # Return a hashref of our globals
    return {
        'dbh'              => $dbh,
        'cgi'              => $cgi,
        'self'             => $self,
        'qs'               => $qs,
    };

}

sub main{
    my $g   = _init();
    my $dbh = $g->{dbh};
    my $qs  = $g->{qs};

    if ($qs->{cmd} eq 'add'){
        add_stream($g);
    }
    elsif ($qs->{cmd} eq 'mount') {
        mount_stream($g);
    }
    elsif ($qs->{cmd} eq 'edit') {
        edit_stream($g);
    }
    elsif ($qs->{cmd} eq 'delete') {
        delete_stream($g);
    }
    elsif ($qs->{cmd} eq 'kill') {
        kill_stream($g);
    }
    else {
        display_streams($g);
    }
              
    
    $dbh->disconnect();

}

sub display_streams{
    my $g   = shift;
    my $C   = $g->{cgi};
    my $dbh = $g->{dbh};
    my $qs  = $g->{qs};

    my $warn = {
            'delete.running'  => 'You are trying to delete a running stream',
        };

    print   $C->header(),
            $C->start_html( -style => {'src'=>'/css/purensimple/default.css'},
                            -head  => [$C->meta({-http_equiv => 'pragma', -content => 'no-cache'}), ],
                            -title => "Boss DJ Stream Admin",
            );
    
    print   $C->h1({class => 'left-box'}, "Stream Admin");
    
    if ($qs->{warn}){
        print $C->p("Warning: $warn->{$qs->{warn}}");
    }
    
    print   $C->start_table( { class => 'left-box', align => 'left', cellpadding => 5 } ),
                $C->Tr(
                    $C->th({colspan => '4'}, "Streams")
                );

    list_streams($g);
    
    print   $C->start_form( {-action => $C->script_name(), -method => 'GET'} ),
            $C->hidden({name => 'cmd', value => 'add', override => 1}),
            $C->Tr(
                $C->td({colspan => '3'}, $C->textfield( {name => 'new_stream', override => 1}, "" )),
                $C->td( $C->submit("Add Stream"))
                ),
            $C->end_form();
    
    print   $C->end_table(),
            $C->end_html();      
}


sub list_streams{
    my $g   = shift;
    my $C   = $g->{cgi};
    my $dbh = $g->{dbh};
    
    my $streams = get_streams_href($g); 
 
    foreach my $key ( sort keys (%$streams)){

        my ($control, $command);

        if ( ($streams->{$key}->{stream_pid} > 0) && (-d "/proc/$streams->{$key}->{stream_pid}") ){
            $control = "?cmd=kill&id=$streams->{$key}->{stream_id}";
            $command = "KILL";
        }
        else {
            $control = "?cmd=mount&id=$streams->{$key}->{stream_id}";
            $command = "MOUNT";
        }


        print $C->Tr(
                $C->td($C->a({href => "/bossdj/playlist.cgi?stream=$streams->{$key}->{stream_name}"}, "$streams->{$key}->{stream_name}")),
                $C->td($C->a({href => $C->url() . $control}, $command)),
                $C->td($C->a({href => $C->url() . "?cmd=edit&id=$streams->{$key}->{stream_id}"}, "EDIT")),
                $C->td($C->a({href => $C->url() . "?cmd=delete&id=$streams->{$key}->{stream_id}"}, "DELETE")),
        );
    }
    
}
    

sub add_stream{
    my $g   = shift;
    my $C   = $g->{cgi};
    my $dbh = $g->{dbh};
    my $qs  = $g->{qs};

    my $table_query = qq[
        CREATE TABLE `$qs->{new_stream}` (
          `s_id` int(10) unsigned NOT NULL auto_increment,
          `track_id` int(10) unsigned NOT NULL,
          `play_count` int(5) default NULL,
          `date_last_played` datetime default NULL,
          PRIMARY KEY  (`s_id`),
          UNIQUE KEY `s_id` (`s_id`)
        ) ENGINE=MyISAM DEFAULT CHARSET=latin1
    ];      

    $dbh->do($table_query);

    my $add_query = qq[
        INSERT INTO streams(stream_name)
        VALUES ( '$qs->{new_stream}' )
    ];

    $dbh->do($add_query);

    print $C->redirect($C->url());

}

sub delete_stream{
    my $g   = shift;
    my $C   = $g->{cgi};
    my $dbh = $g->{dbh};
    my $qs  = $g->{qs};
   
    my $pid = get_stream_pid($g, $qs->{id});
    if (!($pid)){
	$pid = "null";
    }  

    if (-d "/proc/$pid"){
        print $C->redirect($C->url() . "?warn=delete.running");
        exit;
    }

    my $name = get_stream_name($g, $qs->{id}) || die("Stream does not exist");

    my $delete_query = qq[
        DELETE 
        FROM streams 
        WHERE stream_id = '$qs->{id}' 
    ];

    $dbh->do($delete_query);

    my $drop_query = qq[
        DROP TABLE `$name` 
    ];      

    $dbh->do($drop_query);

    print $C->redirect($C->url());

}


sub mount_stream{
    my $g   = shift;
    my $C   = $g->{cgi};
    my $dbh = $g->{dbh};
    my $qs  = $g->{qs};
    
    my $name = get_stream_name($g, $qs->{id}) || die("Stream does not exist");

    my $return = `/usr/local/bin/ices0 -B -D /tmp -S perl -M ices -m /$name -h localhost -p  8000  -P midori -t http -s -n $name`;    
    $return =~ s/.*pid:.(.*)\)/$1/; 

    my $pid_query = qq[
        UPDATE  streams s
        SET     s.stream_pid = '$return'
        WHERE   s.stream_id = '$qs->{id}'
    ];

    $dbh->do($pid_query); 

    print $C->redirect($C->url());

}


sub kill_stream{
    my $g   = shift;
    my $C   = $g->{cgi};
    my $dbh = $g->{dbh};
    my $qs  = $g->{qs};

    my $pid = get_stream_pid($g, $qs->{id}) || die("Cant get pid for stream");
    
    kill 9, $pid;

    clear_stream_pid($g, $qs->{id}) || warn("no rows were changed");

    print $C->redirect($C->url());

}

sub edit_stream{
    my $g   = shift;
    my $C   = $g->{cgi};
    my $qs  = $g->{qs};

    my $name = get_stream_name($g, $qs->{id}) || die("Stream does not exist");

    print   $C->header(),
            $C->start_html( -style=>{'src'=>'/css/purensimple/default.css'},
                      -head =>[$C->meta({-http_equiv => 'pragma', -content => 'no-cache'}),
                              ],
            );
    
    print   $C->h1("Editing Stream: $name");    

    # emulate the itunes interface to a point here

    foreach my $set ( qw(genre artist album)) {
        my $href = get_data_index_href($g, $set); 

        my $fid = $set."_id";

        my ($values, $labels) = get_value_pair_data($href, $fid);

        print $C->scrolling_list(   -name     => $set,
                                    -size     => '10',
                                    -values   => $values,
                                    -labels   => $labels,
                                    -multiple => 1,
                                );
    }
#    # get genre list
#    my $genre_href = get_data_index_href($g, "genre"); 
#
#    my ($values, $labels) = get_value_pair_data($genre_href, "genre_id");
#
#    print $C->scrolling_list(   -name     => 'genre',
#                                -size     => '10',
#                                -values   => $values,
#                                -labels   => $labels,
#                                -multiple => 1,
#                            );


#print Dumper @genre_values;
#print Dumper $genre_labels;
}

sub get_stream_name {
    my $g         = shift;
    my $stream_id = shift;
    my $dbh       = $g->{dbh};
    
    my $name_query = qq[
        SELECT s.stream_name
        FROM streams s
        WHERE s.stream_id = ?
    ];
    
    my $data = $dbh->selectrow_arrayref($name_query, undef, $stream_id);

    return @$data[0];   
}

sub get_stream_pid {
    my $g         = shift;
    my $stream_id = shift;
    my $dbh       = $g->{dbh};
    
    my $pid_query = qq[
        SELECT s.stream_pid
        FROM streams s
        WHERE s.stream_id = ?
    ];
    
    my $data = $dbh->selectrow_arrayref($pid_query, undef, $stream_id);

    return @$data[0];   
}

sub clear_stream_pid {
    my $g         = shift;
    my $stream_id = shift;
    my $dbh       = $g->{dbh};
    
    my $empty_pid_query = qq[
        UPDATE  streams s
        SET     s.stream_pid = NULL
        WHERE   s.stream_id = ? 
    ];

    return $dbh->do($empty_pid_query, undef, $stream_id); 
}

sub get_streams_href {
    my $g         = shift;
    my $dbh       = $g->{dbh};
    
    my $stream_query = qq[
        SELECT      s.stream_id,
                    s.stream_name,
                    s.stream_pid
        FROM        streams s
    ];
    
    return $dbh->selectall_hashref($stream_query, 'stream_name');    
}

sub get_data_index_href {
    my $g         = shift;
    my $table     = shift;
    my $dbh       = $g->{dbh};
   

    my $id    = "g."."$table"."_id";
    my $title = "g."."$table"."_title";
    my $key   = "$table"."_title";

    my $query = qq[
        SELECT      $id,
                    $title
        FROM        $table g
    ];
    
    return $dbh->selectall_hashref($query, $key);    
}

sub get_genres_href {
    my $g         = shift;
    my $dbh       = $g->{dbh};
    
    my $genre_query = qq[
        SELECT      g.genre_id,
                    g.genre_title
        FROM        genre g
    ];
    
    return $dbh->selectall_hashref($genre_query, 'genre_title');    
}

sub get_artists_href {
    my $g         = shift;
    my $dbh       = $g->{dbh};
    
    my $artist_query = qq[
        SELECT      ar.artist_id,
                    ar.artist_title
        FROM        artist ar
    ];
    
    return $dbh->selectall_hashref($artist_query, 'artist_id');    
}

sub get_albums_href {
    my $g         = shift;
    my $dbh       = $g->{dbh};
    
    my $album_query = qq[
        SELECT      al.album_id,
                    al.album_title
        FROM        album al
    ];
    
    return $dbh->selectall_hashref($album_query, 'album_id');    
}

sub get_value_pair_data {
    # takes an href and the field name of the index you want it created on
    my $href        = shift;
    my $index_field = shift;

    my $values;
    my $labels;

    foreach my $key (sort (keys %$href) ) {
        $labels->{ $href->{$key}->{$index_field} } = $key;
        push(@$values, $href->{$key}->{$index_field});
    }

    return ($values, $labels);
}
