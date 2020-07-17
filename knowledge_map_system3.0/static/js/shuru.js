$(function () {
    $(".extract_detail").click(function () {

            var a="1";
            var b="2"
            var c="3"
            html  ="<div> class =\" tag badge badge-primary\" <span> " + a +"</span>" + "<i class=\"tag-remove\">✖</i>" +"</div>"+
            "<div> class =\" tag badge badge-primary\" <span> " + b +"</span>" + "<i class=\"tag-remove\">✖</i>" +"</div>"+
            "<div> class =\" tag badge badge-primary\" <span> " + c +"</span>" + "<i class=\"tag-remove\">✖</i>" +"</div>";
            $("#contents").append(html);
            console.log(html)
            console.log(a);
    });
});
