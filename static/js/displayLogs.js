function displayLogs(e){
    element = e.currentTarget;
    modContainer = $("#modal_container")
    $("#modal_content")[0].innerHTML = test_data[+ $(element).parent()[0].getAttribute("data-idx")].test_list[element.getAttribute("data-idx")].log;
    modContainer.fadeIn();
    modContainer.css("display", "block");
    $("#modal_close").click(function(e){
        modContainer.fadeOut(function(){
            modContainer.css("display", "none");
        })
    })
}

$(".Error").click(displayLogs)
$(".Failed").click(displayLogs)
$("Expected.Failure").click(displayLogs)
