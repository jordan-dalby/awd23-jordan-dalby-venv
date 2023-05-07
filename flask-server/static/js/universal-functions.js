function change_page(page_name, data)
{
    window.location = page_name + "?" + data
}

// src: https://stackoverflow.com/a/22607328/5232304
function get_url_param(sParam)
{
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++) 
    {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == sParam) 
        {
            return sParameterName[1];
        }
    }
}

function get_stripped_string(string)
{
    return string.replace(/\s/g, '');
}