// store user token in browser
function store_token(token)
{
    $.cookie("token", token, { 'path': '/' });
}

// get user token if exists
function get_token()
{
    return $.cookie("token");
}

// log out
function log_out()
{
    $.removeCookie("token", { 'path': "/" });
    window.localStorage.removeItem('username');
    window.localStorage.removeItem('user-id');
    window.location.reload();
}

function get_user_id()
{
    return window.localStorage.getItem('user-id');
}

function get_user_name()
{
    return window.localStorage.getItem('username');
}

admin = false;
function is_admin()
{
    return admin;
}

// on load, check user session token, if none do nothing
$(window).on('pageshow', function()
{
    $('#account-signed-in').hide();

    if (get_token() != null)
    {
        console.log(get_token());
        // if there's a token, ajax request to check if it's valid
        $.ajax( 
        {
            type: "GET",
            url: "/user/token",
            dataType: 'json',
            headers: {
                Authorization: get_token()
            },
            success: function(response)
            {
                const json = JSON.parse(JSON.stringify(response));

                console.log(json["response"]);

                if (json['action'] == 1)
                {
                    // valid token, sign the user in, otherwise they'll have to resign in
                    user_id = json['user_id'];
                    username = json['username'];
                    if (json['admin'] == 1)
                    {
                        admin = true;
                    }

                    set_logged_in(user_id, username);
                }
                else
                {
                    console.log("no action");
                    $('#login-signup-buttons').show();
                }
            },
            error: function(xhr, status, error)
            {
                console.log("Failed");
            }
        })
    }
    else
    {
        console.log("No token");
        $('#login-signup-buttons').show();
    }
});

logged_in = false;
function set_logged_in(user_id, username)
{
    $('#login-signup-buttons').hide();
    $('#account-signed-in').show();

    if (admin)
    {
        $('#account-username').text("Hi, A: " + username);
    }
    else
    {
        $('#account-username').text("Hi, " + username);
    }

    window.localStorage.setItem('user-id', user_id);
    window.localStorage.setItem('username', username);

    logged_in = true;
}