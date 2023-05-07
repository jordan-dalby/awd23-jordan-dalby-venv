function send_like(id)
{
    if (get_token() == null)
    {
        return;
    }
    
    $.ajax(
    {
        type: "GET",
        url: "/post/like/" + id,
        dataType: 'json',
        headers: {
            ContentType: 'application/json',
            Accepts: 'application/json',
            Authorization: get_token()
        },
        async: true,
        success: function(response)
        {
            const json = JSON.parse(JSON.stringify(response));
            if (json.hasOwnProperty('post_id'))
            {
                if (json['action'] == 1)
                    $("#post-likes-heart-" + json['post_id']).css("color", "rgb(255, 255, 255)");
                else
                    $("#post-likes-heart-" + json['post_id']).css("color", "rgb(176, 189, 211)")
                $("#post-likes-" + json['post_id']).text(json['likes']);
            }
        },
        error: function(xhr, status, error)
        {
            alert("Connection Error: Failed to send like");
        }
    })
}