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
            //var url = '/api/machines/' + msg.ip_address;
            $.ajax({
                type: "GET",
                url: '/api/machines/' + msg.ip_address,
                dataType: "json",
                success: function(data){
                    var machine = data['data'];
                    if (machine['status'].includes("Unknown")){
                        insertUnknownMachineElement(msg.ip_address, machine);
                    }
                },
                error: function(e) {
                    // Error handling
                    location.reload();
                }
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
            $('div[id="machine-grid-' + msg.ip_address + '"]').remove();
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

        // EC2 instance's state transits among pending/running/starting/stopping
        else if (msg.data === "ec2_state_updated") {
            if (msg.state === "pending") {
                $('div[id="machine-grid-' + msg.ip_address + '"]').prepend('<img id="ec2-waiting-' + msg.ip_address + '" src="/static/images/ajax-loader2.gif" class="img-waiting"/><span class="txt-waiting">starting...</span>');

            }

            else if (msg.state === "running") {
                $('img[id="ec2-waiting-' + msg.ip_address + '"]').remove();
                $('.txt-waiting').remove();
            }

            else if (msg.state === "stopping") {
                $('div[id="machine-grid-' + msg.ip_address + '"]').prepend('<img id="ec2-waiting-' + msg.ip_address + '" src="/static/images/ajax-loader2.gif" class="img-waiting"/><span class="txt-waiting">stopping...</span>');
            }

            else if (msg.state === "stopped") {
                $('img[id="ec2-waiting-' + msg.ip_address + '"]').remove();
                $('.txt-waiting').remove();
            }

        }
    });
});

function getIndexToInsert(hostname, ip_address){
    var hostnameList = [];
    var ipaddressList = [];
    var index;
    $('[id^=machine-hostname]').each(function(){
        hostnameList.push($(this).text());
    });
    $('[id^=machine-ip]').each(function(){
        ipaddressList.push($(this).text());
    });

    for (var i = 0; i < hostnameList.length; i++){
        if (hostname < hostnameList[i]){
            index = i;
            break;
        }

        else if (hostname === hostnameList[i]){
            if (toInt(ip_address) < toInt(ipaddressList[i])){
                index = i;
                break;
            }
        }

        else {
            index = i + 1;
        }
   }

   return index;
}

function toInt(ip){
  var ipl=0;
  ip.split('.').forEach(function( octet ) {
      ipl<<=8;
      ipl+=parseInt(octet);
  });
  return(ipl >>>0);
};

function insertUnknownMachineElement(ip_address, machine) {
    var numOfMachines = parseInt($('.badge').text());
    var index = numOfMachines + 101;
    var indexToInsert = getIndexToInsert(machine['hostname'], ip_address) + 1;
    $('.badge').text(numOfMachines + 1);

    var ip_address_aws = ip_address;
    if (machine['aws']) {
        ip_address_aws = ip_address + " (AWS)";
    }

    // Top page machine icon
    $('#machine-list div:nth-child(' + indexToInsert + ')').before(
        '<div class="col-xs-4 col-sm-3 col-md-2" id="machine-grid-' + ip_address + '">' +
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
                '<div class="container-fluid">' +
                  '<div class="row">' +
                    '<div class="col-md-8">' +
                      '<h4 class="modal-title" id="myModalLabel">#Unknown</h4>' +
                   '</div>' +
                    '<div class="col-md-4">' +
                      '<div class ="text-right">' +
                      '</div>' +
                    '</div>' +
                  '</div>' +
              '</div>' +
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
                                    '<td> None </td>' +
                                  '</tr>' +
                                  '<tr>' +
                                    '<td>Release:</td>' +
                                    '<td> None </td>' +
                                  '</tr>' +
                                  '<tr>' +
                                    '<td>IP Address:</td>' +
                                    '<td>' + ip_address + '</td>' +
                                  '</tr>' +
                                  '<tr>' +
                                    '<td>MAC Address:</td>' +
                                    '<td> None </td>' +
                                  '</tr>' +
                                  '<tr>' +
                                    '<td>Uptime:</td>' +
                                    '<td> None </td>' +
                                  '</tr>' +
                                '</tbody>' +
                              '</table>' +
                          '</div>' +
                      '</div>' +
                      '<div role="tabpanel" class="tab-pane" id="cpu' + index + '">' +
                          '<h5>CPU Information</h5>' +
                          '<div class="table-responsive">None</div>' +
                          '<h5>CPU Load Average</h5>' +
                          '<div class="table-responsive">None</div>' +
                      '</div>' +
                      '<div role="tabpanel" class="tab-pane" id="memory' + index + '">' +
                          '<h5>Memory Usage</h5>' +
                          '<div class="table-responsive">None</div>' +
                      '</div>' +

                      '<div role="tabpanel" class="tab-pane" id="disk' + index + '">' +
                          '<h5>Disk Usage</h5>' +
                          '<div class="table-responsive">None</div>' +
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

