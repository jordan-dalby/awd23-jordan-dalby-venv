function reply(post_id)
{
    $("#invalid-reply").hide();

    if (get_token() == null)
    {
        return;
    }
    
    data = new Object();
    data.content = $("#post-reply-textarea").val();

    if (get_stripped_string(data.content).length < 5)
    {
        $("#invalid-reply-text").html("&#8226; Content is too short, it must be longer than 5 characters");
        $("#invalid-reply").show();
        return;
    }

    $.ajax(
    {
        type: "POST",
        url: "/post/reply/" + post_id,
        data: JSON.stringify(data),
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
            console.log(json['response']);
            if (json.hasOwnProperty('action'))
            {
                if (json["action"] == 1)
                {
                    window.location.reload();
                }
                else
                {
                    $("#invalid-reply-text").html("&#8226; " + json["response"]);
                    $("#invalid-reply").show();
                }
            }
        },
        error: function(xhr, status, error)
        {
            alert("Connection Error: Failed to post rely")
        }
    })
}