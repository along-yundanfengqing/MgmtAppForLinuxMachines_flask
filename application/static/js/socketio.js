$(function () {
    var socket = io.connect('http://localhost:5000');

    socket.on('connect', function() {
        socket.emit('message', {data: 'connected'});
    });

    socket.on('disconnect', function() {
        socket.emit('message', {data: 'disconnected'});
    });

    socket.on('message', function(msg){
        if (msg.data === "started") {
            $('#status-message').html('<img src="/static/images/ajax-loader.gif"><span class="text-success"> Collecting machine data...</span>');
        }
        else if (msg.data === "completed") {
            $('#status-message').html('<span class="text-success">Completed</span>');
            setTimeout(function () {
                $('#status-message').text("");
            }, 2000);
        }
        else if (msg.data === "created" || msg.data === "updated") {
            location.reload();
        }
        else if (msg.data === "deleted") {
            var modal01ID = $('img[id="machine-img' + msg.ip_address + '"]').attr('data-target');
            var modal02ID = $(modal01ID).find('.modal-footer a').attr('data-target');
            var numOfMachines = parseInt($('.badge').text());
            $('.badge').text(numOfMachines - 1);
            $('div[id=' + '"machine-' + msg.ip_address + '"]').remove();
            $(modal01ID).remove();
            $(modal02ID).remove();
        }
        else if (msg.data === "unreachable") {
            var imgName = $('img[id="machine-img' + msg.ip_address + '"]').attr('src');
            if (! imgName.includes("unreachable.png")) {
                $('img[id="machine-img' + msg.ip_address + '"]').attr('src', imgName.replace(".png", "_unreachable.png"));
            }
        }
    });
});