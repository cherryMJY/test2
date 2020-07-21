$(function () {
    /***
     *  添加归一规则
     */
    var attribute;
    $(".add_merging_rule").click(function () {
        var t_body = $(".add_merging_rule_body");
        var t_tr = $("<tr data-id='-1'></tr>");
        var t_attribute_td = $("<td></td>");
        var t_attribute_select = $("<select class=\"form-control\"></select>");
        for (var j in attribute){
            $("<option data-id='" + attribute[j].id + "'>" + attribute[j].attribute_name + "</option>").appendTo(t_attribute_select);
        }
        t_attribute_select.appendTo(t_attribute_td);
        t_attribute_td.appendTo(t_tr);

        var t_type_td = $("<td></td>");
        var t_type_select = $("<select class=\"form-control\"></select>");
        $("<option>字符串</option>").appendTo(t_type_select);
        $("<option>日期</option>").appendTo(t_type_select);
        $("<option>数字</option>").appendTo(t_type_select);
        t_type_select.appendTo(t_type_td);
        t_type_td.appendTo(t_tr);

        var t_similarity_td = $("<td></td>");
        $("<input type=\"text\" class=\"form-control\" id=\"category_name\">").appendTo(t_similarity_td);
        t_similarity_td.appendTo(t_tr);
        $("<td><input type=\"button\" class=\"btn btn-default delect_rule_detail\" value=\"删除\"></td>").appendTo(t_tr);
        t_tr.appendTo(t_body);
    });
    $(".get_normalize_rule_detail").click(function () {
        var merging_rule_id = $(this).parent().parent().find(".merging_rule_id").html();
        var overall_threshold = $(this).parent().parent().find(".overall_threshold").html();
        $.post('/index/get_normalize_rule_detail',
            {
                merging_rule_id: merging_rule_id,
            },
            function (data){
                if(data.status == 'success'){
                    var normalized_rule_detail = data.msg.context;
                    attribute = data.msg.attribute;
                    var t_body = $(".add_merging_rule_body");
                    t_body.children().remove();
                    for (var i in normalized_rule_detail){
                        var t_tr = $("<tr data-id='" + normalized_rule_detail[i].id + "'></tr>");
                        var t_attribute_td = $("<td></td>");
                        var t_attribute_select = $("<select class=\"form-control attribute_select\"></select>");
                        for (var j in attribute){
                            if (normalized_rule_detail[i].attribute_id === attribute[j].id){
                                $("<option data-id='" + attribute[j].id + "' selected='selected'>" + attribute[j].attribute_name + "</option>").appendTo(t_attribute_select);
                            } else {
                                $("<option data-id='" + attribute[j].id + "'>" + attribute[j].attribute_name + "</option>").appendTo(t_attribute_select);
                            }
                        }
                        t_attribute_select.appendTo(t_attribute_td);
                        t_attribute_td.appendTo(t_tr);

                        var t_type_td = $("<td></td>");
                        var t_type_select = $("<select class=\"form-control\"></select>");
                        $("<option>字符串</option>").appendTo(t_type_select);
                        $("<option>日期</option>").appendTo(t_type_select);
                        $("<option>数字</option>").appendTo(t_type_select);
                        t_type_select.appendTo(t_type_td);
                        t_type_td.appendTo(t_tr);

                        var t_similarity_td = $("<td></td>");
                        $("<input type=\"text\" class=\"form-control similarity_threshold\" value='" + normalized_rule_detail[i].similarity_threshold + "'>").appendTo(t_similarity_td);
                        t_similarity_td.appendTo(t_tr);
                        $("<td><input type=\"button\" class=\"btn btn-default delect_rule_detail\" value=\"删除\"></td>").appendTo(t_tr);
                        t_tr.appendTo(t_body);
                    }
                    $("#overall_threshold_update").val(overall_threshold);
                    $(".modal-body").attr("data-id", merging_rule_id);
                }else{
                    alert(data.msg);
                }
            }
        )
    });
    $(".add_merging_rule_body").on("click", ".delect_rule_detail", function(){
        $(this).parent().parent().remove();
    });
    $("#update_merging_rule").click(function () {
        var merging_rules = $(".add_merging_rule_body").children();
        var overall_threshold = $("#overall_threshold_update").val();
        var rule_id = $(".modal-body").attr("data-id");
        var rule_list = [];
        for (var i=0;i<merging_rules.length;i++){
            var one_rule = $(".add_merging_rule_body > tr").eq(i);
            var id = one_rule.attr("data-id");
            var attribute_id = one_rule.find(".attribute_select > option:selected").attr("data-id");
            var similarity_threshold = one_rule.find(".similarity_threshold").val();
            rule_list.push({id:id, attribute_id:attribute_id, similarity_threshold:similarity_threshold});
        }
        $.post('/index/update_merging_rule',
            JSON.stringify({
                rule_id: rule_id,
                overall_threshold: overall_threshold,
                rule_list: rule_list
            }),
            function (data){
                if(data.status == 'success'){
                    alert(data.msg);
                }else{
                    alert(data.msg);
                }
            }
        )
    });
    /**
     * 配置规则模态框关闭事件
     */
    $('#myModal').on('hide.bs.modal', function () {
        var tbody =  $(".add_merging_rule_body");
        tbody.children().remove();
    });
});