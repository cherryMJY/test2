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
        if(file_info === undefined)
            alert('你没有选择任何文件');
        else{
            $.ajax({
                url:'/index/file_upload',
                type:'POST',
                data: form_data,
                processData: false,  // tell jquery not to process the data
                contentType: false, // tell jquery not to set contentType
                success: function(data) {
                    if(data.status === 'success'){
                    alert(data.msg);
                        // window.location.href = '/index/homepage';
                    }else{
                        alert(data.msg);
                    }
                }
            });
        }
    });

    $("#spider_submit").click(function(){
        var spider_key_word = $("#spider_key_word");
        $.post('/index/spider_submit',
            {
                spider_key_word: spider_key_word,
            },
            function (data){
                console.log(data);
                if(data.status == 'success'){
                    alert(data.msg);
                    // window.location.href = '/index/homepage';
                }else{
                    alert(data.msg);
                }
                $("#myModal").modal("hide");
            }
        )
    });
});