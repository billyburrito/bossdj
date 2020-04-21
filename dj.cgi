#!/usr/bin/perl

use strict;

# Our modules we need
use CGI::Pretty;
use Data::Dumper;
use MP3::Info;
use DBI;


main();

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
    
    # Return a hashref of our globals
    return {
        'dbh'              => $dbh,
        'cgi'              => $cgi,
    };

}

sub main{
    my $g   = _init();
    my $C   = $g->{cgi};
    my $dbh = $g->{dbh};

    
    print   $C->header(),
            $C->start_html( -style=>{'src'=>'/css/purensimple/default.css'},
                      -head =>[$C->meta({-http_equiv => 'pragma', -content => 'no-cache'}),
                              ],
            );
    
    $dbh->disconnect();

}




