from flask import jsonify, request, url_for, session
from flask_api.views import *
from flask_api.models import *
from flask_api.settings import *
import datetime
import bcrypt

@server.route("/")
@server.route("/index")
@server.route("/forums")
def index():
    conn = get_connection()
    cursor = conn[0]

    forum_list = get_forums(cursor)

    connection_done(conn[1])

    return forum_view(forum_list)

@server.route("/forum/<forum_id>")
def forum(forum_id):
    conn = get_connection()
    cursor = conn[0]

    forum_details = get_forum_details(cursor, forum_id)
    if forum_details is None:
        return not_found_view()

    post_list = get_posts(cursor, forum_id)
    
    connection_done(conn[1])

    return posts_view(post_list, forum_details)

@server.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == None or password == None:
            return jsonify({'response': 'Please fill in all fields'})
        
        conn = get_connection()
        cursor = conn[0]

        cursor.execute(f"SELECT user_id, username, password, admin FROM users WHERE username='{username}'")
        if cursor.rowcount == 0:
            return jsonify({'response': 'Invalid credentials entered'})
        
        result = cursor.fetchone()

        connection_done(conn[1])

        db_pass = result[2].encode('utf8')

        if bcrypt.checkpw(password.encode('utf8'), db_pass):
            # return session ID too
            return jsonify({'response': 'Invalid credentials entered', 'token': get_token(result[0], result[1], result[3])})
        else:
            return jsonify({'response': 'Invalid credentials entered'})
    
    return login_view()

@server.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == None or password == None:
            return jsonify({'response': 'Please fill in all fields'})
        
        conn = get_connection()
        cursor = conn[0]

        password = password.encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        string_hashed_password = hashed_password.decode('utf8')

        cursor.execute(f"SELECT user_id FROM users WHERE username='{username}'")
        if not cursor.rowcount == 0:
            return jsonify({'response': 'That username is taken'})
        
        cursor.execute(f"INSERT INTO users(username, password, session) VALUES ('{username}', '{string_hashed_password}', 'token')")
        conn[1].commit()

        cursor.execute(f"SELECT user_id, username, admin FROM users WHERE username='{username}'")
        result = cursor.fetchone()
        user_id = result[0]
        username = result[1]

        connection_done(conn[1])
        # return session ID too
        return jsonify({'response': 'Success', 'token': get_token(user_id, username, result[2])})

    return register_view()

@server.route("/post/create/<forum_id>", methods=["PUT"])
@token_required
def post_post(user_id, *_, forum_id):
    conn = get_connection()
    cursor = conn[0]
    
    json_val = request.get_json(True)
    title = json_val['title']
    content = json_val['content']
    
    if len(title.replace(" ", "")) < 5:
        return jsonify({'response': 'Title too short', 'action': 0})
    
    if len(content.replace(" ", "")) < 5:
        return jsonify({'response': 'Content too short', 'action': 0})
    
    cursor.execute(f"INSERT INTO posts(forum_id, post_title, post_author, post_content, timestamp) VALUES ('{forum_id}', \"{title}\", '{user_id}', \"{content}\", '{datetime.datetime.now()}')")
    conn[1].commit()

    cursor.execute(f"SELECT LAST_INSERT_ID()")
    post_id = cursor.fetchone()[0]

    connection_done(conn[1])

    return jsonify({'response': 'posted', 'action': 1, 'url': url_for("post", post_id=post_id)})

@server.route("/post/create/<forum_id>", methods=["GET"])
@soft_token_check
def post_get(user_id, *_, forum_id):
    if user_id == -1:
        return not_found_view()

    conn = get_connection()
    cursor = conn[0]

    forum_details = get_forum_details(cursor, forum_id)
    if forum_details is None:
        return not_found_view()

    connection_done(conn[1])

    return post_create_view(forum_details)

@server.route("/post/<post_id>")
@soft_token_check
def post(user_id, *_, post_id):
    posts, first_post, forum_id = get_post_posts(user_id, post_id)
    
    if posts is None:
        return not_found_view()

    conn = get_connection()
    cursor = conn[0]
    forum_details = get_forum_details(cursor, forum_id);
    connection_done(conn[1])

    return post_view(first_post, forum_details, posts, user_id != -1)

@server.route("/post/like/<post_id>", methods=["GET"])
@token_required
def like(user_id, *_, post_id):
    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT user_id FROM likes WHERE user_id='{user_id}' AND post_id='{post_id}'")
    if cursor.rowcount == 0:
        cursor.execute(f"INSERT INTO likes(post_id, user_id) VALUES ('{post_id}', '{user_id}')")
        conn[1].commit()

        likes = get_post_likes(cursor, post_id)

        connection_done(conn[1])

        return jsonify({'response': 'success', 'post_id': post_id, 'likes': likes, 'action': 1})
    else:
        cursor.execute(f"DELETE FROM likes WHERE post_id='{post_id}' AND user_id='{user_id}'")
        conn[1].commit()

        likes = get_post_likes(cursor, post_id)

        connection_done(conn[1])
        return jsonify({'response': 'success', 'post_id': post_id, 'likes': likes, 'action': 0})

@server.route("/post/edit/delete/<post_id>", methods=["DELETE"])
@token_required
def post_delete(admin, *_, post_id):
    if not admin:
        return jsonify({'response': 'Only admins can do that'})

    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT parent_post_id FROM posts WHERE post_id='{post_id}'")
    parent_post_id = cursor.fetchone()[0]

    # need to use two separate queries, ysjcs phpmyadmin is mariadb v 10.1, CTEs added in 10.2
    if parent_post_id is None:
        cursor.execute(f"DELETE FROM likes WHERE post_id IN (SELECT post_id FROM (SELECT l.post_id FROM posts p LEFT JOIN likes l ON p.post_id = l.post_id WHERE p.post_id='{post_id}' OR p.parent_post_id='{post_id}') AS likes_to_delete);")
        cursor.execute(f"DELETE FROM posts WHERE post_id IN (SELECT post_id FROM (SELECT post_id FROM posts WHERE post_id='{post_id}' OR parent_post_id='{post_id}') AS posts_to_delete);")
    else:
        cursor.execute(f"DELETE FROM likes WHERE post_id='{post_id}'")
        cursor.execute(f"DELETE FROM posts WHERE post_id='{post_id}'")

    conn[1].commit()

    connection_done(conn[1])

    return jsonify({'response': 'success', 'action': 1 if parent_post_id is None else 0})

@server.route("/post/edit/begin/<post_id>", methods=["GET"])
@token_required
def begin_edit_post(user_id, admin, _, post_id):
    if admin:
        return jsonify({'response': 'Overriden, edit allowed', 'action': 1})

    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT post_author FROM posts WHERE post_id='{post_id}'")
    post_author = cursor.fetchone()[0]

    connection_done(conn[1])

    # if user is the poster of the post
    if post_author == user_id:
        return jsonify({'response': 'Owner, edit allowed', 'action': 1})
    
    return jsonify({'response': 'Insufficient permission, edit disallowed', 'action': 0})

@server.route("/post/edit/end/<post_id>", methods=["POST"])
@token_required
def end_edit_post(user_id, admin, _, post_id):
    json_val = request.get_json(True)
    content = json_val['content']

    if len(content) < 5:
        return jsonify({'response': 'Content too short', 'action': 0})

    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT post_author, post_content FROM posts WHERE post_id='{post_id}'")
    result = cursor.fetchone()

    post_author = result[0]
    post_content = result[1]

    if post_content == content:
        # no changes were made, don't edit
        return jsonify({'response': 'No changes made', 'action': 1})

    # if user is the poster of the post
    if (post_author == user_id) or admin:
        cursor.execute(f"UPDATE posts SET post_content=\"{content}\", edited='1', edit_timestamp='{datetime.datetime.now()}' WHERE post_id='{post_id}'")
        conn[1].commit()
    else:
        return jsonify({'response': 'Insufficient permission', 'action': 0})

    connection_done(conn[1])

    return jsonify({'response': 'success', 'action': 1})

@server.route("/post/edit/cancel/<post_id>", methods=["GET"])
def cancel_edit_post(post_id):
    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT post_content FROM posts WHERE post_id='{post_id}'")
    post_content = cursor.fetchone()[0]

    return jsonify({'response': 'Retrieved', 'post_content': post_content})

@server.route("/post/reply/<post_id>", methods=["POST"])
@token_required
def reply(user_id, *_, post_id):
    json_val = request.get_json(True)
    content = json_val['content']
    
    if len(content) < 2:
        return jsonify({'response': 'Content too short', 'action': 0})

    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT forum_id FROM posts WHERE post_id='{post_id}'")
    forum_id = cursor.fetchone()[0]

    cursor.execute(f"INSERT INTO posts(parent_post_id, forum_id, post_author, post_content, timestamp) VALUES ('{post_id}', '{forum_id}', '{user_id}', \"{content}\", '{datetime.datetime.now()}')")
    conn[1].commit()

    connection_done(conn[1])

    return jsonify({'response': 'success', 'action': 1})

@server.route("/user/token")
@token_required
def check_user_token(user_id, username, admin):
    return jsonify({'response': 'Login token valid, sign in', 'action': 1, 'user_id': user_id, 'username': username, 'admin': admin})

"""
@server.route("/post", methods=["POST"])
def get_post():
    json_val = request.get_json(True)

    post_id = json_val['post_id']
    token = json_val['token']

    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT post_id, forum_id, post_title, post_author, post_content, timestamp, edited, edit_timestamp FROM posts WHERE post_id='{post_id}'")

    if cursor.rowcount == 0:
        return {'response': 'No post found'}

    result = cursor.fetchone()

    _, user_id, _, _ = decode_token(token)
    has_user_liked = False
    show_options = False
    if token is not None:
        if user_id is not None: 
            cursor.execute(f"SELECT user_id FROM likes WHERE post_id='{post_id}' AND user_id='{user_id}'")
            has_user_liked = cursor.rowcount != 0
            show_options = True

    now_time = datetime.datetime.now()

    post = {
        'post_id': result[0],
        'post_title': result[2],
        'post_author': get_user(cursor, result[3])["username"],
        'post_content': result[4],
        'post_likes': get_post_likes(cursor, post_id),
        'post_timestamp': timeago.format(result[5], now_time),
        'forum_id': result[1],
        'forum_name': get_forum_details(cursor, result[1])["name"],
        'has_user_liked': has_user_liked,
        'show_options': show_options,
        'edited': result[6],
        'edit_timestamp': timeago.format(result[7], now_time) if result[6] == 1 else ""
    }

    connection_done(conn[1])

    return jsonify(post)

@server.route("/post/replies", methods=["POST"])
def get_post_replies():
    json_val = request.get_json(True)

    post_id = json_val['post_id']
    token = json_val['token']
    _, user_id, _, admin = decode_token(token)

    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT post_id, post_author, post_content, timestamp, edited, edit_timestamp FROM posts WHERE parent_post_id='{post_id}' ORDER BY timestamp ASC")
    results = cursor.fetchall()

    now_time = datetime.datetime.now()

    post_list = []
    for res in results:
        has_user_liked = False
        show_options = False
        if token is not None:
            if user_id is not None:
                cursor.execute(f"SELECT user_id FROM likes WHERE post_id='{res[0]}' AND user_id='{user_id}'")
                has_user_liked = cursor.rowcount != 0

                if admin or res[1] == user_id:
                    show_options = True

        post_list.append({
            'post_id': res[0],
            'post_author': get_username(cursor, res[1]),
            'post_content': res[2],
            'post_likes': get_post_likes(cursor, res[0]),
            'post_timestamp': timeago.format(res[3], now_time),
            'has_user_liked': has_user_liked,
            'show_options': show_options,
            'edited': res[4],
            'edit_timestamp': timeago.format(res[5], now_time) if res[4] == 1 else ""
        })

    connection_done(conn[1])

    return jsonify(post_list)

@server.route("/post/reply", methods=["POST"])
@token_required
def reply(user_id, *_):
    json_val = request.get_json(True)

    post_id = json_val['post_id']
    content = json_val['content']
    
    if len(content) < 2:
        return jsonify({'response': 'Content too short', 'action': 0})

    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT forum_id FROM posts WHERE post_id='{post_id}'")
    forum_id = cursor.fetchone()[0]

    cursor.execute(f"INSERT INTO posts(parent_post_id, forum_id, post_author, post_content, timestamp) VALUES ('{post_id}', '{forum_id}', '{user_id}', \"{content}\", '{datetime.datetime.now()}')")
    conn[1].commit();

    connection_done(conn[1]);

    return jsonify({'response': 'success', 'action': 1})

@server.route("/post/like", methods=["POST"])
@token_required
def like(user_id, *_):
    json_val = request.get_json(True)

    post_id = json_val['post_id']
    
    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT user_id FROM likes WHERE user_id='{user_id}' AND post_id='{post_id}'")
    if cursor.rowcount == 0:
        cursor.execute(f"INSERT INTO likes(post_id, user_id) VALUES ('{post_id}', '{user_id}')")
        conn[1].commit()

        likes = get_post_likes(cursor, post_id)

        connection_done(conn[1])

        return jsonify({'response': 'success', 'post_id': post_id, 'likes': likes, 'action': 1})
    else:
        cursor.execute(f"DELETE FROM likes WHERE post_id='{post_id}' AND user_id='{user_id}'")
        conn[1].commit()

        likes = get_post_likes(cursor, post_id)

        connection_done(conn[1])
        return jsonify({'response': 'success', 'post_id': post_id, 'likes': likes, 'action': 0})

@server.route("/post/delete", methods=["POST"])
@token_required
def post_delete(admin, *_):
    json_val = request.get_json(True)

    post_id = json_val['post_id']
    
    if not admin:
        return jsonify({'response': 'Only admins can do that'})

    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT parent_post_id FROM posts WHERE post_id='{post_id}'")
    parent_post_id = cursor.fetchone()[0]

    # need to use two separate queries, ysjcs phpmyadmin is mariadb v 10.1, CTEs added in 10.2
    if parent_post_id is None:
        cursor.execute(f"DELETE FROM likes WHERE post_id IN (SELECT post_id FROM (SELECT l.post_id FROM posts p LEFT JOIN likes l ON p.post_id = l.post_id WHERE p.post_id='{post_id}' OR p.parent_post_id='{post_id}') AS likes_to_delete);")
        cursor.execute(f"DELETE FROM posts WHERE post_id IN (SELECT post_id FROM (SELECT post_id FROM posts WHERE post_id='{post_id}' OR parent_post_id='{post_id}') AS posts_to_delete);")
    else:
        cursor.execute(f"DELETE FROM likes WHERE post_id='{post_id}'")
        cursor.execute(f"DELETE FROM posts WHERE post_id='{post_id}'")

    conn[1].commit()

    connection_done(conn[1])

    return jsonify({'response': 'success', 'action': 1 if parent_post_id is None else 0})

@server.route("/post/edit/begin", methods=["POST"])
@token_required
def begin_edit_post(user_id, admin, _):
    json_val = request.get_json(True)

    post_id = json_val['post_id']
    
    if admin:
        return jsonify({'response': 'Overriden, edit allowed', 'action': 1})

    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT post_author FROM posts WHERE post_id='{post_id}'")
    post_author = cursor.fetchone()[0]

    connection_done(conn[1])

    # if user is the poster of the post
    if post_author == user_id:
        return jsonify({'response': 'Owner, edit allowed', 'action': 1})
    
    return jsonify({'response': 'Insufficient permission, edit disallowed', 'action': 0})

@server.route("/post/edit/end", methods=["POST"])
@token_required
def end_edit_post(user_id, admin, _):
    json_val = request.get_json(True)

    post_id = json_val['post_id']
    content = json_val['content']

    if len(content) < 2:
        return jsonify({'response': 'Content too short', 'action': 0})

    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT post_author, post_content FROM posts WHERE post_id='{post_id}'")
    result = cursor.fetchone()

    post_author = result[0]
    post_content = result[1]

    if post_content == content:
        # no changes were made, don't edit
        return jsonify({'response': 'No changes made', 'action': 1})

    # if user is the poster of the post
    if (post_author == user_id) or admin:
        cursor.execute(f"UPDATE posts SET post_content='{content}', edited='1', edit_timestamp='{datetime.datetime.now()}' WHERE post_id='{post_id}'")
        conn[1].commit()
    else:
        return jsonify({'response': 'Insufficient permission', 'action': 0})

    connection_done(conn[1])

    return jsonify({'response': 'success', 'action': 1})

@server.route("/post/edit/cancel/<post_id>", methods=["GET"])
def cancel_edit_post(post_id):
    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT post_content FROM posts WHERE post_id='{post_id}'")
    post_content = cursor.fetchone()[0]

    return jsonify({'response': 'Retrieved', 'post_content': post_content})"""