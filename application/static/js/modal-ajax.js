$(function refreshModal() {
  $('img[id^=machine-img], a[id^=machine-hostname], a[id^=machine-ip]').on('click', function(){
    var ipAddress = $(this).parent().find('a[id^=machine-ip]').text();
    var index = $(this).attr("data-target").replace("#myModal_machine_data", "");
    $.ajax({
        type: "GET",
        url: '/api/machines/' + ipAddress,
        dataType: 'json',
        success: function(data){
            var machine = data['data'];
            var thisModal = $('#myModal_machine_data' + index);
            var now = new Date().getTime();
            var lastUpdated = Date.parse(machine['Last Updated']);
            var lastUpdatedFormatted = getFormattedDatetime(new Date(lastUpdated));
            var deltaInSec = Math.ceil((now - lastUpdated)/1000);

            // Last updated
            thisModal.find('#modal-body' + index + ' > div:nth-child(2)').text(lastUpdatedFormatted + ' (' + deltaInSec + ' seconds ago)');

            if (machine['Status'] === 'OK'){
                // Basic tab
                thisModal.find('#basic' + index + ' tbody tr:nth-child(2) td:nth-child(2)').html('<img src="/static/images/status_ok.png"> OK');
                thisModal.find('#basic' + index + ' tbody tr:nth-child(3) td:nth-child(2)').text(machine['OS']);
                thisModal.find('#basic' + index + ' tbody tr:nth-child(4) td:nth-child(2)').text(machine['Release']);
                thisModal.find('#basic' + index + ' tbody tr:nth-child(6) td:nth-child(2)').text(machine['MAC Address']);
                thisModal.find('#basic' + index + ' tbody tr:nth-child(7) td:nth-child(2)').text(machine['Uptime']);

                // CPU tab
                thisModal.find('#cpu' + index + ' tbody tr:nth-child(2) td:nth-child(1)').text(machine['CPU Load Avg']['1min']);
                thisModal.find('#cpu' + index + ' tbody tr:nth-child(3) td:nth-child(1)').text(machine['CPU Load Avg']['5min']);
                thisModal.find('#cpu' + index + ' tbody tr:nth-child(4) td:nth-child(1)').text(machine['CPU Load Avg']['15min']);

                // Memory tab
                if (Object.keys(machine['Memory Usage']).length === 3){
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(2)').text(machine['Memory Usage']['Mem']['total']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(3)').text(machine['Memory Usage']['Mem']['used']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(4)').text(machine['Memory Usage']['Mem']['free']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(5)').text(machine['Memory Usage']['Mem']['shared']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(6)').text(machine['Memory Usage']['Mem']['buffers']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(7)').text(machine['Memory Usage']['Mem']['cached']);

                    thisModal.find('#memory' + index + ' tbody tr:nth-child(3) td:nth-child(3)').text(machine['Memory Usage']['buffers/cache']['used']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(3) td:nth-child(4)').text(machine['Memory Usage']['buffers/cache']['free']);

                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(2)').text(machine['Memory Usage']['swap']['total']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(3)').text(machine['Memory Usage']['swap']['used']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(4)').text(machine['Memory Usage']['swap']['free']);
                }
                else if (Object.keys(machine['Memory Usage']).length === 2){
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(2)').text(machine['Memory Usage']['Mem']['total']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(3)').text(machine['Memory Usage']['Mem']['used']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(4)').text(machine['Memory Usage']['Mem']['free']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(5)').text(machine['Memory Usage']['Mem']['shared']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(6)').text(machine['Memory Usage']['Mem']['buff/cache']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(2) td:nth-child(7)').text(machine['Memory Usage']['Mem']['available']);

                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(2)').text(machine['Memory Usage']['swap']['total']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(3)').text(machine['Memory Usage']['swap']['used']);
                    thisModal.find('#memory' + index + ' tbody tr:nth-child(4) td:nth-child(4)').text(machine['Memory Usage']['swap']['free']);
                }

                // Disk tab
                for (var i=0; i<machine['Disk Usage'].length; i++){
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+1 + ') td:nth-child(1)').text(machine['Disk Usage'][i]['Filesystem']);
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+1 + ') td:nth-child(2)').text(machine['Disk Usage'][i]['Size']);
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+1 + ') td:nth-child(3)').text(machine['Disk Usage'][i]['Used']);
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+1 + ') td:nth-child(4)').text(machine['Disk Usage'][i]['Avail']);
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+1 + ') td:nth-child(5)').text(machine['Disk Usage'][i]['Use%']);
                    thisModal.find('#disk' + index + ' tbody tr:nth-child(' + i+1 + ') td:nth-child(6)').text(machine['Disk Usage'][i]['Mounted on']);
                }

            }

            else if(machine['Status'] === 'Unreachable'){
              thisModal.find('#basic' + index + ' tbody tr:nth-child(2) td:nth-child(2)').html('<img src="/static/images/status_unreachable.png"> Unreachable (SSH access failed ' + machine['Fail_count'] + ' times)');
              thisModal.find('form button').remove();
            }
            else{
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
