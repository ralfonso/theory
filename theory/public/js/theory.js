function debug(v) {
	$('#debug:visible').html('<br />' + v);
	setTimeout("$('#debug:visible').html('')",6000);
}

function getStatus() {
    // this function is a mess

    if (window.sliding == true)
        return;

	window.statusloads++;
    
    // if this is enabled in the config, stop refreshing the main page after twenty minutes of not seeing the mouse cursor
	if (window.statusloads > 160)
		return;

    if (!(window.frames['frmplaylist']))
        return;

	debug('loading status (' + window.statusloads + ')');

    // load the status data from the server
    $.getJSON('/mpdcontrol/status',
        function(data) {
            // change the icon displayed on the controls
            if (data.status.state == 'play') {
                $('#imgPlay').attr('src','../img/pause.png');
            }
            else if (data.status.state == 'stop' || data.status.state == 'pause') {
                $('#imgPlay').attr('src','../img/play.png');
            }




            // check to see if the playlist was updated
            if ($('#playlistid').val() != data.status.playlist) {
                // don't refresh the playlist if the user just removed a track. wait until next time. 
                if (window.trackremoved) {
                    window.trackremoved = false;
                }
                else {
                    $('#frmplaylist').attr('src','/playlist')
                }
                
                $('#playlistid').val(data.status.playlist);
            }

            if (data.status.time) {
                var time = data.status.time.split(':');
                var currentseconds = time[0];
                var totalseconds = time[1];
            }
            else if (data.track && data.track.time) {
                var currentseconds = 0;
                var totalseconds = data.track.time;
            }
            else {
                var currentseconds = 0;
                var totalseconds = 0;
            }

            window.ignorepositionslide = true;
            $('#position-slider').slider('moveTo',currentseconds);

            // did someone change the volume?! 
            if ($('#vol').html() != data.status.volume) {
                window.ignorevolumeslide = true;
                $('#volume-slider').slider('moveTo',data.status.volume);
            }

            $('#vol').html(data.status.volume);
            $('#vol').show();

            (data.status.repeat == 1) ? $('#repeat').addClass('enabled') : $('#repeat').removeClass('enabled');
            (data.status.random  == 1) ? $('#random').addClass('enabled') : $('#random').removeClass('enabled');

            // destroy / recreate the position slider.  This is ugly, but jquery-ui doesn't seem to provide an 
            // easy way to alter an existing slider



            var currenttime = formatTime(currentseconds);
            var totaltime = formatTime(totalseconds);
            
            $('#time').html(currenttime + ' / ' + totaltime);
            $('#time').show();

            if ((data.track.title != $('#currenttitle').val() || $('#title').html() == 'not playing')) {
                // track updated

                if (data.status.state == 'play') {
                    $('#position-slider').slider("destroy");
                    $('#position-slider').slider(
                        {
                            'min'       : 0,
                            'max'       : totalseconds,
                            'startValue': currentseconds,
                            'start':    function() {
                                            window.sliding = true;   
                                        },
                            'change'    : function(e,ui) {
                                            seek($('#currentid').val(),ui.value);
                                            window.sliding = false;
                                          }
                        }
                    );
                }
                else {
                    $('#position-slider').slider("destroy");
                }

                $('#currentartist').val(data.track.artist)
                $('#currenttitle').val(data.track.title);

                if (data.track.artist && data.track.title)
                    var title = data.track.artist + ' - ' + data.track.title
                else if (data.track.name && data.track.title)
                    var title = data.track.name + ' - ' + data.track.title
                else if (data.track.file)
                    var title = data.track.file

                $('#title').html(title);
                $('#aWiki').attr('href','http://www.google.com/search?btnI=I\'m+Feeling+Lucky&q=site:en.wikipedia.org%20' + data.track.artist);
                $('#wiki').show();
                var arturl = '/fetchart?artist=' + data.track.artist + '&album=' + data.track.album
                $('#currentartlink').attr('href',arturl)
                $('#currentart').attr('src',arturl)
                $('#currentartlink').lightBox();

				if (data.track.artist && data.track.title)
					$(document).attr('title','theory :: ' + data.track.artist + ' - ' + data.track.title)
				else if ($('#title').html() == 'not playing')
					$(document).attr('title','theory :: not playing');

				if ($('#lyrics:visible').length)
					loadLyrics();
            }
            else if (!data.track.title) {
                $('#currentartist').val('');
                $('#currenttitle').val('');
                $('#currentid').val('');
                $('#title').html('not playing');
                $('#wiki').hide();
            }   

            if ($('#currentid').val() != data.track.id || $('#playlist li.selectedtrack',window.frames['frmplaylist'].document).length == 0) {
                $('#currentid').val(data.track.id);

                // this/ doesn't work on the initial page load because the frame isn't ready
                setPlaylistColors(window.frames['frmplaylist'].document,true);
                $('#playlist li[id^=track_' + data.track.id + ']',window.frames['frmplaylist'].document).addClass('selectedtrack');
            }

            $('#currentid').val(data.track.id)
        }
    );
}

/* getPageSize() by quirksmode.com
 *
 * @return Array Return an array with page width, height and window width, height
 */
function getPageSize() {
    var xScroll, yScroll;
    if (window.parent.innerHeight && window.parent.scrollMaxY) {	
        xScroll = window.parent.innerWidth + window.parent.scrollMaxX;
        yScroll = window.parent.innerHeight + window.parent.scrollMaxY;
    } else if (document.body.scrollHeight > document.body.offsetHeight){ // all but Explorer Mac
        xScroll = document.body.scrollWidth;
        yScroll = document.body.scrollHeight;
    } else { // Explorer Mac...would also work in Explorer 6 Strict, Mozilla and Safari
        xScroll = document.body.offsetWidth;
        yScroll = document.body.offsetHeight;
    }
    var windowWidth, windowHeight;
    if (self.innerHeight) {	// all except Explorer
        if(document.documentElement.clientWidth){
            windowWidth = window.parent.document.documentElement.clientWidth; 
        } else {
            windowWidth = self.innerWidth;
        }
        windowHeight = self.innerHeight;
    } else if (document.documentElement && document.documentElement.clientHeight) { // Explorer 6 Strict Mode
        windowWidth = document.documentElement.clientWidth;
        windowHeight = document.documentElement.clientHeight;
    } else if (document.body) { // other Explorers
        windowWidth = document.body.clientWidth;
        windowHeight = document.body.clientHeight;
    }	
    // for small pages with total height less then height of the viewport
    if(yScroll < windowHeight){
        pageHeight = windowHeight;
    } else { 
        pageHeight = yScroll;
    }
    // for small pages with total width less then width of the viewport
    if(xScroll < windowWidth){	
        pageWidth = xScroll;		
    } else {
        pageWidth = windowWidth;
    }
    arrayPageSize = new Array(pageWidth,pageHeight,windowWidth,windowHeight);
    return arrayPageSize;
 }

function jump(v) {
    window.frames['frmartists'].location.hash = 'jump' + v;
}

function setVolume(val) {
    // check to see if the slider was simply updated by status() if so, don't update MPD

    if (!window.ignorevolumeslide)
        $.get('/mpdcontrol/setvolume/' + val);

    window.ignorevolumeslide = false;
}

function seek(id,pos) {
    // check to see if the slider was simply updated by status() if so, don't update MPD

    if (!window.ignorepositionslide)
        $.get('/mpdcontrol/seek/' + id + '/' + pos);
    window.ignorepositionslide = false;
}   

function formatTime(seconds)
{
	var minutes = Math.floor(seconds / 60);
	var seconds = seconds - (minutes * 60);
	var retval = '';
	if (minutes >= 60) {
			hours = Math.floor(minutes / 60);   
			minutes = minutes % 60;
			retval = hours + ":";
	}

	if (minutes < 10) {
			retval = retval + "0" + minutes + ":";
	}
	else {
			retval = retval + minutes + ":";
	}
	if (seconds < 10) {
			retval = retval + "0" + seconds;
	}
	else {
			retval = retval + seconds;
	}

	return retval;
}

function cmd(v) {
    $.get('/mpdcontrol/' + v);
	getStatus();
}

function artistAlbums(artist,album) {
    if (!album)
        album = '';

    window.parent.$('#frmalbums').attr('src','/albums?artist=' + encodeURIComponent(artist) + '&album=' + encodeURIComponent(album))
    window.parent.$('#frmtracks').attr('src','/tracks?artist=' + encodeURIComponent(artist) + '&album=' + encodeURIComponent(album))

	
	$('#list li:odd a',window.parent.frames['frmartists'].document).removeClass('activerow').addClass('oddrow');
	$('#list li:even a',window.parent.frames['frmartists'].document).removeClass('activerow').addClass('evenrow');
	$('#list li a:contains(' + artist + ')',window.parent.frames['frmartists'].document).each(
		function() {
			if ($(this).html() == artist)
				$(this).addClass('activerow');
		}
	);

	if (window.location.pathname != '/artists') {
		if (artist.charCodeAt(0) < 65)
			jumpa = '#';
		else 
			jumpa = artist.charAt(0).toLowerCase();
		window.parent.jump(jumpa);
	}
}

function albumTracks(artist,album) {
    window.parent.$('#frmtracks').attr('src','/tracks?artist=' + encodeURIComponent(artist) + '&album=' + encodeURIComponent(album))

	$('#list li:odd a',window.parent.frames['frmalbums'].document).removeClass('activerow').addClass('oddrow');
	$('#list li:even a',window.parent.frames['frmalbums'].document).removeClass('activerow').addClass('evenrow');
	$('#list li a:contains(' + album + ')',window.parent.frames['frmalbums'].document).each(
		function() {
            // wow this is a hack!
			if ($(this).html() == $('<div/>').text(album).html())
				$(this).addClass('activerow');
		}
	);
}

function resizeIframes() {
	if (window.innerHeight) {
		var theight = window.innerHeight - 357; 
		var pheight = window.innerHeight - 145;
		var lheight = window.innerHeight - 200;
		var lwidth = window.innerWidth / 2 - 50;
	} 
	else {
		var theight = document.documentElement.offsetHeight - 399 ; 
		var pheight = document.documentElement.offsetHeight - 204;
	}

    $('#frmtracks').css('height',theight + 'px');
    $('#frmplaylist').css('height',pheight + 'px');
    $('#fakeborder',window.frames['frmplaylist'].document).height(pheight);

	$('#lyrics').css('height',lheight + 'px');
	$('#lyrics').css('width',lwidth + 'px');
}

function addToPlaylist(file) {
    var url = '/mpdcontrol/addtoplaylist';

    $.ajax({
            url: url,
            type: 'POST',
            cache: false,
            data: 'file=' + file,
            success: function() {
                        window.parent.$('#frmplaylist').attr('src','/playlist')
                     }
          });
}

function removeTrack(el,id) {
    var url = '/mpdcontrol/removetrack/' + id
    window.parent.trackremoved = true;
    $.ajax({
            url: url,
            type: 'GET',
            cache: false,
            success: function() {
                        $(el).parent().remove();
                        setPlaylistColors(document)
                     }
          });
}

function setPlaylistColors(scope,force) {
    var addl = '';

    if (force != true)
        addl = ':not(li.selectedtrack)';

    $('#playlist li:even' + addl,scope).removeClass('selectedtrack').removeClass('evenrow').addClass('oddrow');
    $('#playlist li:odd' + addl,scope).removeClass('selectedtrack').removeClass('oddrow').addClass('evenrow');
}

function playNow(id) {
    var url = '/mpdcontrol/playnow/' + id;
    $.ajax({
            url: url,
            type: 'GET',
            cache: false,
            success: function() {
                        getStatus()
                     }
          });
}

function addAlbum(artist,album) {
    var url = '/mpdcontrol/addalbumtoplaylist?artist=' + encodeURIComponent(artist) + '&album=' + encodeURIComponent(album);
    $.ajax({
            url: url,
            type: 'GET',
            cache: false,
            success: function() {
                        $('#frmplaylist').attr('src','/playlist')
                        getStatus()
                     }
          });
}

function initConfig() {
    var arrPageSizes = getPageSize(); // from jquery-lightbox
    $('#dark-overlay').css({
        width:				arrPageSizes[2],
        height:				arrPageSizes[3]
    }).fadeIn();
    $('#config').show();
}

function hideConfig(reloadframes,reloadpage) {
    $('#config').hide();
    $('#dark-overlay').fadeOut();

    if (reloadpage) {
        document.location.replace('/');
        return;
    }

    if (reloadframes) {
        window.frames['frmartists'].location.reload();
        window.frames['frmplaylist'].location.reload();
    }

    getStatus();
}

function playlistAjax(func) {
    var url = '/mpdcontrol/' + func;
    $.ajax({
            url: url,
            type: 'GET',
            cache: false,
            success: function() {
                        window.location.reload()
                        window.parent.getStatus();
                     }
          });
}

function loadLyrics() {
    var artist = $('#currentartist').val()
    var track = $('#currenttitle').val()

    var url = '/lyrics?artist=' + artist + '&track=' + track;
    $('#lyrics').attr('src',url);
}

function loadPlaylist() {
    var playlist = $('#playlists').val();
    if (playlist == '') {
        alert('please select a playlist to load')
        return;
    }

    var url = '/playlist/load?name=' + playlist;
    $.ajax({
            url: url,
            type: 'GET',
            cache: false,
            success: function() {
                        window.location.reload();
                        window.parent.getStatus();
                     }
         });
        
}

function deletePlaylist() {
    var playlist = $('#playlists').val();
    if (playlist == '') {
        alert('please select a playlist to delete')
        return;
    }

    if (!confirm('Are you sure you want to delete this playlist?'))
        return;

    var url = '/playlist/delete?name=' + playlist;
    $.ajax({
            url: url,
            type: 'GET',
            cache: false,
            success: function() {
                        $('#playlists option[value=' + playlist + ']').remove();                        
                     }
         });
}

function fsStatus() {
    $.getJSON('/mpdcontrol/fs_status',
        function (data) {
            var begin_id = $('#currentid').html();

            if (data.current.title) {
                $('#not-playing').hide();
                $('#current').show();
                $('#next').show();
                $('#albumart-container').show();
				$('#progress').show();
                $('#currentid').html(data.current.id);
                $('#currenttrack').html(data.current.title);
                if (data.current.name) {
                    $('#currentartist').html(data.current.name);
                    $('#currentalbum').html();
                }
                else {
                    $('#currentartist').html(data.current.artist);
                    $('#currentalbum').html(data.current.album);
                }

                var arturl = '/fetchart?artist=' + data.current.artist + '&album=' + data.current.album
                $('#albumart-container a').attr('href',arturl)
                $('#albumart').attr('src',arturl)
                $('#albumart-container a').lightBox();
            }
            else if (data.status.state == 'stop') {
                $('#currentid').html('')
                $('#current').hide();
                $('#next').hide();
                $('#albumart-container').hide();
				$('#progress').hide();
                $('#not-playing').show();
                $('#currenttrack').html(data.current.title);
                $('#currentartist').html(data.current.artist);
                $('#currentalbum').html(data.current.album);

            }

            if (data.status.time) {
                var time = data.status.time.split(':');
                var currentseconds = time[0];
                var totalseconds = time[1];
            }
            else if (data.track && data.track.time) {
                var currentseconds = 0;
                var totalseconds = data.track.time;
            }
            else {
                var currentseconds = 0;
                var totalseconds = 0;
            }
            
            var currenttime = formatTime(currentseconds);
            var totaltime = formatTime(totalseconds);

            if (time) {
                $('#playing-time').html(currenttime);
                $('#total-time').html(totaltime);

                var progress = currentseconds / totalseconds * 100;
                $('#progress-img').css('width',progress + '%');
            }

            if (begin_id != data.status.id)
                $('#next').html('');

            for (var i = 0; i < data.playlist.length; i++) {
                if (data.playlist[i].artist && data.playlist[i].title)
                    var title = data.playlist[i].artist + ' - ' + data.playlist[i].title + '<br />';
                else
                    var title = data.playlist[i].file + '<br />';
                $('#next').append(title);
            }
        });
}

function getURL() {
    var url = prompt('Please enter the URL of the stream you\'d like to append to the playlist:');
    if (url) {
        addToPlaylist(url);
    }
}

function editStream(name,url) {
    $('#oldname').val(name);
    $('#name').val(name);
    $('#url').val(url);

    $('#addtitle').html('edit stream');
    window.location.hash = 'form';
}
