$(function () {
    $(".knowledge_extract_li").click(function () {
        var currentClass = $(this).attr("class");
        var tag = "active";
        if(currentClass.indexOf(tag) == -1){
            $(".active").removeClass("active");
            $(this).addClass("active");
            $(".knowledge_extract_div").show();
            $(".property_map_div").hide();
            $(".data_cleaning_div").hide();
            $(".merge_div").hide();
        }
    });

    $(".property_map_li").click(function () {
        var currentClass = $(this).attr("class");
        var tag = "active";
        if(currentClass.indexOf(tag) == -1){
            $(".active").removeClass("active");
            $(this).addClass("active");
            $(".knowledge_extract_div").hide();
            $(".property_map_div").show();
            $(".data_cleaning_div").hide();
            $(".merge_div").hide();
        }
    });
    $(".data_cleaning_li").click(function () {
        var currentClass = $(this).attr("class");
        var tag = "active";
        if(currentClass.indexOf(tag) == -1){
            $(".active").removeClass("active");
            $(this).addClass("active");
            $(".knowledge_extract_div").hide();
            $(".property_map_div").hide();
            $(".data_cleaning_div").show();
            $(".merge_div").hide();
        }
    });

    $(".merge_li").click(function () {
        var currentClass = $(this).attr("class");
        var tag = "active";
        if(currentClass.indexOf(tag) == -1){
            $(".active").removeClass("active");
            $(this).addClass("active");
            $(".knowledge_extract_div").hide();
            $(".property_map_div").hide();
            $(".data_cleaning_div").hide();
            $(".merge_div").show();
        }
    });
});