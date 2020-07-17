// JavaScript Document
// echarts
// create for AgnesXu at 20161115


//折线图
var line = echarts.init(document.getElementById('line'));
line.setOption({
    color:["#32d2c9"],
    title: {
        x: 'left',
        text: '票房',
        textStyle: {
            fontSize: '25',
            color: '#000',
            fontWeight: 'bolder'
        }
    },
    tooltip: {
        trigger: 'axis'
    },
    toolbox: {
        show: true,
        feature: {
            dataZoom: {
                yAxisIndex: 'none'
            },
            dataView: {readOnly: false},
            magicType: {type: ['line', 'bar']}
        }
    },
    xAxis:  {
        type: 'category',
        boundaryGap: false,
        //这儿是要改的 每天的数据
        data: ['周一','周二','周三','周四','周五','周六','周日'],
        axisLabel: {
            interval:0,
            rotate:45
        }
    },
    yAxis: {
        type: 'value'
    },
    series: [
        {
            name:'成绩',
            type:'line',
            data:[23, 42, 18, 45, 48, 49,100000000],
            markLine: {data: [{type: 'average', name: '平均值'}]}
        }
    ]
}) ;

//var movie_id = $("#movie_id").val();

        $.ajax({
            url: '/index/acquire_movie_piaofang',
            type: 'post',
            data: {
                'movie_id': 123,
            },
            success: function (arg) {
                console.log(arg);
                line.setOption({
                        //data.msg.date
                        xAxis:{data:arg.msg.date},
                        series:[{name:'销量',data:arg.msg.data}]
                        });
            }
        });




