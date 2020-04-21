the ices.pm was coded around ices0 v0.4 dont know if there is future compat issues or not, but the syscalls from some of the scripts were originally designed to be run on a fbsd system, with a little tweaking there should be no problem to get this to run on linux.  Also DO NOT run this code on an external facing system, it wasn't designed for it.  There is some unsafe sql in here that has potential to ruin your day should some wily person start poking around.  



#random sql musings
select t.track_num, t.track_title, al.album_title, ar.artist_title
FROM  tracks t,
      artist ar,
      album al,
      genre g
WHERE t.artist_id = ar.artist_id AND
      t.album_id = al.album_id AND
      t.genre_id = g.genre_id AND
      ar.`artist_title` = 'Faces'
ORDER BY al.`album_title`, t.track_num



# where my module had to be linked up
speedy# pwd
/usr/local/lib/perl5/5.8.7/BSDPAN/5.8.7
speedy# ls
ices.pm


# how to manually add tracks to a stream, the only way for now
 insert into mb (track_id) select t.track_id from tracks t, artist ar wher
e t.artist_id = ar.artist_id AND ar.artist_title like 'faces';


# how to startup a stream manually
       ices0  -B -D /tmp/all -S perl -M ices -m /all  -h localhost -p 8000  -P password -t http -s -n all
