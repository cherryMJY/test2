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
    $(".knowledge_extract").click(function () {
        var log_id = $(this).parent().parent().find(".log_id").html();
        $.post('/index/knowledge_extract',
            {
                log_id: log_id,
            },
            function (data){
                console.log(data);
                if(data.status === 'success'){
                    alert(data.msg);
                    window.location.reload();
                    // window.location.href = '/index/homepage';
                }else{
                    alert(data.msg);
                }
            }
        )
    });
    $(".extract_detail").click(function () {
        var log_id = $(this).parent().parent().find(".log_id").html();
        window.location.href = '/index/extract_result?log_id=' + log_id;
    });
});