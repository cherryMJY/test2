$(function () {
    // $(".lcs_wrap").click(function () {
    //     var change = $(this).find("input[type='checkbox']").is(':checked'); //checkbox选中判断
    //     alert(change);
    // });
    $(".category_select").change(function(){
        var select_category_id = $(".category_select > option:selected").attr("data-id");
        $.post('/index/get_cleaning_rule',
            {
                select_category_id: select_category_id,
            },
            function (data){
                if(data.status === 'success'){
                    var cleaning_rule = data.msg.cleaning_rule;
                    var cleaning_rule_tbody = $(".cleaning_rule_tbody");
                    cleaning_rule_tbody.children().remove();
                    for (var i in cleaning_rule){
                        var cleaning_rule_tr = $("<tr></tr>");
                        cleaning_rule_tr.appendTo(cleaning_rule_tbody);
                        $("<td class=\"cleaning_rule_id\">" + cleaning_rule[i].id + "</td>").appendTo(cleaning_rule_tr);
                        $("<td>" + cleaning_rule[i].attribute.attribute_name + "</td>").appendTo(cleaning_rule_tr);
                        $("<td>" + cleaning_rule[i].attribute.attribute_datatype + "</td>").appendTo(cleaning_rule_tr);
                        if(cleaning_rule[i].attribute.is_single_value === 1){
                            $("<td>单值</td>").appendTo(cleaning_rule_tr);
                        } else {
                            $("<td>多值</td>").appendTo(cleaning_rule_tr);
                        }
                        var cleaning_rule_td = $("<td></td>");
                        var cleaning_rule_div = $("<div class=\"form-inline\"></div>");
                        $("<label>自定义</label>").appendTo(cleaning_rule_div);
                        var lcs_wrap = $("<div class=\"lcs_wrap\"></div>");
                        var lcs_switch;
                        if(cleaning_rule[i].is_custom === 1){
                            $("<input type=\"checkbox\" name=\"check-1\" class=\"lcs_check\" autocomplete=\"off\" checked>").appendTo(lcs_wrap);
                            lcs_switch = $("<div class=\"lcs_switch lcs_checkbox_switch lcs_on\"></div>");
                        } else {
                            $("<input type=\"checkbox\" name=\"check-1\" value=\"4\" class=\"lcs_check\" autocomplete=\"off\">").appendTo(lcs_wrap);
                            lcs_switch = $("<div class=\"lcs_switch lcs_checkbox_switch lcs_off\"></div>");
                        }
                        $("<div class=\"lcs_cursor\"></div>").appendTo(lcs_switch);
                        $("<div class=\"lcs_label lcs_label_on\">ON</div>").appendTo(lcs_switch);
                        $("<div class=\"lcs_label lcs_label_off\">OFF</div>").appendTo(lcs_switch);
                        lcs_switch.appendTo(lcs_wrap);
                        lcs_wrap.appendTo(cleaning_rule_div);

                        var is_not_custom_rule_select;
                        if(cleaning_rule[i].is_custom === 1){
                            $("<input type=\"text\" class=\"custom_input form-control\" id=\"attribute_name\"\n" +
                                "placeholder=\"请输入正则表达式\">").appendTo(cleaning_rule_div);
                            is_not_custom_rule_select = $("<select class=\"un_custom_input form-control\" style=\"display:none;\"></select>");
                        } else {
                            $("<input type=\"text\" class=\"custom_input form-control\" id=\"attribute_name\"\n" +
                                "placeholder=\"请输入正则表达式\" style=\"display:none;\">").appendTo(cleaning_rule_div);
                            is_not_custom_rule_select = $("<select class=\"un_custom_input form-control\">");
                        }
                        $("<option data-id='-1'>不清洗</option>").appendTo(is_not_custom_rule_select);
                        if(cleaning_rule[i].attribute.attribute_datatype === "时间"){
                            $("<option data-id='4'>yyyy-MM-dd</option>\n" +
                                "<option data-id='5'>yyyy-MM</option>\n" +
                                "<option data-id='6'>yyyy-MM-dd HH:mm:ss</option>").appendTo(is_not_custom_rule_select);
                        } else if (cleaning_rule[i].attribute.attribute_datatype === "数字"){
                            $("<option data-id='0'>整数</option>\n" +
                                "<option data-id='1'>保留小数点后面1位</option>\n" +
                                "<option data-id='2'>保留小数点后面2位</option>\n" +
                                "<option data-id='3'>保留小数点后面3位</option>").appendTo(is_not_custom_rule_select);
                        }
                        is_not_custom_rule_select.appendTo(cleaning_rule_div);
                        cleaning_rule_div.appendTo(cleaning_rule_td);
                        cleaning_rule_td.appendTo(cleaning_rule_tr);
                        $("<td><input type=\"button\" class=\"btn btn-default update_cleaning_rule\" value=\"保存\"/></td>").appendTo(cleaning_rule_tr);
                    }
                }else{
                    alert(data.msg);
                }
            }
        )
    });
    $(".cleaning_rule_tbody").on("click", ".update_cleaning_rule", function(){
        let rule_id = $(this).parent().parent().find(".cleaning_rule_id").html();
        let is_custom = $(this).parent().parent().find("input[type='checkbox']").is(':checked');
        let rule_content;
        let rule_number = 7;
        if (is_custom === true){
            rule_content = $(this).parent().parent().find(".custom_input").val();
        } else {
            rule_content = $(this).parent().parent().find(".un_custom_input > option:selected").val();
            rule_number = $(this).parent().parent().find(".un_custom_input > option:selected").attr("data-id");
        }
        $.post('/index/update_cleaning_rule',
            {
                rule_id: rule_id,
                is_custom: is_custom,
                rule_content: rule_content,
                rule_number: rule_number
            },
            function (data){
                console.log(data);
                if(data.status === 'success'){
                    alert(data.msg);
                    // window.location.href = '/index/homepage';
                }else{
                    alert(data.msg);
                }
            }
        )
    });
    // $(".cleaning_rule_tbody").on("click", ".update_cleaning_rule", function(){
    //     var is_custom = $(this).parent().parent().find("input[type='checkbox']").is(':checked');
    //     alert(is_custom);
    //     var cleaning_rule_tbody = $(".cleaning_rule_tbody");
    //     var cleaning_rule_tr = $("<tr></tr>");
    //     cleaning_rule_tr.appendTo(cleaning_rule_tbody);
    //     $("<td class=\"cleaning_rule_id\">1</td>").appendTo(cleaning_rule_tr);
    //     $("<td>attribute_name</td>").appendTo(cleaning_rule_tr);
    //     $("<td>attribute_datatype</td>").appendTo(cleaning_rule_tr);
    //     $("<td>单值</td>").appendTo(cleaning_rule_tr);
    //     $("<td>\n" +
    //         "                                <div class=\"form-inline\">\n" +
    //         "                                    <label>自定义</label>\n" +
    //         "                                    <div class=\"lcs_wrap\">\n" +
    //         "                                        <input type=\"checkbox\" name=\"check-1\" value=\"4\" class=\"lcs_check\" autocomplete=\"off\">\n" +
    //         "                                        <div class=\"lcs_switch  lcs_checkbox_switch lcs_off\">\n" +
    //         "                                            <div class=\"lcs_cursor\"></div>\n" +
    //         "                                            <div class=\"lcs_label lcs_label_on\">ON</div>\n" +
    //         "                                            <div class=\"lcs_label lcs_label_off\">OFF</div>\n" +
    //         "                                        </div>\n" +
    //         "                                    </div>\n" +
    //         "                                    <input type=\"text\" class=\"custom_input form-control\" id=\"attribute_name\"\n" +
    //         "                                                   placeholder=\"请输入正则表达式\" style=\"display:none;\">\n" +
    //         "                                    <select class=\"un_custom_input form-control\">\n" +
    //         "                                        <option>不清洗</option>\n" +
    //         "                                    </select>\n" +
    //         "                                </div>\n" +
    //         "                            </td>").appendTo(cleaning_rule_tr);
    //     $("<td>\n" +
    //         "                                  <input type=\"button\" class=\"btn btn-default update_cleaning_rule\" value=\"保存\"/>\n" +
    //         "                              </td>").appendTo(cleaning_rule_tr);
    // });
    // $(".lcs_wrap").on("change", function () {
    //     alert("111");
    //     var change = $("input[type='checkbox']").is(':checked'); //checkbox选中判断
    //     alert(change);
    //     if (change) {
    //
    //         $("#SureBtn").css("display", "block");
    //         $("#SureBtn").click(function () {
    //             var str = $(" input[name='WorkYears']").val();
    //             alert($("input[name='Agreements']").is(':checked'));
    //         })
    //     } else {
    //         $("#SureBtn").css("display", "none");
    //         return false;
    //     }
    // });
});