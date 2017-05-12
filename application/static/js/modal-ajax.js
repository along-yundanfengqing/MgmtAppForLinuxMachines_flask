$(function () {
  $('#machine-list').on('click', 'img[id^=machine-img], a[id^=machine-hostname], a[id^=machine-ip]', function(){
    var ipAddress = $(this).parent().find('a[id^=machine-ip]').text();
    var index = $(this).attr("data-target").replace("#myModal_machine_data", "");
    $.ajax({
        type: "GET",
        url: '/api/machines/' + ipAddress,
        dataType: "json",
        success: function(data){
            var machine = data['data'];
            var thisModal = $('#myModal_machine_data' + index);
            var now = new Date().getTime();
            var lastUpdated = Date.parse(machine['last_updated']);
            var lastUpdatedFormatted = getFormattedDatetime(new Date(lastUpdated));
            var deltaInSec = Math.ceil((now - lastUpdated)/1000);

            // Last updated
            thisModal.find('#modal-body' + index + ' > div:nth-child(2)').text(lastUpdatedFormatted + ' (' + deltaInSec + ' seconds ago)');

            if (machine['status'] === 'OK'){
                // Basic tab
                thisModal.find('#basic' + index + ' tbody tr:nth-child(2) td:nth-child(2)').html('<img src="/static/images/status_ok.png"> OK');
                thisModal.find('#basic' + index + ' tbody tr:nth-child(3) td:nth-child(2)').text(machine['os_distribution']);
                thisModal.find('#basic' + index + ' tbody tr:nth-child(4) td:nth-child(2)').text(machine['release']);
                thisModal.find('#basic' + index + ' tbody tr:nth-child(6) td:nth-child(2)').text(machine['mac_address']);
                thisModal.find('#basic' + index + ' tbody tr:nth-child(7) td:nth-child(2)').text(machine['uptime']);

                // CPU tab
                thisModal.find('#cpu' + index + ' tbody tr:nth-child(2) td:nth-child(1)').text(machine['cpu_load_avg']['1min']);
                thisModal.find('#cpu' + index + ' tbody tr:nth-child(3) td:nth-child(1)').text(machine['cpu_load_avg']['5min']);
                thisModal.find('#cpu' + index + ' tbody tr:nth-child(4) td:nth-child(1)').text(machine['cpu_load_avg']['15min']);

                // Memory tab
                if (Object.keys(machine['memory_usage']).length === 3){
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(2)').text(machine['memory_usage']['mem']['total']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(3)').text(machine['memory_usage']['mem']['used']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(4)').text(machine['memory_usage']['mem']['free']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(5)').text(machine['memory_usage']['mem']['shared']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(6)').text(machine['memory_usage']['mem']['buffers']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(7)').text(machine['memory_usage']['mem']['cached']);

                    thisModal.find('#memory' + index + ' tbody tr:nth-child(3) td:nth-child(3)').text(machine['memory_usage']['buffers/cache']['used']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(3) td:nth-child(4)').text(machine['memory_usage']['buffers/cache']['free']);

                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(2)').text(machine['memory_usage']['swap']['total']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(3)').text(machine['memory_usage']['swap']['used']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(4)').text(machine['memory_usage']['swap']['free']);
                }
                else if (Object.keys(machine['memory_usage']).length === 2){
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(2)').text(machine['memory_usage']['mem']['total']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(3)').text(machine['memory_usage']['mem']['used']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(4)').text(machine['memory_usage']['mem']['free']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(5)').text(machine['memory_usage']['mem']['shared']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(6)').text(machine['memory_usage']['mem']['buff/cache']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(7)').text(machine['memory_usage']['mem']['available']);

                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(2)').text(machine['memory_usage']['swap']['total']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(3)').text(machine['memory_usage']['swap']['used']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(4)').text(machine['memory_usage']['swap']['free']);
                }

                // Disk tab
                for (var i=0; i<machine['disk_usage'].length; i++){
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+2 + ') td:nth-child(1)').text(machine['disk_usage'][i]['filesystem']);
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+2 + ') td:nth-child(2)').text(machine['disk_usage'][i]['size']);
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+2 + ') td:nth-child(3)').text(machine['disk_usage'][i]['used']);
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+2 + ') td:nth-child(4)').text(machine['disk_usage'][i]['avail']);
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+2 + ') td:nth-child(5)').text(machine['disk_usage'][i]['use%']);
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+2 + ') td:nth-child(6)').text(machine['disk_usage'][i]['mounted_on']);
                }
            }

            else if(machine['status'] === 'Unreachable'){
              thisModal.find('#basic' + index + ' tbody tr:nth-child(2) td:nth-child(2)').html('<img src="/static/images/status_unreachable.png"> Unreachable (SSH access failed ' + machine['fail_count'] + ' times)');
              thisModal.find('form button').remove();
            }
            else{ // Unknown
              thisModal.find('#basic' + index + ' tbody tr:nth-child(2) td:nth-child(2)').html('<img src="/static/images/status_unknown.png"> Unknown (Waiting for the first SSH access)');
              thisModal.find('form button').remove();
            }
        }
    });
  });
});


function getFormattedDatetime(str){
    var months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    var M = months[str.getMonth()];
    var dd = str.getDate() < 10 ? '0' + str.getDate(): str.getDate();
    var yyyy = str.getFullYear();
    var hh = str.getHours() < 10 ? '0' + str.getHours() : str.getHours();
    var mm = str.getMinutes() < 10 ? '0' + str.getMinutes() : str.getMinutes();
    var ss = str.getSeconds() < 10 ? '0' + str.getSeconds() : str.getSeconds();
    var formattedDatetime = M + " " + dd + ", " + yyyy + " / " + hh + ":" + mm + ":" + ss;
    return formattedDatetime;
}
