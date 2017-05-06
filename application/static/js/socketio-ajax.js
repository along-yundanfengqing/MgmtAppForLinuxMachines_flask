$(function () {
    var socket = io.connect('http://localhost:5000');

    socket.on('connect', function() {
        socket.emit('message', {data: 'connected'});
    });

    socket.on('disconnect', function() {
        socket.emit('message', {data: 'disconnected'});
    });

    socket.on('message', function(msg){
        // Background thread started
        if (msg.data === "started") {
            $('#status-message').html('<img src="/static/images/ajax-loader.gif"><span class="text-success"> Collecting machine data...</span>');
        }
        // Background thread completed
        else if (msg.data === "completed") {
            $('#status-message').html('<span class="text-success">Completed</span>');
            setTimeout(function () {
                $('#status-message').text("");
            }, 2000);
        }
        // New machine created with status #Unknwon
        else if (msg.data === "created_new") {
            var url = '/api/machines/' + msg.ip_address;
            $.getJSON(url, function(data){
                var machine = data['data'];
                if (machine['Status'].includes("Unknown")){
                    createUnknownMachineElement(msg.ip_address, machine);
                }
            }).fail(function(e) {
                // Error handling
                alert("Ajax failed");
                location.reload();
            });
        }
        // Machines updated
        else if (msg.data === "created" || msg.data === "updated") {
            location.reload();
        }
        // Machines deleted
        else if (msg.data === "deleted") {
            var modal01ID = $('img[id="machine-img-' + msg.ip_address + '"]').attr('data-target');
            //var modal02ID = $(modal01ID).find('.modal-footer a').attr('data-target');
            var index = modal01ID.replace("#myModal_machine_data", "");
            var modal02ID = "#myModal_export_json" + index;
            var numOfMachines = parseInt($('.badge').text());
            $('.badge').text(numOfMachines - 1);
            $('div[id=' + '"machine-' + msg.ip_address + '"]').remove();
            $(modal01ID).remove();
            $(modal02ID).remove();
        }
        // Machines become unreachable status
        else if (msg.data === "unreachable") {
            var imgName = $('img[id="machine-img-' + msg.ip_address + '"]').attr('src');
            if (! imgName.includes("unreachable.png")) {
                $('img[id="machine-img-' + msg.ip_address + '"]').attr('src', imgName.replace(".png", "_unreachable.png"));
            }
        }
    });
});


function createUnknownMachineElement(ip_address, machine) {
    var numOfMachines = parseInt($('.badge').text());
    var index = numOfMachines + 101;
    $('.badge').text(numOfMachines + 1);

    var ip_address_aws = ip_address;
    if (machine['AWS']) {
        ip_address_aws = ip_address + " (AWS)";
    }

    // Top page machine icon
    $('#machine-list').prepend(
        '<div class="col-xs-4 col-sm-3 col-md-2" id="machine-' + ip_address + '">' +
        '<img id="machine-img-' + ip_address + '" class="img-responsive" src="/static/images/other.png" data-toggle="modal" data-target="#myModal_machine_data' + index + '">' +
        '<h4><a href="#" data-toggle="modal" data-target="#myModal_machine_data' + index + '" id="machine-hostname-#Unknown-' + index + '">#Unknown</a></h4>' +
        '<h5><a href="#" data-toggle="modal" data-target="#myModal_machine_data' + index + '" id="machine-ip-' + ip_address + '-' + index + '">' + ip_address_aws + '</a></h5>' +
        '</div>'

     );


     // Modal#1
     $('#modal1').prepend(
        '<div class="modal fade" id="myModal_machine_data' + index + '" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">' +
        '<div class="modal-dialog">' +
          '<div class="modal-content">' +
            '<div class="modal-header">' +
              '<h4 class="modal-title" id="myModalLabel">#Unknown</h4>' +
            '</div>' +
            '<div class="modal-body" id="modal-body' + index + '">' +
                '<div class ="text-right">Last Updated:</div>' +
                '<div class ="text-right"></div>' +
                '<div class="tabbable">' +
                    '<ul class="nav nav-tabs" role="tablist">' +
                      '<li role="presentation" class="active"><a href="#basic' + index + '" aria-controls="basic' + index + '" role="tab" data-toggle="tab">Basic</a></li>' +
                      '<li role="presentation"><a href="#cpu' + index + '" aria-controls="cpu' + index + '" role="tab" data-toggle="tab">CPU</a></li>' +
                      '<li role="presentation"><a href="#memory' + index + '" aria-controls="memory' + index + '" role="tab" data-toggle="tab">Memory</a></li>' +
                      '<li role="presentation"><a href="#disk' + index + '" aria-controls="disk' + index + '" role="tab" data-toggle="tab">Disk</a></li>' +
                    '</ul>' +
                    '<div class="tab-content">' +
                      '<div role="tabpanel" class="tab-pane active" id="basic' + index + '">' +
                          '<h5>Basic Machine Data</h5>' +
                          '<div class="table-responsive">' +
                              '<table class="table table-hover">' +
                                '<tbody>' +
                                  '<th class="active"> Items </th>' +
                                  '<th class="active"> Parameters </th>' +
                                  '<tr>' +
                                    '<td>Status:</td>' +
                                        '<td><img src="/static/images/status_unknown.png"> Unknown (Waiting for the first SSH access)</td>' +
                                  '</tr>' +
                                  '<tr>' +
                                    '<td>OS Distribution:</td>' +
                                    '<td> N.A </td>' +
                                  '</tr>' +
                                  '<tr>' +
                                    '<td>Release:</td>' +
                                    '<td> N.A </td>' +
                                  '</tr>' +
                                  '<tr>' +
                                    '<td>IP Address:</td>' +
                                    '<td>' + ip_address + '</td>' +
                                  '</tr>' +
                                  '<tr>' +
                                    '<td>MAC Address:</td>' +
                                    '<td> N.A </td>' +
                                  '</tr>' +
                                  '<tr>' +
                                    '<td>Uptime:</td>' +
                                    '<td> N.A </td>' +
                                  '</tr>' +
                                '</tbody>' +
                              '</table>' +
                          '</div>' +
                      '</div>' +
                      '<div role="tabpanel" class="tab-pane" id="cpu' + index + '">' +
                          '<h5>CPU Load Average</h5>' +
                          '<div class="table-responsive">N.A</div>' +
                      '</div>' +
                      '<div role="tabpanel" class="tab-pane" id="memory' + index + '">' +
                          '<h5>Memory Usage</h5>' +
                          '<div class="table-responsive">N.A</div>' +
                      '</div>' +

                      '<div role="tabpanel" class="tab-pane" id="disk' + index + '">' +
                          '<h5>Disk Usage</h5>' +
                          '<div class="table-responsive">N.A</div>' +
                      '</div>' +
                    '</div>' +
                    '<div class ="text-right"></div>' +
                '</div>' +
            '</div>' +
            '<div class="modal-footer">' +
              '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>' +
            '</div>' +
          '</div>' +
        '</div>'
    );

}

