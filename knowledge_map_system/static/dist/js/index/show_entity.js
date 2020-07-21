$(function () {
    graph_query_base_info = NaN;
    var myChart = echarts.init(document.getElementById('main'));
    /***
     * 关系图节点点击事件
     */
    myChart.on('click', function (param){
        // console.log('param---->', param);  // 打印出param, 可以看到里边有很多参数可以使用
        // //获取节点点击的数组序号
        // var arrayIndex = param.dataIndex;
        // console.log('arrayIndex---->', arrayIndex);
        // console.log('name---->', param.name);
        if (param.dataType === 'node') {
            let entity_id = param.value;
            $.post('/index/query_entity_info',
                {
                    entity_id: entity_id,
                },
                function (data){
                    if(data.status === 'success'){
                        let entity_info = data.msg;
                        $(".entity_info").attr("id", entity_info.id);
                        $(".category_name").html(entity_info.category_name);
                        $(".entity_name").html(entity_info["名字"]);
                        $(".entity_id").html(entity_info._id);
                        let entity_info_body = $("#entity_info_body");
                        entity_info_body.children().remove();
                        let other_attribute = entity_info.other;
                        for (let key in other_attribute){
                            $("<p><span class='item_key'>" + key + "</span>:<span class='item_value'>" + other_attribute[key] +"</span></p>").appendTo(entity_info_body);
                        }
                        $("#entity_info_head").css("display", "block");
                        entity_info_body.css("display", "block");

                        // 更新时间轴内容
                        let swiper_wrapper = $(".swiper-wrapper");
                        let event_list = data.msg.event;

                        swiper_wrapper.children().remove();
                        console.log(event_list);
                        for (let i=0;i < event_list.length;i++)
                        {
                            let item_li;
                            if (i === event_list.length - 1)
                                item_li = $("<li class=\"features-item swiper-slide dark\"></li>");
                            else
                                item_li = $("<li class=\"features-item swiper-slide\"></li>");
                            $("<h3>" + event_list[i]["发生时间"] + "</h3><i></i>").appendTo(item_li);
                            $("<a class=\"features-info\">\n" +
                                "<p class=\"features-info-i\"></p>\n" +
                                "<p class=\"features-info-s\">" + event_list[i]["名字"] + "</p>\n" +
                                "</a>").appendTo(item_li);
                            item_li.appendTo(swiper_wrapper);
                        }

                        //更新折线图方框内容
                        graph_query_base_info = data.msg.category;
                        let link_category = $("#link_category");
                        link_category.children().remove();
                        let abscissa = $("#abscissa");
                        abscissa.children().remove();
                        let ordinate = $("#ordinate");
                        ordinate.children().remove();
                        for (let i=0;i<graph_query_base_info.length;i++){
                            $("<option data-id='" + graph_query_base_info[i].category_id + "'>" + graph_query_base_info[i].category_name + "</option>").appendTo(link_category);
                            if (i === 0){
                                let attribute_list = graph_query_base_info[i].attribute;
                                for (let j=0;j<attribute_list.length;j++){
                                    $("<option data-id='" + attribute_list[j]["id"] + "'>" + attribute_list[j]["attribute_name"] + "</option>").appendTo(abscissa);
                                    $("<option data-id='" + attribute_list[j]["id"] + "'>" + attribute_list[j]["attribute_name"] + "</option>").appendTo(ordinate);
                                }
                            }
                        }
                        var line = echarts.init(document.getElementById('line'));
                        line.setOption({
                            //data.msg.date
                            title: {
                                x: 'left',
                                text: "",
                                textStyle: {
                                    fontSize: '25',
                                    color: '#000',
                                    fontWeight: 'bolder'
                                }
                            },
                            xAxis:{data:[]},
                            series:[{name:"",data:[]}]
                        });
                    }else{
                        alert(data.msg);
                    }
                }
            )
            // alert("ID" + param.value);
        } else {
            // alert("点击了边" + param.name)
            // alert("value" + param.value);
        }
    });
    /***
     * 关联类目改变事件
     */
    $("#link_category").change(function () {
        let cur_link_category = parseInt($("#link_category > option:selected").attr("data-id"));
        for (let i=0;i<graph_query_base_info.length;i++){
            if (graph_query_base_info[i].category_id === cur_link_category){
                let abscissa = $("#abscissa");
                abscissa.children().remove();
                let ordinate = $("#ordinate");
                ordinate.children().remove();
                let attribute_list = graph_query_base_info[i].attribute;
                for (let j=0;j<attribute_list.length;j++){
                    $("<option data-id='" + attribute_list[j]["attribute_id"] + "'>" + attribute_list[j]["attribute_name"] + "</option>").appendTo(abscissa);
                    $("<option data-id='" + attribute_list[j]["attribute_id"] + "'>" + attribute_list[j]["attribute_name"] + "</option>").appendTo(ordinate);
                }
                break;
            }
        }
    });
    /***
     *查询具体类目下所有节点
     */
    $("#category_select").change(function(){
        var select_category_id = $("#category_select > option:selected").attr("data-id");
        $.post('/index/ret_category_all_node',
            {
                category_id: select_category_id,
            },
            function (data){
                if(data.status === 'success'){
                    let nodes = data.msg.nodes;
                    let links = data.msg.links;
                    console.log(nodes);
                    let categories = [];
                    let temp = [];
                    for (let i in nodes){
                        nodes[i]["des"] = nodes[i]["name"];
                        nodes[i]["symbolSize"] = 50;
                        nodes[i]["value"] = nodes[i]["id"];
                        nodes[i]["category"] = parseInt(nodes[i]["category"]);

                        if (temp.indexOf(nodes[i]["category"]) === -1){
                            temp.push(nodes[i]["category"]);
                        }
                    }
                    for (let i in category){
                        if (temp.indexOf(category[i].id) !== -1){
                            categories.push({
                                name:category[i].category_name,
                                id:category[i].id
                            });
                        }
                    }
                    for (let i in nodes){
                        for (let j in categories){
                            if (nodes[i].category === categories[j].id)
                                nodes[i].category = parseInt(j);
                        }
                    }
                    option = {
                        // 图的标题
                        title: {
                            text: '关系图'
                        },
                        // 提示框的配置
                        tooltip: {
                            formatter: function (x) {
                                return x.data.des;
                            }
                        },
                        // 工具箱
                        toolbox: {
                            // 显示工具箱
                            show: true,
                            feature: {
                                mark: {
                                    show: true
                                },
                                // 还原
                                restore: {
                                    show: true
                                },
                                // 保存为图片
                                saveAsImage: {
                                    show: true
                                }
                            }
                        },
                        legend: [{
                            // selectedMode: 'single',
                            data: categories.map(function (a) {
                                return a.name;
                            })
                        }],
                        series: [{
                            type: 'graph', // 类型:关系图
                            layout: 'force', //图的布局，类型为力导图
                            symbolSize: 40, // 调整节点的大小
                            roam: true, // 是否开启鼠标缩放和平移漫游。默认不开启。如果只想要开启缩放或者平移,可以设置成 'scale' 或者 'move'。设置成 true 为都开启
                            edgeSymbol: ['circle', 'arrow'],
                            edgeSymbolSize: [2, 10],
                            edgeLabel: {
                                normal: {
                                    textStyle: {
                                        fontSize: 20
                                    }
                                }
                            },
                            force: {
                                repulsion: 2500,
                                edgeLength: [10, 50]
                            },
                            draggable: true,
                            lineStyle: {
                                normal: {
                                    width: 2,
                                    color: '#4b565b',
                                }
                            },
                            edgeLabel: {
                                normal: {
                                    show: true,
                                    formatter: function (x) {
                                        return x.data.name;
                                    }
                                }
                            },
                            label: {
                                normal: {
                                    show: true,
                                    textStyle: {}
                                }
                            },

                            // 数据
                            data: nodes,
                            links: links,
                            categories: categories,
                        }]
                    };
                    myChart.setOption(option);
                }else{
                    alert(data.msg);
                }
            }
        )
    });
    /***
     *动态更改模态框内容
     */
    $(".modify_entity_info").click(function () {
        let entity_id = $(".entity_id").html();
        let entity_name = $(".entity_name").html();
        let entity_category = $(".category_name").html();
        let base_info = $("#entity_info_body").children();
        let update_entity_form = $(".update_entity_form");
        update_entity_form.children().remove();
        $("<div class=\"form-group\">\n" +
            "<label class=\"col-sm-2 control-label\">类目名</label>\n" +
            "<label class=\"col-sm-10 control-label fixed_info\">" + entity_category + "</label>\n" +
            "</div>").appendTo(update_entity_form);
        $("<div class=\"form-group\">\n" +
            "<label class=\"col-sm-2 control-label\">实体名</label>\n" +
            "<label class=\"col-sm-10 control-label fixed_info\">" + entity_name + "</label>\n" +
            "</div>").appendTo(update_entity_form);
        $("<div class=\"form-group\">\n" +
            "<label class=\"col-sm-2 control-label\">实体ID</label>\n" +
            "<label class=\"col-sm-10 control-label fixed_info update_entity_id\">" + entity_id + "</label>\n" +
            "</div>").appendTo(update_entity_form);
        for (let i=0;i<base_info.length;i++){
            let one_attribute_info = $("#entity_info_body > p").eq(i);
            let attribute_key = one_attribute_info.find(".item_key").html();
            let attribute_value = one_attribute_info.find(".item_value").html();
            let form_group = $("<div class='form-group modifiable_info_div'></div>");
            $("<label class=\"col-sm-2 control-label update_attribute_key\">" + attribute_key + "</label>").appendTo(form_group);
            let attribute_value_div = $("<div class='col-sm-10'></div>");
            let attribute_value_textarea = $("<textarea class=\"form-control update_attribute_value\"></textarea>");
            attribute_value_textarea.val(attribute_value);
            attribute_value_textarea.appendTo(attribute_value_div);
            attribute_value_div.appendTo(form_group);
            form_group.appendTo(update_entity_form);
        }
    });

    $("#update_entity").click(function () {
        let entity_id = $(".update_entity_id").html();
        let entity_info = $(".update_entity_form").children(".modifiable_info_div");
        let new_attribute_info = {};
        for (let i=0;i<entity_info.length;i++){
            let current_modifiable_info = $(".update_entity_form > div.modifiable_info_div").eq(i);
            let attribute_key = current_modifiable_info.find(".update_attribute_key").html();
            new_attribute_info[attribute_key] = current_modifiable_info.find(".update_attribute_value").val();
        }
        console.log(new_attribute_info);
    });
    /*
    获取折线图数据
     */
    $(".get_line_infos").click(function () {
        let id = $(".entity_info").attr("id");
        let link_category_id = $("#link_category > option:selected").attr("data-id");
        let ordinate_id = $("#ordinate > option:selected").attr("data-id");
        let abscissa_id = $("#abscissa > option:selected").attr("data-id");
        $.post('/index/acquireGraphInf',
            {
                id: id,
                link_category_id: link_category_id,
                ordinate_id: ordinate_id,
                abscissa_id: abscissa_id
            },
            function (data){
                console.log(data);
                if(data.status === 'success'){
                    let ordinate_name = $("#ordinate > option:selected").html();
                    var line = echarts.init(document.getElementById('line'));
                    let horizontal = data.msg.horizontal;
                    let vertical = data.msg.vertical;
                    let interval = Math.round(horizontal.length / 15);
                    line.setOption({
                        //data.msg.date
                        title: {
                            x: 'left',
                            text: ordinate_name,
                            textStyle: {
                                fontSize: '25',
                                color: '#000',
                                fontWeight: 'bolder'
                            }
                        },
                        xAxis:{data:horizontal,
                            "axisLabel":{interval: interval}
                        },
                        series:[{name:ordinate_name,data:vertical}]
                    });
                    // let swiper_wrapper = $(".swiper-wrapper");
                    // let event_list = data.msg.category;
                    // //console.log(event_list)
                    // // html = '';
                    // swiper_wrapper.children().remove();
                    // for (let i=0;i < event_list.length;i++)
                    // {
                    //     let item_li
                    //     if (i === event_list.length - 1)
                    //         item_li = $("<li class=\"features-item swiper-slide dark\"></li>");
                    //     else
                    //         item_li = $("<li class=\"features-item swiper-slide\"></li>");
                    //     $("<h3>" + event_list[i].date + "</h3><i></i>").appendTo(item_li);
                    //     $("<a class=\"features-info\">\n" +
                    //         "<p class=\"features-info-i\"></p>\n" +
                    //         "<p class=\"features-info-s\">" + event_list[i].event + "</p>\n" +
                    //         "</a>").appendTo(item_li);
                    //     item_li.appendTo(swiper_wrapper);
                    //     // console.log(event_list[i].event);
                    //     // console.log(event_list[i].date);
                    //     // $("<tr />").append("<td>陈希章</td><td>100</td>"+).appendTo("#contents");
                    //      //       $("<ul class=\"features-slide swiper-wrapper\" id = \"contents\"> /").append("<li class=\"features-item swiper-slide\"><h3>"+event_list[i].date+"</h3><i></i> <a class=\"features-info\"><p class=\"features-info-i\"></p><p class=\"features-info-s\">"+event_list[i].event+"</p></a> </li>").appendTo("#contents");
                    //     //html+=     "<li class=\"features-item swiper-slide\"><h3>"+event_list[i].date+"</h3><i></i> <a class=\"features-info\"><p class=\"features-info-i\"></p><p class=\"features-info-s\">"+event_list[i].event+"</p></a> </li>";
                    //     // html+=     "<li class=\"features-item swiper-slide\"><h3>"+event_list[i].date+"</h3><i></i> <p class=\"features-info-s\">"+event_list[i].event+"</p></a> </li>";
                    //
                    // }
                    // // $(".swiper-button-prev").removeClass("swiper-button-disabled");
                    // // $(".swiper-button-next").addClass("swiper-button-disabled");
                    // // swiper_wrapper.append(html);
                    // // var swiper = new Swiper('.swiper-container', {
                    // //     pagination: '.swiper-pagination',
                    // //     slidesPerView: 'auto',
                    // //     slidesPerView: 3,
                    // //     paginationClickable: true,
                    // //     spaceBetween: 0,
                    // //     initialSlide :0,
                    // //      observer:true,//修改swiper自己或子元素时，自动初始化swiper
                    // //      observeParents:true,//修改swiper的父元素时，自动初始化swiper
                    // //      prevButton: ".swiper-button-prev", //左右按钮
		            // //      nextButton: ".swiper-button-next"
                    // // });
                }else{
                    alert(data.msg);
                }
             }
        );
    });
    /***
     *搜索实体
     */
    $("#entity_search_btn").click(function () {
        let entity_search_text = $("#entity_search_text").val();
        let category_id = $("#category_select > option:selected").attr("data-id");
        console.log(entity_search_text);
        $.post('/index/searchEntity',
            {
                entity_search_text: entity_search_text,
                category_id: category_id
            },
            function (data){
                console.log(data);
                if(data.status === 'success'){
                    console.log(data.msg);
                    let nodes = data.msg.nodes;
                    let links = data.msg.links;
                    let categories = [];
                    let temp = [];
                    for (let i in nodes){
                        nodes[i]["des"] = nodes[i]["name"];
                        nodes[i]["symbolSize"] = 50;
                        nodes[i]["value"] = nodes[i]["id"];
                        nodes[i]["category"] = parseInt(nodes[i]["category"]);

                        if (temp.indexOf(nodes[i]["category"]) === -1){
                            temp.push(nodes[i]["category"]);
                        }
                    }
                    for (let i in category){
                        if (temp.indexOf(category[i].id) !== -1){
                            categories.push({
                                name:category[i].category_name,
                                id:category[i].id
                            });
                        }
                    }
                    for (let i in nodes){
                        for (let j in categories){
                            if (nodes[i].category === categories[j].id)
                                nodes[i].category = parseInt(j);
                        }
                    }
                    option = {
                        // 图的标题
                        title: {
                            text: '关系图'
                        },
                        // 提示框的配置
                        tooltip: {
                            formatter: function (x) {
                                return x.data.des;
                            }
                        },
                        // 工具箱
                        toolbox: {
                            // 显示工具箱
                            show: true,
                            feature: {
                                mark: {
                                    show: true
                                },
                                // 还原
                                restore: {
                                    show: true
                                },
                                // 保存为图片
                                saveAsImage: {
                                    show: true
                                }
                            }
                        },
                        legend: [{
                            // selectedMode: 'single',
                            data: categories.map(function (a) {
                                return a.name;
                            })
                        }],
                        series: [{
                            type: 'graph', // 类型:关系图
                            layout: 'force', //图的布局，类型为力导图
                            symbolSize: 40, // 调整节点的大小
                            roam: true, // 是否开启鼠标缩放和平移漫游。默认不开启。如果只想要开启缩放或者平移,可以设置成 'scale' 或者 'move'。设置成 true 为都开启
                            edgeSymbol: ['circle', 'arrow'],
                            edgeSymbolSize: [2, 10],
                            edgeLabel: {
                                normal: {
                                    textStyle: {
                                        fontSize: 20
                                    }
                                }
                            },
                            force: {
                                repulsion: 2500,
                                edgeLength: [10, 50]
                            },
                            draggable: true,
                            lineStyle: {
                                normal: {
                                    width: 2,
                                    color: '#4b565b',
                                }
                            },
                            edgeLabel: {
                                normal: {
                                    show: true,
                                    formatter: function (x) {
                                        return x.data.name;
                                    }
                                }
                            },
                            label: {
                                normal: {
                                    show: true,
                                    textStyle: {}
                                }
                            },

                            // 数据
                            data: nodes,
                            links: links,
                            categories: categories,
                        }]
                    };
                    myChart.setOption(option);
                }else{
                    alert(data.msg);
                }
             }
        );
    });
});