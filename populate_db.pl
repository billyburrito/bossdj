#!/usr/bin/perl

use strict;

use Data::Dumper;
use MP3::Info;
use DBI;


#####################################################
#
#   TODO:
#       - reinit the db (0 out tables)
#       - have the script create the db
#       - command line options
#       - add path as a command line option

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
    
    # Return a hashref of our globals
    return {
        'dbh'              => $dbh,
    };

}

sub main{

    my $g   = _init();
    my $dbh = $g->{dbh};

    #have to double escape our find command
    my @filelist = `/usr/bin/find /music/albums/ | grep -i \\\\.mp3`;
    
    foreach my $file(@filelist){
        chomp $file;

        #check if file exists
        if( file_exists($g, $file) ){
            print "File skipped: $file\n";
        }else{

            my $taghash = get_mp3tag($file);
            
            if( !($taghash->{ALBUM})){ 
                $taghash->{ALBUM} = "no album";
            }
            if( !($taghash->{GENRE})){ 
                $taghash->{GENRE} = "no genre";
            }
    
            # call subs to get these ids for track table
            my $artist_id = check_artist($g, $taghash->{ARTIST});
            my $album_id = check_album($g, $taghash->{ALBUM}, $taghash->{YEAR} );
            my $genre_id = check_genre($g, $taghash->{GENRE});
    
            if($artist_id && $album_id && $genre_id){
                my $insert_query = qq[
                    INSERT INTO tracks (path,       artist_id,
                                        album_id,   genre_id, 
                                        track_num,  track_title,
                                        date_added)
                    VALUES ( ?, ?,
                             ?, ?,
                             ?, ?,
                             NOW())
                ];
    
                my @bindvars = ($file,              $artist_id,
                                $album_id,          $genre_id,
                                $taghash->{TRACKNUM},  $taghash->{TITLE},
                                );
    
                if($dbh->do($insert_query, undef, @bindvars)){
                    print "File added: $file\n";
                }else{
                    print "$dbh->errstr";
                }
    
    
            }else{
                print STDERR "$file doesnt have artist, album or genre\n";
            }
        }       # END if( !(track_exists) )
    }
    $dbh->disconnect;
}

sub file_exists{
    my $g           = shift;
    my $file        = shift;
    my $dbh         = $g->{dbh};
    my $data;
    
    my $check_query = qq[
        SELECT count(*) 
        FROM tracks t 
        WHERE t.path = ?
    ];
    
    $data = $dbh->selectrow_arrayref($check_query, undef, $file);  
    return @$data[0];
}
    
sub check_artist{
    my $g            = shift;
    my $artist_title = shift;
    my $dbh          = $g->{dbh};
    my $data;

    my $check_query = qq[
        SELECT  ar.artist_id
        FROM    artist ar
        WHERE   ar.artist_title = ?
    ];
        
    my $insert_query = qq[
        INSERT INTO artist(artist_title)
        VALUES (?)
    ];

    if($data = $dbh->selectrow_arrayref($check_query, undef, $artist_title)){
        return @$data[0];   
    } else {
        $dbh->do($insert_query, undef, $artist_title);
        return $dbh->last_insert_id(undef, undef, "artist", "artist_id");
    }
}

sub check_album{
    my $g            = shift;
    my $album_title  = shift;
    my $album_year   = shift;
    my $dbh          = $g->{dbh};
    my $data;

    my $check_query = qq[
        SELECT  al.album_id
        FROM    album al
        WHERE   al.album_title = ?
    ];
        
    my $insert_query = qq[
        INSERT INTO album(album_title, album_year)
        VALUES (?, ?)
    ];

    if($data = $dbh->selectrow_arrayref($check_query, undef, $album_title)){
        return @$data[0];   
    } else {
        $dbh->do($insert_query, undef, ($album_title, $album_year));
        return $dbh->last_insert_id(undef, undef, "album", "album_id");
    }
}

sub check_genre{
    my $g            = shift;
    my $genre_title  = shift;
    my $dbh          = $g->{dbh};
    my $data;

    my $check_query = qq[
        SELECT  g.genre_id
        FROM    genre g
        WHERE   g.genre_title = ?
    ];
        
    my $insert_query = qq[
        INSERT INTO genre(genre_title)
        VALUES (?)
    ];

    if($data = $dbh->selectrow_arrayref($check_query, undef, $genre_title)){
        return @$data[0];   
    } else {
        $dbh->do($insert_query, undef, $genre_title);
        return $dbh->last_insert_id(undef, undef, "genre", "genre_id");
    }
}

