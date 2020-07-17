/**
 * Created by lenovo on 2020/3/21.
 */
$(function () {
    /**
     * 登录
     * @type {any}
     */

    $("#login_form").submit(function () {
        var user = $("#username").val();
        var password = $("#password").val();

        if (user == ""){
        alert("请输入帐号");
        } else if (password == ""){
            alert("请输入密码");
        } else{
            $.post('/index/login',
                {
                    username: user,
                    password: password
                },
                function (data){
                    console.log(data);
                    if(data.status == 'success'){
                        alert(data.msg);
                        window.location.href = '/index/homepage';
                    }else{
                        alert(data.msg);
                    }
                }
            )
        }
        return false;
    });
});