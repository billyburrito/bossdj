#!/usr/bin/perl

use strict;

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
            
    my $cgi = new CGI;
    my $qs      = $cgi->Vars();    

    my $listen_url = "http://192.168.101.3:8000/INDEX.m3u";

    # Return a hashref of our globals
    return {
        'dbh'              => $dbh,
        'cgi'              => $cgi,
        'qs'               => $qs,
        'listen'          => $listen_url,
    };
}

sub main{
    my $g   = _init();
    my $C   = $g->{cgi};
    my $dbh = $g->{dbh};
    my $qs  = $g->{qs};

    my $master = master_recent($g);
    my $album_art;
    my $album_art_title;

    
    print   $C->header(),
            $C->start_html( -style => {'src'=>'/css/purensimple/default.css'},
                            -head  => [$C->meta({-http_equiv => 'pragma', -content => 'no-cache'}),
                               $C->meta({-http_equiv => 'Refresh', -content => "$g->{refresh};" . $C->self_url() })],
                            -title => "Boss DJ Playlist",
            );
    
#    print $C->h2({ class => 'left-box'}, "Master Playlist Data");

    my $master = master_recent($g);
    my $album_art;
    my $album_art_title;
    my $stream_title;
    
    if ($g->{image_path}){
        $album_art = $C->img( {src => $g->{image_path}, width => '250'} );
        $album_art_title = "Album Art";
    }

    if ($qs->{stream}){
        my $listen = $g->{listen};
        $listen =~ s/INDEX/$qs->{stream}/;
        $stream_title = $C->a({href => "$listen"}, "Playlist for $qs->{stream}");
    }
    else {
        $stream_title = "Master Playlist";
    }
    
        print   $C->start_table( { class => 'left-box', align => 'left', cellpadding => 5 } ),
                $C->Tr(
                    $C->td( {align => 'left'}, $C->h3($stream_title) ),
                    $C->td( {align => 'left'}, $C->h3($album_art_title) ),
                ),
                $C->Tr(
                    $C->td( {align => 'left', valign => 'top'}, $master),
                    $C->td( {align => 'left', valign => 'top'}, $album_art),
                ),
                $C->end_table();

    $dbh->disconnect();

}

sub master_recent{
    my $g   = shift;
    my $dbh = $g->{dbh};
    my $C   = $g->{cgi};
    my $qs  = $g->{qs};

    my $html_data;  #we are going to use this to buffer our html
    my $source = 'tracks'; 

    if ($qs->{stream}){
        $source = $qs->{stream};
    }

# table name reserved words cause this to fail
    my $master_query = qq[
        SELECT      t.track_id,
                    t.track_title,
                    al.album_title,
                    ar.artist_title,
                    s.play_count,
                    t.path,
                    s.date_last_played
        FROM        tracks t,
                    artist ar,
                    `$source` s,
                    album al
        WHERE       t.track_id = s.track_id AND
                    t.artist_id = ar.artist_id AND
                    t.album_id = al.album_id AND
                    s.play_count > 0
        ORDER BY    s.date_last_played DESC
        LIMIT 10
    ];

    my $lastten = $dbh->selectall_hashref($master_query, 'date_last_played');
    my $rows = scalar keys (%$lastten);

    $html_data .= $C->start_table( { align => 'left', cellpadding => 5 } );
    $html_data .= $C->Tr(
                $C->th( {align => 'left'}, "Title"),
                $C->th( {align => 'left'}, "Artist"),
                $C->th( {align => 'left'}, "Album"),
                $C->th( {align => 'left'}, "Play Count"),
                $C->th( {align => 'left'}, "Play Time"),
            );                    

    my $counter = 0; #  

    # if tracks have the same start time, the refresh will loop
    foreach my $key (sort keys (%$lastten)){
        $counter++;

        my $file_info = get_mp3info($lastten->{$key}->{path});
        my ($boldS, $boldE);
        
        if($counter > ($rows - 1) ){
            # set bold and italics for current track
            $boldS = '<B><I>';
            $boldE = '</I></B>';
            
            #also set album art if exists
            $g->{image_path} = $lastten->{$key}->{path};
            $g->{image_path} =~ s/(.*\/).*\.mp3/$1folder.jpg/;

            if( !(-e $g->{image_path} ) ){
                delete $g->{image_path};
            }
            
            #set our refresh time to be the length of current track
            $g->{refresh} = $file_info->{SECS}
        }
        
        $html_data .= $C->Tr( {color => '#FFFFFF'},
                    $C->td( "$boldS$lastten->{$key}->{track_title}$boldE"),
                    $C->td( "$boldS$lastten->{$key}->{artist_title}$boldE"),
                    $C->td( "$boldS$lastten->{$key}->{album_title}$boldE"),
                    $C->td( {align => 'center'}, "$boldS$lastten->{$key}->{play_count}$boldE"),
                    $C->td( {align => 'center'}, "$boldS$file_info->{TIME}$boldE"),
                );                    
    }
    $html_data .= $C->end_table();

    return $html_data;
    
}





