// function getText(obj) {
//     var word = $(obj).text();
//     var textarea1 = $("#textarea1");
//     var str = textarea1.val() + word.split("/")[0];
//     textarea1.val(str);
// }

$(function () {
    // var test = [];
    // var current_word_id = "";
    // var object1 = "";
    // var key_word = "";
    // var object2 = "";

    var add_word_li = $(".add_word_li");
    add_word_li.click(function () {
        /***
         * 显示添加术语组块，隐藏其他组块
         * @type {jQuery}
         */
        var currentClass = $(this).attr("class");
        var tag = "active";
        if(currentClass.indexOf(tag) === -1){
            $(".active").removeClass("active");
            $(this).addClass("active");

            $(".relationship_textarea").val("");
            $(".event_textarea").val("");
            $(".add_word_div").show();
            $(".add_relationship_div").hide();
            $(".add_event_div").hide();
        }
    });

    var add_relationship_li = $(".add_relationship_li");
    add_relationship_li.click(function(){
        /***
         * 显示添加关系组块，隐藏其他组块
         * @type {jQuery}
         */
        var currentClass = $(this).attr("class");
        var tag = "active";
        if(currentClass.indexOf(tag) === -1){
            $(".active").removeClass("active");
            $(this).addClass("active");

            $(".add_word_textarea").val("");
            $(".event_textarea").val("");
            $(".add_word_div").hide();
            $(".add_relationship_div").show();
            $(".add_event_div").hide();
        }
    });

    let add_event_li = $(".add_event_li");
    add_event_li.click(function () {
        /***
         * 显示添加事件组块。隐藏其他组块
         * @type {jQuery}
         */
        let currentClass = $(this).attr("class");
        let tag = "active";
        if(currentClass.indexOf(tag) === -1){
            $(".active").removeClass("active");
            $(this).addClass("active");

            $(".relationship_textarea").val("");
            $(".add_word_textarea").val("");
            $(".add_word_div").hide();
            $(".add_relationship_div").hide();
            $(".add_event_div").show();
        }
    });
    $.judgeIsUndefined = function(content){
        /***
         * 判断内容是否喂空，若为空返回-1
         */
        if(typeof(content)=="undefined"){
            return -1;
        }
        return content;
    }
    $.updateWordSegmentationResult = function(wordSegmentationResults){
        /***
         * 更新分词结果
         * @type {*|jQuery.fn.init|jQuery|HTMLElement}
         */
        let fenci_content = $("#fenci_content");
        fenci_content.children().not(":first").remove();
        for (let i in wordSegmentationResults){
            let div_row = $("<div class='fenci row'></div>");
            div_row.appendTo(fenci_content);
            $("<p>&nbsp;&nbsp;&nbsp;&nbsp;</p>").appendTo(div_row);
            for (let j in wordSegmentationResults[i]){
                $("<p class='n" + wordSegmentationResults[i][j]["tag"] + " get_text' id='" + wordSegmentationResults[i][j]["num"] + "'>" + wordSegmentationResults[i][j]["word"] + "</p>").appendTo(div_row);
            }
        }
    }
    $.updateRelationshipResult = function(relationship_extract_result_list){
        /***
         * 更新关系抽取结果
         * @type {*|jQuery.fn.init|jQuery|HTMLElement}
         */
        let relationship_extract_result = $(".relationship_extract_result");
        relationship_extract_result.children().remove();
        for (let i in relationship_extract_result_list){
            let one_extract_result_tr = $("<tr></tr>");
            $("<td class='object_from'>" + relationship_extract_result_list[i]["object_from_name"] + "</td>").appendTo(one_extract_result_tr);
            $("<td class='object_event'>" + relationship_extract_result_list[i]["object_relationship_name"] + "</td>").appendTo(one_extract_result_tr);
            $("<td class='object_to'>" + relationship_extract_result_list[i]["object_to_name"] + "</td>").appendTo(one_extract_result_tr);
            $("<td><input type='button' class='btn btn-default' id='delete_relationship_btn' value='删除关系'></td>").appendTo(one_extract_result_tr);
            one_extract_result_tr.appendTo(relationship_extract_result);
        }
    }
    $.updateEventResult = function(event_extract_result_list){
        /***
         * 更新事件表
         * @type {*|jQuery.fn.init|jQuery|HTMLElement}
         */
        let event_extract_result = $(".event_extract_result");
        event_extract_result.children().remove();
        for (let i in event_extract_result_list){
            let one_extract_result_tr = $("<tr></tr>");
            $("<td class='time'>" + event_extract_result_list[i]["actual_event_time"] + "</td>").appendTo(one_extract_result_tr);
            $("<td class='location'>" + event_extract_result_list[i]["location"] + "</td>").appendTo(one_extract_result_tr);
            $("<td class='event_subject'>" + event_extract_result_list[i]["eventSubject"] + "</td>").appendTo(one_extract_result_tr);
            $("<td class='event_name'>" + event_extract_result_list[i]["eventName"] + "</td>").appendTo(one_extract_result_tr);
            if (typeof(event_extract_result_list[i]["eventObject"]) === "undefined")
                $("<td class='event_object'></td>").appendTo(one_extract_result_tr);
            else
                $("<td class='event_object'>" + event_extract_result_list[i]["eventObject"] + "</td>").appendTo(one_extract_result_tr);
            $("<td><input type='button' class='btn btn-default' id='delete_event_btn' value='删除事件'></td>").appendTo(one_extract_result_tr);
            one_extract_result_tr.appendTo(event_extract_result);
        }
    }
    $.updateTagCategory = function(tagCategory){
        /***
         * 更新标签颜色
         * @type {*|jQuery.fn.init|jQuery|HTMLElement}
         */
        let color_label = $(".color-label");
        color_label.children().not(":first").remove();
        for (let i in tagCategory){
            $("<p class='n" + tagCategory[i]["tag"] + "'>" + tagCategory[i]["category"] + "</p>").appendTo(color_label);
            $(".n" + tagCategory[i]["tag"]).css("background-color", "rgb("+rc()+","+rc()+","+rc()+")");
        }
    }
    $("#fenci_content").on("click", ".get_text", function(){
        /***
         * 分词结果标签点击事件，获取目标词和这个词的标号到对应的textarea框里
         * @type {jQuery}
         */
        var current_mod = $(".active").attr("class");
        var word = $(this).text();
        if(current_mod.indexOf("add_word_li") !== -1){
            let added_word = $("#added_word");
            // test = test + word;
            let str = added_word.val() + word;
            added_word.val(str);
        } else if(current_mod.indexOf("add_relationship_li") !== -1){
            let relationship_word = $("#get_relationship_word_textarea");
            relationship_word.val(word);
            relationship_word.attr("data-id", $(this).attr("id"));
        } else if(current_mod.indexOf("add_event_li") !== -1){
            let event_word = $("#get_event_word_textarea");
            event_word.val(word);
            event_word.attr("data-id", $(this).attr("id"));
        }
    });
    var btn_input = $(".btn-input");
    btn_input.click(function () {
        let textarea_input = $(this).parent().parent().find(".textarea-input");
        let cur_word = $(this).parent().parent().parent().parent().find(".get_word_textarea")
        // let textarea2 = $("#textarea2");
        let current_value = cur_word.val();
        let current_num = cur_word.attr("data-id");
        textarea_input.val(current_value);
        textarea_input.attr("data-id", current_num);
        // if ($(this).attr("id") === "btn-input3"){
        //     object1 = current_word_id;
        // } else if ($(this).attr("id") === "btn-input4"){
        //     key_word = current_word_id;
        // } else if ($(this).attr("id") === "btn-input5"){
        //     object2 = current_word_id;
        // }
    });
    // get_text_btn.click(function(){
    //     var word = $(this).text();
    //     var textarea1 = $("#textarea1");
    //
    //     test = test + word;
    //     var str = textarea1.val() + word.split("/")[0];
    //     textarea1.val(str);
    //     // alert(test);
    // });
    var add_relationship = $(".add_relationship");
    add_relationship.click(function(){
        /***
         * 添加关系
         * @type {jQuery}
         */
        let object1_id = $("#object_from_textarea").attr("data-id");
        let relationship_textarea_id = $("#relationship_textarea").attr("data-id");
        let relationship_type = $("#relationship_type > option:selected").attr("data-id");
        let object2_id = $("#object_to_textarea").attr("data-id");
        if (object1_id == "" || relationship_textarea_id == "" || object2_id == ""){
            alert("关系对象不能为空！");
            return;
        }
        // var project_id = $(".panel").attr("id");
        var id = $(".panel-body").attr("id");
        // var time = $(".relationship_time").val();
        $.post('/index/addRelationship',
            {
                id:id,
                object1_id:object1_id,
                object2_id:object2_id,
                key_word_id:relationship_textarea_id,
                relationship_id:relationship_type,
            },
            function (data) {
                if(data.status === 'success'){
                    console.log(data.msg);
                    // let fenci_content = $("#fenci_content");
                    // fenci_content.children().not(":first").remove();
                    // let wordSegmentationResults = data.msg["wordSegmentationResults"];
                    $.updateWordSegmentationResult(data.msg["wordSegmentationResults"]);
                    // for (let i in wordSegmentationResults){
                    //     let div_row = $("<div class='fenci row'></div>");
                    //     div_row.appendTo(fenci_content);
                    //     $("<p>&nbsp;&nbsp;&nbsp;&nbsp;</p>").appendTo(div_row);
                    //     for (let j in wordSegmentationResults[i]){
                    //         $("<p class='n" + wordSegmentationResults[i][j]["tag"] + " get_text' id='" + wordSegmentationResults[i][j]["num"] + "'>" + wordSegmentationResults[i][j]["word"] + "</p>").appendTo(div_row);
                    //     }
                    // }
                    $.updateRelationshipResult(data.msg["relationship_extract_result"]);
                    // let relationship_extract_result = $(".relationship_extract_result");
                    // relationship_extract_result.children().remove();
                    // let relationship_extract_result_list = data.msg["relationship_extract_result"];
                    // for (let i in relationship_extract_result_list){
                    //     let one_extract_result_tr = $("<tr></tr>");
                    //     $("<td class='object_from'>" + relationship_extract_result_list[i]["object_from_name"] + "</td>").appendTo(one_extract_result_tr);
                    //     $("<td class='object_event'>" + relationship_extract_result_list[i]["object_relationship_name"] + "</td>").appendTo(one_extract_result_tr);
                    //     $("<td class='object_to'>" + relationship_extract_result_list[i]["object_to_name"] + "</td>").appendTo(one_extract_result_tr);
                    //     $("<td><input type='button' class='btn btn-default' id='delete_relationship_btn' value='删除关系'></td>").appendTo(one_extract_result_tr);
                    //     one_extract_result_tr.appendTo(relationship_extract_result);
                    // }
                    $.updateTagCategory(data.msg["tagCategory"]);
                    // let color_label = $(".color-label");
                    // color_label.children().not(":first").remove();
                    // let tagCategory = data.msg["tagCategory"];
                    // for (let i in tagCategory){
                    //     $("<p class='n" + tagCategory[i]["tag"] + "'>" + tagCategory[i]["category"] + "</p>").appendTo(color_label);
                    //     $(".n" + tagCategory[i]["tag"]).css("background-color", "rgb("+rc()+","+rc()+","+rc()+")");
                    // }
                    alert("添加成功！");
                }
            }
        )
    });
    let add_word_btn = $(".add_word");
    add_word_btn.click(function () {
        /***
         * 导入术语
         * @type {jQuery|string|undefined}
         */
        let word = $("#added_word").val();
        let word_type = $("#select_word_type > option:selected").attr("data-id");
        let id = $(".panel-body").attr("id");
        // var project_id = $(".panel").attr("id");
        // alert(test);
        $.post('/index/insertTerm',
            {
                // project_id:project_id,
                id:id,
                word:word,
                word_type:word_type,
            },
            function (data) {
                if(data.status === 'success'){
                    alert("添加成功！");
                    window.location.reload();
                    // for (var i in data.msg){
                    //     var task_tr = $("<tr></tr>");
                    //     task_tr.appendTo(tbody);
                    //      $("<td>" + data.msg[i].c_name + "</td>").appendTo(task_tr);
                    //     $("<td>" + data.msg[i].c_position + "</td>").appendTo(task_tr);
                    //     $("<td>" + data.msg[i].c_major + "</td>").appendTo(task_tr);
                    //      $("<td>" + data.msg[i].c_telephone + "</td>").appendTo(task_tr);
                    //     $("<td>" + data.msg[i].c_email + "</td>").appendTo(task_tr);
                    //     $("<td>" + data.msg[i].c_birthday + "</td>").appendTo(task_tr);
                    //     $("<td>" + data.msg[i].c_time + "</td>").appendTo(task_tr);
                    //     if(data.msg[i].c_status == 1){
                    //         $("<td>成功</td>").appendTo(task_tr);
                    //     } else{
                    //         $("<td>失败</td>").appendTo(task_tr);
                    //     }
                    //     $("<td>" + data.msg[i].c_error + "</td>").appendTo(task_tr);
                    // }
                }
            }
        )
    });

    let add_event = $(".add_event");
    add_event.click(function () {
        /***
         * 添加事件
         * @type {jQuery}
         */
        let id = $(".panel-body").attr("id");
        let event_time_key_word = $.judgeIsUndefined($("#event_time_key_word").attr("data-id"));
        let event_place_key_word = $.judgeIsUndefined($("#event_place_key_word").attr("data-id"));
        let event_subject_key_word = $.judgeIsUndefined($("#event_subject_key_word").attr("data-id"));
        let event_trigger_word = $.judgeIsUndefined($("#event_trigger_word").attr("data-id"));
        let event_object_key_word = $.judgeIsUndefined($("#event_object_key_word").attr("data-id"));
        let actual_event_time = $(".actual_event_time").val();
        let select_event_type = $("#select_event_type > option:selected").attr("data-id");

        $.post('/index/addEvent',
            {
                // project_id:project_id,
                id: id,
                event_time_key_word: event_time_key_word,
                event_place_key_word: event_place_key_word,
                event_subject_key_word: event_subject_key_word,
                event_trigger_word: event_trigger_word,
                event_object_key_word: event_object_key_word,
                actual_event_time: actual_event_time,
                select_event_type: select_event_type
            },
            function (data) {
                if(data.status === 'success'){
                    alert("添加成功！");
                    window.location.reload();
                }
            }
        )
    });

    $("#analysis_relationship_result_table").on("click", "#delete_relationship_btn", function(){
        /***
         * 删除关系
         * @type {jQuery}
         */
        let cur_tr = $(this).parent().parent();
        let index = $(".relationship_extract_result tr").index(cur_tr);
        let id = $(".panel-body").attr("id");
        let object_from = $(this).parent().parent().find(".object_from").text();
        let object_event = $(this).parent().parent().find(".object_event").text();
        let object_to = $(this).parent().parent().find(".object_to").text();

        $.post('/index/deleteRelationship',
            {
                id:id,
                index: index,
                object_from:object_from,
                object_event:object_event,
                object_to:object_to
            },
            function (data) {
                if(data.status === 'success'){
                    $.updateWordSegmentationResult(data.msg["wordSegmentationResults"]);
                    $.updateRelationshipResult(data.msg["relationship_extract_result"]);
                    $.updateTagCategory(data.msg["tagCategory"]);
                    alert("删除成功！");
                    // var fenci_content =  $("#fenci_content");
                    // fenci_content.children().not(":first").remove();
                    // for (var i in data.msg["fenci_result"]){
                    //     var div_row = $("<div class='fenci row'></div>");
                    //     div_row.appendTo(fenci_content);
                    //     $("<p>&nbsp;&nbsp;&nbsp;&nbsp;</p>").appendTo(div_row);
                    //     for (var j in data.msg["fenci_result"][i]){
                    //         $("<p class='n" + data.msg["fenci_result"][i][j]["tag"] + " get_text' id='" + data.msg["fenci_result"][i][j]["num"] + "'>" + data.msg["fenci_result"][i][j]["word"] + "</p>").appendTo(div_row);
                    //     }
                    // }
                    // var extract_result = $(".extract_result");
                    // extract_result.children().remove();
                    // for (var i in data.msg["extract_result"]){
                    //     var one_extract_result_tr = $("<tr></tr>");
                    //     $("<td class='time'>" + data.msg["extract_result"][i]["time"] + "</td>").appendTo(one_extract_result_tr);
                    //     $("<td class='object_from'>" + data.msg["extract_result"][i]["object_from"] + "</td>").appendTo(one_extract_result_tr);
                    //     $("<td class='object_event'>" + data.msg["extract_result"][i]["event"] + "</td>").appendTo(one_extract_result_tr);
                    //     $("<td class='object_to'>" + data.msg["extract_result"][i]["object_to"] + "</td>").appendTo(one_extract_result_tr);
                    //     $("<td><input type='button' class='btn btn-default' id='delete_btn' value='删除关系'></td>").appendTo(one_extract_result_tr);
                    //     one_extract_result_tr.appendTo(extract_result);
                    // }
                    // $("#textarea1").val("");
                } else if(data.status === 'error'){
                    alert(data.msg);
                }
            }
        )
    });

    $("#analysis_event_result_table").on("click", "#delete_event_btn", function(){
        /***
         * 删除事件
         * @type {jQuery}
         */
        let id = $(".panel-body").attr("id");
        let cur_tr = $(this).parent().parent();
        let index = $(".event_extract_result tr").index(cur_tr);
        let time = $(this).parent().parent().find(".time").text();
        let location = $(this).parent().parent().find(".location").text();
        let event_subject = $(this).parent().parent().find(".event_subject").text();
        let event_name = $(this).parent().parent().find(".event_name").text();
        let event_object = $(this).parent().parent().find(".event_object").text();
        $.post('/index/deleteEvent',
            {
                id:id,
                index: index,
                time:time,
                location:location,
                event_subject:event_subject,
                event_name:event_name,
                event_object:event_object
            },
            function (data) {
                if(data.status === 'success'){
                    $.updateWordSegmentationResult(data.msg["wordSegmentationResults"]);
                    $.updateEventResult(data.msg["event_extract_result"]);
                    $.updateTagCategory(data.msg["tagCategory"]);
                    alert("删除成功！");
                } else if(data.status === 'error'){
                    alert(data.msg);
                }
            }
        )
    });
    // var synchronous_btn = $("#synchronous_btn");
    // synchronous_btn.click(function () {
    //     var id = $(".panel-body").attr("id");
    //     var project_id = $(".panel").attr("id");
    //     // alert(test);
    //     $.post('/spider/synchronousdata',
    //         {
    //             project_id:project_id,
    //             id:id,
    //         },
    //         function (data) {
    //             if(data.status === 'success'){
    //                 alert(data.msg);
    //             } else if(data.status === 'error'){
    //                 alert(data.msg);
    //             }
    //         }
    //     )
    // });
});