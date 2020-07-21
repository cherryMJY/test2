$(function () {
    $(".update_entity_info").click(function () {
        var entity_id = $(this).parent().parent().parent().find("span[data-name='_id']").html();
        var category_id = $(this).parent().find(".categote_select > option:selected").attr("data-id");
        $.post('/index/update_entity_info',
            {
                entity_id: entity_id,
                category_id: category_id
            },
            function (data){
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
});