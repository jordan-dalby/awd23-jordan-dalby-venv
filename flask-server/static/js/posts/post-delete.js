function delete_post(post_id)
{
    if (get_token() == null)
    {
        return;
    }
    
    $.ajax(
    {
        type: "DELETE",
        url: "/post/edit/delete/" + post_id,
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
            if (json.hasOwnProperty('action'))
            {
                if (json["action"] == 1)
                    window.history.back();
                else
                    window.location.reload();
            }
            else
            {
                alert(json["response"]);
            }
        },
        error: function(xhr, status, error)
        {
            alert("Connection Error: Failed to delete post");
        }
    })
}