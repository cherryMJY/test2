/**
 * Created by lenovo on 2020/3/21.
 */
$(function () {
    /**
     * 下拉框
     * @type {any}
     */

    $(".dropdownMenu1").hover(
        function(){
            $(this).parent().parent().parent().find(".dropDownCur").show();
    });//为了鼠标可以进入下拉框
    $(".dropDownCur").hover(function() {
        $(this).show();//鼠标进入下拉框
    }, function() {
        $(this).hide();//鼠标离开下拉框后，就会消失
    });
    /**
     * 新建知识库模态框关闭事件，清空文本内容
     */
    $('#myModal').on('hide.bs.modal', function () {
        $("#repo_name_add").val("");
        $("#repo_describe_add").val("");
    });
    /**
     * 修改知识库模态框打开事件，填充文本内容
     */
    $('#myModa2').on('shown.bs.modal', function (event) {
         var btnThis = $(event.relatedTarget);
         var repo_name = btnThis.parent().parent().parent().parent().find(".repo_name").html();
         var repo_id = btnThis.parent().parent().parent().parent().find(".repo_id").attr("id");
         var repo_describe = btnThis.parent().parent().parent().parent().find(".repo_describe").html();
         $("#repo_id_update").html(repo_id);
         $("#repo_name_update").val(repo_name);
         $("#repo_describe_update").val(repo_describe);
    });
    /**
     * 修改知识库模态框关闭事件，清空文本内容
     */
    $('#myModa2').on('hide.bs.modal', function () {
         $("#repo_id_update").html("");
         $("#repo_name_update").val("");
         $("#repo_describe_update").val("");
    });
    /**
     * 更新知识库
     */
    $("#update_repo").click(function () {
        var repo_id = $("#repo_id_update").html();
        var repo_name = $("#repo_name_update").val();
        var repo_describe = $("#repo_describe_update").val();
        $.post('/index/update_repo',
            {
                repo_id: repo_id,
                repo_name: repo_name,
                repo_describe: repo_describe
            },
            function (data){
                console.log(data);
                if(data.status == 'success'){
                    alert(data.msg);
                    location.reload();
                    // window.location.href = '/index/homepage';
                }else{
                    alert(data.msg);
                }
            }
        )
    });
    /**
     * 添加知识库
     */
    $("#add_repo").click(function () {
        var repo_name = $("#repo_name_add").val();
        var repo_describe = $("#repo_describe_add").val();
        // alert(repo_name);
        // alert(repo_describe);
        $.post('/index/add_repo',
            {
                repo_name: repo_name,
                repo_describe: repo_describe
            },
            function (data){
                console.log(data);
                if(data.status == 'success'){
                    alert(data.msg);
                    location.reload();
                    // window.location.href = '/index/homepage';
                }else{
                    alert(data.msg);
                }
            }
        )
    });
    /**
     * 删除知识库
     */
    $(".delete_repo").click(function () {
        var repo_id = $(this).parent().parent().parent().parent().find(".repo_id").attr("id");
        $.post('/index/delete_repo',
            {
                repo_id: repo_id,
            },
            function (data){
                console.log(data);
                if(data.status == 'success'){
                    alert(data.msg);
                    location.reload();
                    // window.location.href = '/index/homepage';
                }else{
                    alert(data.msg);
                }
            }
        )
    });
    $(".guess-item").click(function () {
        window.location.href = '/index/knowledge_definition';
    })
});