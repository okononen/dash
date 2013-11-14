function callAjax (){ 
    params = window.location.search;
    $.ajax({
        type: "GET",
        url: "http://claw.cs.uwaterloo.ca/~okononen/cgi-bin/dash.py" + params,
        cache: "false",
        success: function (response) {
            document.getElementById('main').innerHTML = response;
            $('tr[title]').qtip({
                    position: {
                        my: 'top center',
						at: 'bottom center'
                    },
                    style: {
                        classes: 'qtipCustomClass'
                    }
				});
        },
        error: function (jqXHR, textStatus, errorThrown) {
            if (jqXHR.status === 0) {
                msg = 'Not connect.\n Verify Network.';
            } else if (jqXHR.status == 404) {
                msg = 'Requested page not found. [404]';
            } else if (jqXHR.status == 500) {
                msg = 'Internal Server Error [500].';
            } else if (exception === 'parsererror') {
                msg = 'Requested JSON parse failed.';
            } else if (exception === 'timeout') {
                msg = 'Time out error.';
            } else if (exception === 'abort') {
                msg = 'Ajax request aborted.';
            } else {
                msg = 'Uncaught Error.\n' + jqXHR.responseText;
            }

	    $(document.body).innerHTML = msg;
       }
    });
}

$(document).ready(function(){
callAjax();
//setInterval(callAjax,3600000);
});

