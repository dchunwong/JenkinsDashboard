$(document).ready(function() {
    var autoWidth;
    if(window.innerWidth < 768){
        autoWidth = false;
    }else{
        autoWidth = true;
    }
    $("#jobselect").select2({
        placeholder: "Select a Job",
        dropdownAutoWidth: autoWidth
    });
    $("#buildselect").select2({
        placeholder: "Select a Build",
        dropdownAutoWidth: autoWidth,
        allowClear: true,
        ajax:{
            url: function(){
                return "/api/job/"+$("#jobselect").val()+"/builds"
            },
            dataType: "json",
            data: function(term){
                return {q:term}
            },
            results: function(data){
                temp = {results:[]}
                for(var i=0; i < data.results.length; i++){
                    build = data.results[i].toString()
                    temp.results.push({id:build, text:build});
                }
                return temp
            }
        }
    })

    $("#testselect").select2({
        placeholder: "Select a Test",
        dropdownAutoWidth: autoWidth,
        allowClear: true,
        ajax:{
            url: function(){
                return "/api/job/"+$("#jobselect").val()+"/tests";
            },
            dataType: "json",
            data: function(term){
                return {q:term}
            },
            results: function(data){
                temp = {results:[]}
                for(var i=0; i < data.results.length; i++){
                    temp.results.push({id:data.results[i], text:data.results[i]});
                }
                return temp
            }
        }
    });

    job_index = document.URL.split('/').indexOf('job');
    if(job_index != -1){
        $("#jobselect").select2("val", document.URL.split('/')[job_index+1]);
    }
    toggleSelects();

    $("#jobselect").on("change", toggleSelects);
    $("#buildselect").on("change", function(){disableOther('#buildselect', '#testselect')});
    $("#testselect").on("change", function(){disableOther('#testselect', '#buildselect')});
    $("#search").keypress(function(event){
        if(event.key == "Enter"){
            $("#search").submit()
        }
    })
});

var toggleSelects = function(){
    $("#testselect").select2("val", "");
    $("#buildselect").select2("val", "");
    if($("#jobselect").val() == ""){
        $("#testselect").select2("enable", false);
        $("#buildselect").select2("enable", false);
    } else{
        $("#testselect").select2("enable", true);
        $("#buildselect").select2("enable", true);
    }
}
var grabTests = function(){
    var value = $("#jobselect").val();
    $.getJSON("/api/job/"+value, function(data){
        $("#testselect").select2();
    })
}

var disableOther = function(el1, el2){
    if($(el1).val() != ""){
        $(el2).select2("val", "");        
        $(el2).select2("enable", false);        
    } else{
        $(el2).select2("enable", true);
    }
}
