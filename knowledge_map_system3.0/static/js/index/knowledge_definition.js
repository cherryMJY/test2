$(function () {
	$(".frist-title").on("click",function(){
		$(this).find(".myicon").toggle();
		$(this).parent().next().toggle();
		var text = $(this).find(".text").text();
		console.log(text)
	});

	$("#container1").on("click",".second-title",function(){
		$(this).find(".myicon").toggle();
		$(this).parent().next(".three-wrapper").toggle();
		console.log($(this).find(".text").text());
	});

	/**
     * 新建知识库模态框关闭事件，清空文本内容
     */
	$('#myModal').on('hide.bs.modal', function () {
        $("#category_name").val("");
        $("#inherit_category").val("事物");
        $("#category_describe").val("");
    });
	/**
     * 修改知识库模态框打开事件，填充文本内容
     */
    $('#myModal2').on('shown.bs.modal', function (event) {
         var btnThis = $(event.relatedTarget);
         var attribute_name = btnThis.parent().parent().find("td").eq(0).html();
         var attribute_alias = btnThis.parent().parent().find("td").eq(1).html();
         var attribute_type = btnThis.parent().parent().find("td").eq(2).html();
         var attribute_is_single_value = btnThis.parent().parent().find("td").eq(3).html();
         var attribute_describe = btnThis.parent().parent().find("td").eq(4).html();
         $("#attribute_name_update").val(attribute_name);
         $("#attribute_alias_update").val(attribute_alias);
         $("#attribute_type_update").val(attribute_type);
         $("#attribute_is_single_value_update").val(attribute_is_single_value);
         $("#attribute_describe_update").val(attribute_describe);
    });
    /**
     * 修改知识库模态框关闭事件，清空文本内容
     */
	$('#myModal2').on('hide.bs.modal', function () {
        $("#attribute_name_update").val("");
         $("#attribute_alias_update").val("");
         $("#attribute_type_update").val("字符串");
         $("#attribute_is_single_value_update").val("单值");
         $("#attribute_describe_update").val("");
    });
    /**
     * 添加类目
     */
    $("#add_category").click(function () {
    	var category_name = $("#category_name").val();
        var inherit_category = $("#inherit_category").val();
        var category_describe = $("#category_describe").val();
        // alert(inherit_category);
        // $("#myModal").modal("hide");
        $.post('/index/add_category',
            {
                category_name: category_name,
                inherit_category: inherit_category,
                category_describe: category_describe
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
    /**
     * 添加属性
     */
    $(".add_attribute").click(function () {
        var attribute_name = $("#attribute_name").val();
        var attribute_alias = $("#attribute_alias").val();
        var attribute_type = $("#attribute_type").val();
        var attribute_is_single_value = $("#attribute_is_single_value > option:selected").attr("data-id");
        var attribute_describe = $("#attribute_describe").val();

        $.post('/index/add_attribute',
            {
                attribute_name: attribute_name,
                attribute_alias: attribute_alias,
                attribute_type: attribute_type,
                attribute_is_single_value: attribute_is_single_value,
                attribute_describe: attribute_describe
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

    $("#attribute_update").click(function () {
        var attribute_name = $("#attribute_name_update").val();
        var attribute_alias = $("#attribute_alias_update").val();
        var attribute_type = $("#attribute_type_update").val();
        var attribute_is_single_value = $("#attribute_is_single_value_update > option:selected").attr("data-id");
        var attribute_describe = $("#attribute_describe_update").val();
        $.post('/index/attribute_update',
            {
                attribute_name: attribute_name,
                attribute_alias: attribute_alias,
                attribute_type: attribute_type,
                attribute_is_single_value: attribute_is_single_value,
                attribute_describe: attribute_describe
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