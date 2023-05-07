function edit_post(post_id)
{
    if (get_token() == null)
    {
        return;
    }
    
    // send auth token and message id, make sure the user is who they say they are
    data = new Object();
    data.post_id = post_id;

    $.ajax(
    {
        type: "GET",
        url: "/post/edit/begin/" + post_id,
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
                {
                    start_edit(post_id);
                }
            }
        },
        error: function(xhr, status, error)
        {
            alert("Failed to start edit");
        }
    })
}

function start_edit(post_id)
{
    var post_content = $("#post-content-" + post_id).get(0);
    var post_parent = post_content.parentElement;
    var post_content_text = post_content.innerHTML;

    var textArea = document.createElement("textarea");
    textArea.id = "edit-post-content-" + post_id;
    textArea.style = "width: 98%;margin-right: 16px;margin-bottom: 16px;margin-left: 12px;min-height: 150px;background: rgba(255,255,255,0);border-color: rgb(176,189,211);padding-left: 12px;padding-top: 12px;color: rgb(255,255,255);";
    
    textArea.value = post_content_text;
    post_parent.insertBefore(textArea, post_content.nextSibling);

    post_content.remove();

    var options = $("#options-" + post_id);
    options.hide();

    var edit_options = $("#edit-options-" + post_id);
    var edit_options_element = edit_options.get(0);

    edit_options_element.querySelector(".done").href = "javascript:end_edit(" + post_id + ")";
    edit_options.show();
}

function end_edit(post_id)
{
    if (get_token() == null)
    {
        return;
    }
    
    // send auth token and message id, make sure the user is who they say they are
    data = new Object();
    var edit_post_content = $("#edit-post-content-" + post_id).get(0).value;

    if (get_stripped_string(edit_post_content).length < 5)
    {
        alert("Your edit is too short, it must be 5 characters or more");
        return;
    }

    data.content = edit_post_content;

    $.ajax(
    {
        type: "POST",
        url: "/post/edit/end/" + post_id,
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
            if (json.hasOwnProperty('action'))
            {
                if (json["action"] == 1)
                {
                    close_edit(post_id, null);
                }
            }
            else
            {
                alert(json["response"]);
            }
        },
        error: function(xhr, status, error)
        {
            alert("Connection Error: Failed to edit post");
        }
    })
}

function cancel_edit(post_id)
{
    $.ajax(
    {
        type: "GET",
        url: "/post/edit/cancel/" + post_id,
        dataType: 'json',
        success: function(response)
        {
            const json = JSON.parse(JSON.stringify(response));
            close_edit(post_id, json["post_content"]);
        },
        error: function(xhr, status, error)
        {
            console.log("Failed");
        }
    })
}

function close_edit(post_id, content)
{
    var edit_post_content = $("#edit-post-content-" + post_id).get(0);
    var edit_post_parent = edit_post_content.parentElement;
    var edit_post_content_text = content == null ? edit_post_content.value : content;

    var p = document.createElement("p");
    p.id = "post-content-" + post_id;
    p.style = "color: rgb(255,255,255);margin-top: 16px;margin-right: 16px;margin-bottom: 16px;margin-left: 12px;";

    p.innerHTML = edit_post_content_text;
    edit_post_parent.insertBefore(p, edit_post_content.nextSibling);
    
    edit_post_content.remove();

    var options = $("#options-" + post_id);
    options.show();
    var edit_options = $("#edit-options-" + post_id);
    edit_options.hide();
}