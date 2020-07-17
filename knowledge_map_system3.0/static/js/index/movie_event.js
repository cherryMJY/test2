$(function () {
    $(".extract_detail").click(function () {

        //var log_id = $(this).parent().parent().find(".log_id").html();
        var log_id = 123;
        alert(123);
        $.post('/index/knowledge_test',
            {
                log_id: log_id,
            },
            function (data){
                console.log(data);
                if(data.status === 'success'){
                    event_list = data.msg.category;
                    //console.log(event_list)
                    html = '';
                    for (let i=0;i<event_list.length;i++)
                    {
                        console.log(event_list[i].event);
                        console.log(event_list[i].date);
                        // $("<tr />").append("<td>陈希章</td><td>100</td>"+).appendTo("#contents");
                         //       $("<ul class=\"features-slide swiper-wrapper\" id = \"contents\"> /").append("<li class=\"features-item swiper-slide\"><h3>"+event_list[i].date+"</h3><i></i> <a class=\"features-info\"><p class=\"features-info-i\"></p><p class=\"features-info-s\">"+event_list[i].event+"</p></a> </li>").appendTo("#contents");
                        //html+=     "<li class=\"features-item swiper-slide\"><h3>"+event_list[i].date+"</h3><i></i> <a class=\"features-info\"><p class=\"features-info-i\"></p><p class=\"features-info-s\">"+event_list[i].event+"</p></a> </li>";
                        html+=     "<li class=\"features-item swiper-slide\"><h3>"+event_list[i].date+"</h3><i></i> <p class=\"features-info-s\">"+event_list[i].event+"</p></a> </li>";

                    }
                    $("#contents").append(html);
                    var swiper = new Swiper('.swiper-container', {
                        pagination: '.swiper-pagination',
                        slidesPerView: 'auto',
                        slidesPerView: 4,
                        paginationClickable: true,
                        spaceBetween: 0,
                        initialSlide :0,
                         observer:true,//修改swiper自己或子元素时，自动初始化swiper
                         observeParents:true,//修改swiper的父元素时，自动初始化swiper
                         prevButton: ".swiper-button-prev", //左右按钮
		                 nextButton: ".swiper-button-next"
                    });
                }else{
                    alert(data.msg);
                }
             }

        );


    });
});
