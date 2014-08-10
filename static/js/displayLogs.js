function displayLogs(e){
    element = e.currentTarget;
    modContainerSelector = $("#modal_container");
    $("#modal_content")[0].innerHTML = test_data[+ $(element).parent()[0].getAttribute("data-idx")].test_list[element.getAttribute("data-idx")].log;
    modContainerSelector.fadeIn();
    modContainerSelector.css("display", "block");
    $("#modal_close").click(function(e){
        modContainerSelector.fadeOut(function(){
            modContainerSelector.css("display", "none");
        })
    })
}

$(".Error").click(displayLogs)
$(".Failure").click(displayLogs)
$("Expected.Failure").click(displayLogs)
