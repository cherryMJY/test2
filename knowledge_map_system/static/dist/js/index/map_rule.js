$(function () {
    $("#category_select").change(function(){
        var select_category_id = $("#category_select > option:selected").attr("data-id");
        $.post('/index/get_map_rule',
            {
                category_id: select_category_id,
            },
            function (data){
                if(data.status === 'success'){
                    console.log(data.msg);
                    let attribute = data.msg.attribute;
                    let attribute_mapping = data.msg.attribute_mapping;
                    let attribute_map_tbody = $(".attribute_map_tbody");
                    attribute_map_tbody.children().remove();
                    for (let i in attribute_mapping){
                        let attribute_mapping_rule_tr = $("<tr></tr>");
                        $("<td class=\"map_rule_id\">" + attribute_mapping[i].id + "</td>").appendTo(attribute_mapping_rule_tr);
                        $("<td>" +attribute_mapping[i].attribute_name + "</td>").appendTo(attribute_mapping_rule_tr);
                        $("<td>" + attribute_mapping[i].coverage_rate + "</td>").appendTo(attribute_mapping_rule_tr);
                        let rule_select_td = $("<td></td>");
                        let rule_select = $("<select class=\"form-control map_attribute_id\"></select>");
                        $("<option data-id=\"-1\">不映射</option>").appendTo(rule_select);
                        for (let j in attribute){
                            if (attribute[j].id === attribute_mapping[i].map_attribute_id){
                                $("<option data-id='" + attribute[j].id + "' selected>" + attribute[j].attribute_name + "</option>").appendTo(rule_select);
                            } else {
                                $("<option data-id='" + attribute[j].id + "'>" + attribute[j].attribute_name + "</option>").appendTo(rule_select);
                            }
                        }
                        rule_select.appendTo(rule_select_td);
                        rule_select_td.appendTo(attribute_mapping_rule_tr);
                        $("<td><input type=\"button\" class=\"btn btn-default update_mapping_rule\" value=\"提交\"/></td>").appendTo(attribute_mapping_rule_tr);
                        attribute_mapping_rule_tr.appendTo(attribute_map_tbody);
                    }
                    if (attribute_mapping.length === 0){
                        $(".no_data_div").css("display", "block");
                    } else {
                        $(".no_data_div").css("display", "none");
                    }
                }else{
                    alert(data.msg);
                }
            }
        )
    });

    /**
     * 提交保存映射规则
     */
    $(".attribute_map_tbody").on("click", ".update_mapping_rule", function(){
        var map_rule_id = $(this).parent().parent().find(".map_rule_id").html();
        var map_attribute_id = $(this).parent().parent().find(".map_attribute_id > option:selected").attr("data-id");
        $.post('/index/update_mapping_rule',
            {
                map_rule_id: map_rule_id,
                map_attribute_id: map_attribute_id
            },
            function (data){
                console.log(data);
                if(data.status == 'success'){
                    alert(data.msg);
                    // window.location.href = '/index/homepage';
                }else{
                    alert(data.msg);
                }
            }
        )
    });
});