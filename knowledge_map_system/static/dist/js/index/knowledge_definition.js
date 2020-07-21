$(function () {
    let cur_attribute;
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
         let btnThis = $(event.relatedTarget);
         let cur_tr = btnThis.parent().parent();
         let cur_index = cur_tr.parent().children().index(cur_tr);
         let update_attribute = cur_attribute[cur_index];
         console.log(cur_attribute[cur_index]);
         // var attribute_id = btnThis.parent().parent().attr("data-id");
         // var attribute_name = btnThis.parent().parent().find("td").eq(0).html();
         // var attribute_alias = btnThis.parent().parent().find("td").eq(1).attr("data-value");
         // var attribute_type = btnThis.parent().parent().find("td").eq(2).html();
         // var attribute_is_single_value = btnThis.parent().parent().find("td").eq(3).html();
         // var attribute_describe = btnThis.parent().parent().find("td").eq(4).attr("data-value");
         $(".attribute_update_form").attr("data-id", update_attribute.id);
         $("#attribute_name_update").val(update_attribute.attribute_name);
         $("#attribute_alias_update").val(update_attribute.attribute_alias);
         $("#attribute_type_update").val(update_attribute.attribute_datatype);
         if (update_attribute.is_single_value === 1)
            $("#attribute_is_single_value_update").val("单值");
         else
             $("#attribute_is_single_value_update").val("多值");
         $("#attribute_describe_update").val(update_attribute.attribute_description);
         let relationship_algorithm_update = $("#relationship_algorithm_update");
         relationship_algorithm_update.val($("#relationship_algorithm_update option[data-id='" + update_attribute.algorithm_id +"']").text());
         if ($("#attribute_type_update > option:selected").attr("data-value") === "-1"){
             $(".relationship_algorithm_update_div").hide();
         } else {
             $(".relationship_algorithm_update_div").show();
         }
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
        $(".attribute_update_form").attr("data-id", "");
    });

	$("#attribute_type").change(function(){
        let attribute_type_category = $("#attribute_type > option:selected").attr("data-value");
        if (attribute_type_category === "-1"){
            $("#relationship_algorithm").val("无");
            $(".relationship_algorithm_div").hide();
        } else {
            $(".relationship_algorithm_div").show();
        }
    });
	$("#attribute_type_update").change(function () {
        let attribute_type_update_category = $("#attribute_type_update > option:selected").attr("data-value");
        if (attribute_type_update_category === "-1"){
            $(".relationship_algorithm_update_div").hide();
        } else {
            $(".relationship_algorithm_update_div").show();
        }

    });
    /**
     * 添加类目
     */
    $("#add_category").click(function () {
    	let category_name = $("#category_name").val();
        let inherit_category = $("#inherit_category option:checked").attr("data-id");
        let category_describe = $("#category_describe").val();
        if (category_name.match(/^[ ]*$/)) {
            console.log("all space or empty");
            alert("类目名称不可为空！");
            return;
        }
        let flag = -1;
        $(".category").each(function () {
            if ($(this).html() === category_name){
                flag = $(this).attr("id");
            }
        })
        if (flag !== -1){
            alert("同一个知识库中不允许创建同名类目！")
            return;
        }
        $.post('/index/add_category',
            {
                category_name: category_name,
                inherit_category: inherit_category,
                category_describe: category_describe
            },
            function (data){
                if(data.status === 'success'){
                    let new_category = data.msg;
                    console.log(new_category);
                    console.log(new_category.category_level === 2);
                    if (new_category.category_level === 2){
                        var sub_category = $(".sub-category" + new_category.category_type);
                        var new_category_li = $("<li></li>");
                        var new_category_div = $("<div></div>");
                        new_category_div.appendTo(new_category_li);
                        $("<span class=\"second-title\">\n" +
                            "<i class=\"glyphicon glyphicon-chevron-right myicon\" style=\"font-size: 15px;color: #337ab7;display: none;\"></i>\n" +
                            "<i class=\"glyphicon glyphicon-chevron-down myicon\" style=\"font-size: 15px;color: #337ab7;\"></i>\n" +
                            "</span>").appendTo(new_category_div);
                        $("<span class=\"category\" id='" + new_category.id + "'>" + new_category.category_name + "</span>").appendTo(new_category_div);
                        $("<dl class=\"three-wrapper\" style=\"display: block;\"></dl>").appendTo(new_category_li);
                        new_category_li.appendTo(sub_category);
                        var inherit_category = $("#inherit_category");
                        $("<option data-id='" + new_category.id + "'>" + new_category.category_name + "</option>").appendTo(inherit_category);
                    } else if (new_category.category_level === 3){
                        var three_wrapper_dl = $("#" + new_category.father_category_id).parent().parent().find(".three-wrapper");
                        $("<dd class=\"category\" id='" + new_category.id + "'>" + new_category.category_name + "</dd>").appendTo(three_wrapper_dl);
                    }
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
        let category_id = $("#category_name_show").attr("data-id");
        let attribute_name = $("#attribute_name").val();
        let attribute_alias = $("#attribute_alias").val();
        let attribute_type_id = $("#attribute_type > option:selected").attr("data-id");
        let attribute_is_single_value = $("#attribute_is_single_value > option:selected").attr("data-id");
        let attribute_describe = $("#attribute_describe").val();
        let algorithm_id = $("#relationship_algorithm > option:selected").attr("data-id");

        if (attribute_name.match(/^[ ]*$/)) {
            console.log("all space or empty");
            alert("属性名称不可为空！");
            return;
        }
        let flag = -1;
        $(".attribute_name_show").each(function () {
            if ($(this).html() === attribute_name){
                flag = $(this).attr("id");
            }
        })
        if (flag !== -1){
            alert("同一个类目中不允许创建同名属性！")
            return;
        }
        $.post('/index/add_attribute',
            {
                category_id: category_id,
                attribute_name: attribute_name,
                attribute_alias: attribute_alias,
                attribute_type_id: attribute_type_id,
                attribute_is_single_value: attribute_is_single_value,
                attribute_describe: attribute_describe,
                algorithm_id: algorithm_id
            },
            function (data){
                if(data.status === 'success'){
                    alert("属性添加成功！");
                    var new_attribute = data.msg;
                    var attribute_tbody = $(".attribute_tbody");
                    var new_attribute_tr = $("<tr class='attribute_info_tr' data-id='" + new_attribute.id + "'></tr>");
                    $("<td>" + new_attribute.attribute_name + "</td>").appendTo(new_attribute_tr);
                    if (new_attribute.attribute_alias === "")
                        $("<td>暂无</td>").appendTo(new_attribute_tr);
                    else
                        $("<td data-value='" + new_attribute.attribute_alias + "'>" + new_attribute.attribute_alias + "</td>").appendTo(new_attribute_tr);
                    $("<td>" + new_attribute.attribute_datatype + "</td>").appendTo(new_attribute_tr);
                    if (new_attribute.is_single_value === "1")
                        $("<td>单值</td>").appendTo(new_attribute_tr);
                    else
                        $("<td>多值</td>").appendTo(new_attribute_tr);
                    if (new_attribute.attribute_description === "")
                        $("<td>暂无</td>").appendTo(new_attribute_tr);
                    else
                        $("<td data-value='" + new_attribute.attribute_description + "'>" + new_attribute.attribute_description + "</td>").appendTo(new_attribute_tr);
                    $("<td>" + new_attribute.create_time + "</td>").appendTo(new_attribute_tr);
                    $("<td><input type='button' class='btn btn-default' value='修改'' data-toggle='modal' data-target='#myModal2'/><input type='button' class='btn btn-default delete_attribute' value='删除'/></td>").appendTo(new_attribute_tr);
                    new_attribute_tr.appendTo(attribute_tbody);
                    // window.location.href = '/index/homepage';
                    $("#attribute_name").val("");
                    $("#attribute_alias").val("");
                    $("#attribute_type").first().attr("selected", true);
                    $("#attribute_is_single_value").first().attr("selected", true);
                    $("#attribute_describe").val("");
                    $("#attribute_table_no_data_div").css("display", "none");
                }else{
                    alert(data.msg);
                }
                $("#myModal").modal("hide");
            }
        )
    });
    /**
     * 更新属性
     */
    $("#attribute_update").click(function () {
        let attribute_id = $(".attribute_update_form").attr("data-id");
        let attribute_name = $("#attribute_name_update").val();
        let attribute_alias = $("#attribute_alias_update").val();
        let attribute_type = $("#attribute_type_update").val();
        let attribute_type_id = $("#attribute_type_update > option:selected").attr("data-id");
        let attribute_is_single_value = $("#attribute_is_single_value_update > option:selected").attr("data-id");
        let attribute_algorithm_id = $("#relationship_algorithm_update > option:selected").attr("data-id");
        console.log(attribute_algorithm_id);
        let attribute_describe = $("#attribute_describe_update").val();
        $.post('/index/update_attribute',
            {
                attribute_id: attribute_id,
                attribute_name: attribute_name,
                attribute_alias: attribute_alias,
                attribute_type_id: attribute_type_id,
                attribute_is_single_value: attribute_is_single_value,
                attribute_algorithm_id: attribute_algorithm_id,
                attribute_describe: attribute_describe
            },
            function (data){
                if(data.status === 'success'){
                    for (let i in cur_attribute){
                        if (cur_attribute[i].id === parseInt(attribute_id)){
                            cur_attribute[i].attribute_name = attribute_name;
                            cur_attribute[i].attribute_alias = attribute_alias;
                            cur_attribute[i].data_type_id = parseInt(attribute_type_id);
                            cur_attribute[i].datatype = attribute_type;
                            cur_attribute[i].is_single_value = parseInt(attribute_is_single_value);
                            cur_attribute[i].algorithm_id = parseInt(attribute_algorithm_id);
                            cur_attribute[i].attribute_description = attribute_describe;
                            break;
                        }
                    }
                    alert(data.msg);
                    let update_tr = $(".attribute_tbody").find("tr[data-id='" + attribute_id + "']");
                    update_tr.find("td").eq(0).html(attribute_name);
                    if (attribute_alias === "")
                        update_tr.find("td").eq(1).html("暂无");
                    else
                        update_tr.find("td").eq(1).html(attribute_alias);
                    update_tr.find("td").eq(2).html(attribute_type);
                    if (attribute_is_single_value === "1")
                        update_tr.find("td").eq(3).html("单值");
                    else
                        update_tr.find("td").eq(3).html("多值");
                    if (attribute_describe === "")
                        update_tr.find("td").eq(4).html("暂无");
                    else
                        update_tr.find("td").eq(4).html(attribute_describe);

                }else{
                    alert(data.msg);
                }
                $("#myModal2").modal("hide");
            }
        )
    });
    /**
     * 删除属性
     */
    $(".attribute_tbody").on("click", ".delete_attribute", function(){
        var attribute_id = $(this).parent().parent().attr("data-id");
        $.post('/index/delete_attribute',
            {
                attribute_id: attribute_id,
            },
            function (data){
                console.log(data);
                if(data.status === 'success'){
                    $(".attribute_info_tr[data-id='" + attribute_id + "']").remove();
                    if ($(".attribute_tbody").children().length === 0){
                        $("#attribute_table_no_data_div").css("display", "block");
                    }
                    alert(data.msg);
                    // window.location.href = '/index/homepage';
                }else{
                    alert(data.msg);
                }
            }
        )
    });
    /**
     * 类目具体内容查询
     */
    $("#container1").on("click", ".category", function(){
        var category_id = $(this).attr("id");

        $.post('/index/category_query',
            {
                category_id: category_id,
            },
            function (data){
                if(data.status === 'success'){
                    let father_category = data.msg.father_category;
                    let cur_category = data.msg.category;
                    let data_type = data.msg.data_type;
                    let attribute_type = $("#attribute_type");
                    attribute_type.children().remove();
                    let attribute_type_update = $("#attribute_type_update");
                    attribute_type_update.children().remove();
                    for (let i in data_type){
                        $("<option data-value='" + data_type[i].category_id + "' data-id='" + data_type[i].datatype_id + "'>" + data_type[i].datatype_name + "</option>").appendTo(attribute_type);
                        $("<option data-value='" + data_type[i].category_id + "' data-id='" + data_type[i].datatype_id + "'>" + data_type[i].datatype_name + "</option>").appendTo(attribute_type_update);
                    }

                    let relationship_extract_algorithm = data.msg.relationship_extract_algorithm;
                    let relationship_algorithm = $("#relationship_algorithm");
                    let relationship_algorithm_update = $("#relationship_algorithm_update");
                    relationship_algorithm.children().not(":first").remove();
                    relationship_algorithm_update.children().not(":first").remove();
                    for (let i in relationship_extract_algorithm){
                        $("<option data-id='" + relationship_extract_algorithm[i].id + "'>" + relationship_extract_algorithm[i].algorithm_name + "</option>").appendTo(relationship_algorithm);
                        $("<option data-id='" + relationship_extract_algorithm[i].id + "'>" + relationship_extract_algorithm[i].algorithm_name + "</option>").appendTo(relationship_algorithm_update);
                    }

                    //更改类目基础信息（类目名、描述）
                    $("#category_name_show").html(cur_category.category_name);
                    $("#category_name_show").attr("data-id", category_id);
                    if(cur_category.category_description === null || cur_category.category_description === ""){
                        $("#category_describe_show").html("暂无");
                    } else {
                        $("#category_describe_show").html(cur_category.category_description);
                    }
                    //当是事件时，显示规则模块，并更新当前数据
                    if (cur_category.category_type === 2 && cur_category.id !== 2){
                        let object_category_list = data.msg.event_rule.object_category_list;
                        let rule_detail = data.msg.event_rule.rule_detail;
                        let algorithm_list = data.msg.event_rule.algorithm_list;

                        let event_subject = $("#event_subject");
                        event_subject.children().remove();
                        $("<option data-id='-1'>无</option>").appendTo(event_subject);
                        for (let i in object_category_list){
                            if (object_category_list[i].category_id === rule_detail.event_subject_id)
                                $("<option data-id='" + object_category_list[i].category_id + "' selected>" +
                                    object_category_list[i].category_name + "</option>").appendTo(event_subject);
                            else
                                $("<option data-id='" + object_category_list[i].category_id + "'>" +
                                    object_category_list[i].category_name + "</option>").appendTo(event_subject);
                        }

                        let event_object = $("#event_object");
                        event_object.children().remove();
                        $("<option data-id='-1'>无</option>").appendTo(event_object);
                        for (let i in object_category_list){
                            if (object_category_list[i].category_id === rule_detail.event_object_id)
                                $("<option data-id='" + object_category_list[i].category_id + "' selected>" +
                                    object_category_list[i].category_name + "</option>").appendTo(event_object);
                            else
                                $("<option data-id='" + object_category_list[i].category_id + "'>" +
                                    object_category_list[i].category_name + "</option>").appendTo(event_object);
                        }

                        let event_algorithm = $("#event_algorithm");
                        event_algorithm.children().not(":first").remove();
                        for(let i in algorithm_list){
                            if (rule_detail.algorithm_id === algorithm_list[i].id)
                                $("<option data-id='" + algorithm_list[i].id + "' selected>" +
                                        algorithm_list[i].algorithm_name + "</option>").appendTo(event_algorithm);
                            else
                                $("<option data-id='" + algorithm_list[i].id + "'>" +
                                        algorithm_list[i].algorithm_name + "</option>").appendTo(event_algorithm);
                        }

                        let trigger_word_div = $(".trigger-word-div");
                        trigger_word_div.children().remove();
                        let new_trigger_word = $("<input class=\"trigger_word\" data-role='tags-input' value='" + rule_detail.trigger_word_list + "' />");
                        new_trigger_word.appendTo(trigger_word_div);
                        new_trigger_word.tagsInput();
                        $(".event_rule_define_div").css('display', '');
                    } else {
                        $(".event_rule_define_div").css('display', 'none');
                    }
                    //基础类目隐藏添加属性、规则的操作
                    if(category_id === "1" || category_id === "2"){
                        $(".add_attribute_div").css('display','none');
                        $(".attribute_operation").css('display','none');

                    } else {
                        $(".add_attribute_div").css('display','');
                        $(".attribute_operation").css('display','');
                    }
                    //动态更新当前自有属性表的内容
                    var attribute_tbody = $(".attribute_tbody");
                    attribute_tbody.children().remove();
                    attribute_tbody.parent().parent().children().not(":first").remove();
                    cur_attribute = cur_category.attribute;
                    for (var i in cur_category.attribute){
                        var attribute_tr = $("<tr class='attribute_info_tr' data-id='" + cur_category.attribute[i].id + "'></tr>");
                        attribute_tr.appendTo(attribute_tbody);
                        $("<td class='attribute_name_show'>" + cur_category.attribute[i].attribute_name + "</td>").appendTo(attribute_tr);
                        if (cur_category.attribute[i].attribute_alias === "")
                            $("<td data-value=''>暂无</td>").appendTo(attribute_tr);
                        else
                            $("<td data-value='" + cur_category.attribute[i].attribute_alias + "'>" + cur_category.attribute[i].attribute_alias + "</td>").appendTo(attribute_tr);
                        $("<td>" + cur_category.attribute[i].attribute_datatype + "</td>").appendTo(attribute_tr);
                        if(cur_category.attribute[i].is_single_value === 1){
                            $("<td>单值</td>").appendTo(attribute_tr);
                        } else {
                            $("<td>多值</td>").appendTo(attribute_tr);
                        }
                        if (cur_category.attribute[i].attribute_description === "")
                            $("<td>暂无</td>").appendTo(attribute_tr);
                        else
                            $("<td data-value='" + cur_category.attribute[i].attribute_description + "'>" + cur_category.attribute[i].attribute_description + "</td>").appendTo(attribute_tr);
                        $("<td>" + cur_category.attribute[i].create_time + "</td>").appendTo(attribute_tr);
                        if (category_id !== "1" && category_id !== "2")
                            $("<td><input type='button' class='btn btn-default' value='修改'' data-toggle='modal' data-target='#myModal2'/><input type='button' class='btn btn-default delete_attribute' value='删除'/></td>").appendTo(attribute_tr);
                    }

                    var attribute_div = attribute_tbody.parent().parent();
                    if (cur_category.attribute.length === 0){
                        $("<div class=\"no_data_div\" id='attribute_table_no_data_div'>暂无数据</div>").appendTo(attribute_div);
                    } else {
                        $("<div class=\"no_data_div\" id='attribute_table_no_data_div' style='display: none;'>暂无数据</div>").appendTo(attribute_div);
                    }
                    //动态更新继承自父类的属性
                    var father_attribute_tables = $(".father_attribute_tables");
                    father_attribute_tables.children().not(":first").remove();
                    for (var i in father_category){
                        $("<div class='row father_attribute_title'>" + father_category[i].category_name + "</div>").appendTo(father_attribute_tables);
                        var father_attribute_div = $("<div class=\"row\"></div>");
                        father_attribute_div.appendTo(father_attribute_tables);
                        var father_attribute_table = $("<table class=\"table table-striped table-hover\"></table>");
                        father_attribute_table.appendTo(father_attribute_div);
                        $("<thead><tr><th>属性名称</th><th>属性别称</th><th>属性类型</th><th>单/多值</th><th>描述</th>" +
                            "<th>创建时间</th></tr></thead>").appendTo(father_attribute_table);
                        var father_attribute_tbody = $("<tbody></tbody>");
                        father_attribute_tbody.appendTo(father_attribute_table);
                        for (var j in father_category[i].attribute){
                            var father_attribute_tr = $("<tr></tr>");
                            father_attribute_tr.appendTo(father_attribute_tbody);
                            $("<td class='attribute_name_show'>" + father_category[i].attribute[j].attribute_name + "</td>").appendTo(father_attribute_tr);
                            if (father_category[i].attribute[j].attribute_alias === "")
                                $("<td>暂无</td>").appendTo(father_attribute_tr);
                            else
                                $("<td>" + father_category[i].attribute[j].attribute_alias + "</td>").appendTo(father_attribute_tr);
                            $("<td>" + father_category[i].attribute[j].attribute_datatype + "</td>").appendTo(father_attribute_tr);
                            if(father_category[i].attribute[j].is_single_value === 1){
                                $("<td>单值</td>").appendTo(father_attribute_tr);
                            } else {
                                $("<td>多值</td>").appendTo(father_attribute_tr);
                            }
                            if (father_category[i].attribute[j].attribute_description === "")
                                $("<td>暂无</td>").appendTo(father_attribute_tr);
                            else
                                $("<td>" + father_category[i].attribute[j].attribute_description + "</td>").appendTo(father_attribute_tr);
                            $("<td>" + father_category[i].attribute[j].create_time + "</td>").appendTo(father_attribute_tr);
                        }

                        if (father_category[i].attribute.length === 0){
                            $("<div class=\"no_data_div\">暂无数据</div>").appendTo(father_attribute_div);
                        }
                    }
                    // window.location.href = '/index/homepage';
                }else{
                    alert(data.msg);
                }
                $("#myModal").modal("hide");
            }
        )
    });
    /**
     * 保存类目规则
     */
    $(".save_eveny_rule").click(function () {
        let trigger_word = $(".trigger_word").val();
        let event_subject_id = $("#event_subject > option:selected").attr("data-id");
        let event_object_id = $("#event_object > option:selected").attr("data-id");
        let category_id = $("#category_name_show").attr("data-id");
        let event_algorithm_id = $("#event_algorithm > option:selected").attr("data-id");
        $.post('/index/update_event_rule',
            {
                trigger_word: trigger_word,
                event_subject_id: event_subject_id,
                event_object_id: event_object_id,
                category_id: category_id,
                event_algorithm_id: event_algorithm_id
            },
            function (data){
                if(data.status === 'success'){
                    alert(data.msg);
                    // window.location.href = '/index/homepage';
                }else{
                    alert(data.msg);
                }
            }
        )
        // trigger_word.val("test1;test2;test3");
        // let test1 = "test1;test2;test3;";
        // trigger_word.val("test1;test2;test3");
        // console.log(trigger_word.val());
        // let trigger_word_div = $(".trigger-word-div");
        // trigger_word_div.children().remove();
        // let new_trigger_word = $("<input class=\"trigger_word\" data-role='tags-input' value='" + test1 + "' />");
        // new_trigger_word.appendTo(trigger_word_div);
        // new_trigger_word.tagsInput();
    });
});