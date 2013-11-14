$(document).ready(function() {

    $("body").on('submit', "#form1", (function(event) {
        var form = this;
        event.preventDefault(); // don't submit the form yet
        _gaq.push(["_trackEvent", "Form", "Submitted"]); // create a custom event
        setTimeout(function() { // now wait 300 milliseconds...
          form.submit(); // ... and continue with the form submission
        }, 300);
    }));
                
    $("body").on("click",".content a", (function(event) {
        var href = $(this).attr("href");
	var target = "_blank";
     	event.preventDefault(); // don't open the link yet
            if (href.indexOf("https://bugzilla")!==-1) {
                _gaq.push(["_trackEvent", "Links", "Issue", href]); // create a custom event
                setTimeout(function() { // now wait 300 milliseconds...
                  window.open(href, target); // ...and open the link as usual
            },300);}
            if (href.indexOf("https://bug")!==-1 && href.indexOf("attachment")!==-1) {
                _gaq.push(["_trackEvent", "Links", "Patch", href]); // create a custom event
                setTimeout(function() { // now wait 300 milliseconds...
                  window.open(href, target); // ...and open the link as usual
            },300);}

    }));

    $("body").on("change", 'input[type=radio]', (function(){
        var label = $(this).attr("value");  
        var id = $(this).attr("id");          
        //push the selection event to GA
        _gaq.push(["_trackEvent", "Tab", "Selected", id]);
    }));    
 
});
