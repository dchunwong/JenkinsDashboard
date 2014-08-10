$(document).ready(function() {
    var $jobSelector = $("#jobselect");
    var $buildSelector = $("#buildselect");
    var $testSelector =  $("#testselect");
    var autoWidth = window.innerWidth > 768;
    $jobSelector.select2({
        placeholder: "Select a Job",
        dropdownAutoWidth: autoWidth
    });

    $buildSelector.select2({
        placeholder: "Select a Build",
        dropdownAutoWidth: autoWidth,
        allowClear: true,
        ajax:{
            url: function(){
                return "/api/job/"+$jobSelector.val()+"/builds";
            },
            dataType: "json",
            data: function(term){
                return {q:term};
            },
            results: function(data){
                temp = {results:[]};
                for(var i=0; i < data.results.length; i++){
                    build = data.results[i].toString();
                    temp.results.push({id:build, text:build});
                }
                return temp
            }
        }
    });

    $testSelector.select2({
        placeholder: "Select a Test",
        dropdownAutoWidth: autoWidth,
        allowClear: true,
        ajax:{
            url: function(){
                return "/api/job/"+$jobSelector.val()+"/tests";
            },
            dataType: "json",
            data: function(term){
                return {q:term};
            },
            results: function(data){
                temp = {results:[]};
                for(var i=0; i < data.results.length; i++){
                    temp.results.push({id:data.results[i], text:data.results[i]});
                }
                return temp
            }
        }
    });

    job_index = document.URL.split('/').indexOf('job');
    if(job_index != -1){
        $jobSelector.select2("val", document.URL.split('/')[job_index+1]);
    }
    var toggleSelects = function(){
        $testSelector.select2("val", "");
        $buildSelector.select2("val", "");
        if($jobSelector.val() == ""){
            $testSelector.select2("enable", false);
            $buildSelector.select2("enable", false);
        } else{
            $testSelector.select2("enable", true);
            $buildSelector.select2("enable", true);
        }
    };
    toggleSelects();

    $jobSelector.on("change", toggleSelects);
    $buildSelector.on("change", function(){disableOther('#buildselect', '#testselect')});
    $testSelector.on("change", function(){disableOther('#testselect', '#buildselect')});
    $("#search").keypress(function(event){
        if(event.key == "Enter"){
            $("#search").submit()
        }
    })
});


var disableOther = function(el1, el2){
    if($(el1).val() != ""){
        $(el2).select2("val", "");        
        $(el2).select2("enable", false);        
    } else{
        $(el2).select2("enable", true);
    }
};
