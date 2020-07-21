function get_file_name(){
    // $('#location').val($('#i-file').val());
    var file_info =$('#i-file')[0].files[0];
    $('#location').val(file_info.name);
}
$(function () {
    $("#file_upload").click(function(){
        var form_data = new FormData();
        var file_info =$('#i-file')[0].files[0];
        form_data.append('file', file_info);
        // form_data.append("csrfmiddlewaretoken", "{{ csrf_token }}");
        if(file_info === undefined)
            alert('你没有选择任何文件');
        else{
            $.ajax({
                url:'/index/upload_file',
                type:'POST',
                data: form_data,
                processData: false,  // tell jquery not to process the data
                contentType: false, // tell jquery not to set contentType
                success: function(data) {
                    if(data.status === 'success'){
                        alert(data.msg);
                        window.location.reload();
                            // window.location.href = '/index/homepage';
                    }else{
                        alert(data.msg);
                    }
                    $("#myModal").modal("hide");
                }
            });
        }
    });

    $("#spider_submit").click(function(){
        var spider_key_word = $("#spider_key_word").val();
        $.post('/index/spider_submit',
            {
                spider_key_word: spider_key_word,
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
                $("#myModal").modal("hide");
            }
        )
    });
    $(".log_delete").click(function(){
        var log_id = $(this).parent().parent().attr("data-id");
        $.post('/index/delete_acquisition_log',
            {
                log_id: log_id,
            },
            function (data){
                console.log(data);
                if(data.status == 'success'){
                    alert(data.msg);
                    // window.location.href = '/index/homepage';
                    window.location.reload();
                }else{
                    alert(data.msg);
                }
                // $("#myModal").modal("hide");
            }
        )
    });
    $(".view_file_content").click(function () {
        var file_id = $(this).parent().parent().attr("data-id");
        window.open("/index/view_file_content?file_id=" + file_id);
    });
});