#!/usr/bin/perl

use strict;

# Our modules we need
use Data::Dumper;
use MP3::Info;
use DBI;

# hashref for metadata
# we will leave him global so the metadata func
# doesnt have to have the global hashref passed
my $taghash;

sub _init{
    
    ########################################
    # Db info
    my $user     = "bossdj";
    my $password = "bossdj";
    
    my $database = "bossdj";
    my $driver   = "mysql";
    ########################################
    
    # put our database handle in our global
    my $dbh = DBI->connect("DBI:$driver:$database", $user, $password,
            { RaiseError => 1, AutoCommit => 0 });
    
    # Return a hashref of our globals
    return {
        'dbh'       => $dbh,
        'taghash'   => $taghash,
    };
}


# Function called to get the next filename to stream. 
# Should return a string.
sub ices_get_next {
    my $nextfile; 
    my $g       = _init();
    my $dbh     = $g->{dbh};

    # open the pid file so the calling program knows which stream it is    
    open (PROC, "/proc/$$/cmdline");
    my $stream = <PROC>;
    close (PROC);
    
    # parse out the stream name out of the call
    $stream =~ s/.*-m.\/(.*).-h.localhost.*/$1/;
    $g->{stream} =  "$stream";

    # get a track_id by random out of the stream
    my $rand_track = rand_track_id($g);

    # TODO add conditional if pulling from a queue
    #   if no queue then use rand
    
    # pulss the path for ices0 to know which file to play next
    $nextfile = get_track_path($g, $rand_track);
    
    # dump our id3 into our global hashref outside of $g
    $taghash = get_mp3tag($nextfile);

    # disconnect from db
    $dbh->disconnect;

    # return the pathname to ices0
    return $nextfile;
}

# If defined, the return value is used for title streaming (metadata)
sub ices_get_metadata {
        return "$taghash->{ARTIST} - $taghash->{TITLE} ($taghash->{ALBUM}, $taghash->{YEAR})";
}

# we are sending the db handle and the track_id to get
# a better way of getting the track_id is sought
# this sub should be fine when it is fixed though
sub get_track_path{
    my $g        = shift;
    my $track_id = shift;
    my $dbh      = $g->{dbh};
    my $data;
    
    my $track_query = qq[
        SELECT  t.path, t.play_count, st.play_count, t.track_id
        FROM    tracks t,
                bossdj.$g->{stream} st 
        WHERE   t.track_id = st.track_id
                AND t.track_id = ? 
    ];


    $data = $dbh->selectrow_arrayref($track_query, undef, ( $track_id) );

    track_global_stats_update($g, @$data[1], @$data[3]);
    track_stream_stats_update($g, @$data[2], @$data[3]);

    return @$data[0];  
    
}

# DEPRECATED!!!!
# this will grab the number of records in the tracks table
# not accurate, if a track is ever deleted, this will fail
sub track_count{
    my $g   = shift;
    my $dbh = $g->{dbh};
    my $data;
    
    my $count_query = qq[
        SELECT count(*) 
        FROM   bossdj.$g->{stream}
    ];

    $data = $dbh->selectrow_arrayref($count_query);
        return @$data[0];  
}

sub rand_track_id{
    my $g   = shift;
    my $dbh = $g->{dbh};
    my $data;
    
    my $rand_query = qq[
        SELECT s.track_id
        FROM   bossdj.$g->{stream} s
        ORDER BY rand()
        LIMIT 1
    ];

    $data = $dbh->selectrow_arrayref($rand_query);
        return @$data[0];  
}


sub track_global_stats_update{
    my $g           	= shift;
    my $dbh         	= $g->{dbh};
    my $g_track_count 	= shift;
    my $track_id    	= shift;
    
    my $update_query = qq[
        UPDATE  tracks t
        SET     t.play_count = ($g_track_count + 1), 
                t.date_last_played = NOW()
        WHERE   t.track_id = ?
    ];

    if($dbh->do($update_query, undef, $track_id)){
        print "Global Track Updated!\n";
    }else{
        print "$dbh->errstr";
    }

}

sub track_stream_stats_update{
    my $g           	= shift;
    my $dbh         	= $g->{dbh};
    my $st_track_count 	= shift;
    my $track_id    	= shift;
    
    my $update_query = qq[
        UPDATE  bossdj.$g->{stream} st
        SET     st.play_count = ($st_track_count + 1), 
                st.date_last_played = NOW()
        WHERE   st.track_id = ?
    ];

    if($dbh->do($update_query, undef, $track_id)){
        print "Stream Track Updated!\n";
    }else{
        print "$dbh->errstr";
    }

}

1;