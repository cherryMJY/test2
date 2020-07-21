$(function () {
    function toggleChange(id) {
        project_status = '';
        if($('#toggle-trigger'+id).prop("checked")){
            project_status = 'start';
        }else{
            project_status = 'stop';
        }
        $.ajax({
         type: "GET",
         url: "/spider/status",
         data: { status: project_status,id:id },
         dataType: "json",
         success: function(data){
             console.log(data)
          }
        });
    }
    function refresh_project_statistics(project_id) {
        $.get("/spider/statistics",{'id':project_id}, function(ret){
            $("#project_statistics_"+project_id).html(ret);
        })
    }

    $("#add_project").click(function () {
        let spider_data_website_id = $("#spider_data_website > option:selected").attr("data-id");
        let spider_data_type_id = $("#spider_data_type > option:selected").attr("data-id");
        console.log(spider_data_website_id);
        console.log(spider_data_type_id);
        $.post('/index/add_project',
            {
                spider_data_website_id: spider_data_website_id,
                spider_data_type_id: spider_data_type_id
            },
            function (data){
                console.log(data);
                if(data.status === 'success'){
                    alert(data.msg);
                    window.location.reload();
                }else{
                    alert(data.msg);
                }
            }
        )
    });
});