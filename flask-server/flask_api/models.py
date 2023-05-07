from flask_api.settings import *
from flaskext.mysql import MySQL
import timeago

mysql = MySQL()

# reference: AWD Moodle Labs
server.config['SECRET_KEY'] = 'jd-awd-forum-super-secret-key'

# reference: AWD Moodle Labs
server.config['MYSQL_DATABASE_USER'] = 'jordan.dalby'
server.config['MYSQL_DATABASE_PASSWORD'] = '3K3RpLm8p'
server.config['MYSQL_DATABASE_DB'] = 'jordandalby-awd-forum'
server.config['MYSQL_DATABASE_HOST'] = 'ysjcs.net'
server.config['MYSQL_DATABASE_PORT'] = 3306
server.config['MYSQL_DATABASE_CHARSET'] = 'utf8'
mysql.init_app(server)

def get_connection():
    conn = mysql.connect()
    conn.ping(True)
    return conn.cursor(), conn
    
def connection_done(conn):
    conn.close()

# forums
def get_forum_details(cursor, forum_id):
    cursor.execute(f"SELECT forum_name, forum_description FROM forums WHERE forum_id='{forum_id}'")

    if cursor.rowcount == 0:
        return None

    result = cursor.fetchone()
    forum_details = {
        'forum_id': forum_id,
        'name': result[0],
        'description': result[1]
    }

    return forum_details

def get_forums(cursor):
    cursor.execute("SELECT * FROM forums")
    results = cursor.fetchall()

    forum_list = []
    for result in results:
        cursor.execute(f"SELECT COUNT(*) FROM posts WHERE forum_id='{result[0]}' AND parent_post_id IS NULL")
        count_result = cursor.fetchone()[0]

        recent_post_id = None
        recent_post_title = None
        recent_post_author_username = None

        cursor.execute(f'''SELECT p.post_id, p.post_title, p.post_author, p.timestamp
                       FROM posts p
                       LEFT JOIN (
                       SELECT parent_post_id, MAX(timestamp) AS max_timestamp
                       FROM posts
                       WHERE parent_post_id IS NOT NULL
                       GROUP BY parent_post_id) p2 ON p.post_id = p2.parent_post_id
                       WHERE p.parent_post_id IS NULL
                       AND forum_id='{result[0]}'
                       ORDER BY COALESCE(p2.max_timestamp, p.timestamp) DESC''')
        if cursor.rowcount != 0:
            recent_post_result = cursor.fetchone()

            recent_post_id = recent_post_result[0]
            recent_post_title = recent_post_result[1]

            recent_post_author_username = get_user(cursor, recent_post_result[2])["username"]
        
        forum_list.append(
        {
            'id': result[0],
            'name': result[1], 
            'description': result[2],
            'post_count': count_result,
            'recent_post_id': recent_post_id,
            'recent_post_title': shorten_string(recent_post_title, 20),
            'recent_post_author': recent_post_author_username
        })

    return forum_list

# posts
def get_posts(cursor, forum_id):
    # complex query that selects all original posts by first filtering the results by rows that have a parent_post_id equal to NULL
    # then further filtered by forum_id
    # then a left join is used to match each original post with its most recent reply, if it has one
    # the subquery then selects the parent_post_id and the maximum timestamp value for each reply and groups them by their parent_post_id
    # then the result is ordered by maximum timestamp in descending order, using the timestamp of the most recent reply if there is one
    # and the timestamp of the original post if there isn't
    # this achieves the behaviour of a forum by ordering by most recent activity as oppose to most recent original post
    cursor.execute(f'''SELECT p.post_id, p.post_title, p.post_author, p.timestamp
                       FROM posts p
                       LEFT JOIN (
                       SELECT parent_post_id, MAX(timestamp) AS max_timestamp
                       FROM posts
                       WHERE parent_post_id IS NOT NULL
                       GROUP BY parent_post_id) p2 ON p.post_id = p2.parent_post_id
                       WHERE p.parent_post_id IS NULL
                       AND forum_id='{forum_id}'
                       ORDER BY COALESCE(p2.max_timestamp, p.timestamp) DESC''')
    results = cursor.fetchall()

    post_list = []
    for result in results:
        cursor.execute(f"SELECT COUNT(*) FROM posts WHERE parent_post_id='{result[0]}'")
        count_result = cursor.fetchone()[0]

        author_username = get_user(cursor, result[2])["username"]

        now_time = datetime.datetime.now()
        last_reply = result[3]
        reply_author = author_username

        cursor.execute(f"SELECT post_author, timestamp FROM posts WHERE parent_post_id='{result[0]}' AND timestamp=(SELECT MAX(timestamp) FROM posts WHERE parent_post_id='{result[0]}')")
        if cursor.rowcount != 0:
            out = cursor.fetchone()
            last_reply = out[1]

            reply_author = get_user(cursor, out[0])["username"]

        difference = timeago.format(last_reply, now_time)

        post_list.append(
        {
            'id': result[0],
            'title': result[1],
            'author': author_username,
            'timestamp': timeago.format(result[3], now_time),
            'reply_count': count_result,
            'recent_reply_username': reply_author,
            'recent_reply_timestamp': difference
        })
    
    return post_list

def get_post_posts(user_id, post_id):
    conn = get_connection()
    cursor = conn[0]

    cursor.execute(f"SELECT post_id FROM posts WHERE post_id='{post_id}'")

    if cursor.rowcount == 0:
        return None, None, None
    
    user = get_user(cursor, user_id)

    cursor.execute(f"SELECT post_id, parent_post_id, forum_id, post_title, post_author, post_content, timestamp, edited, edit_timestamp FROM posts WHERE post_id='{post_id}' OR parent_post_id='{post_id}' ORDER BY timestamp ASC")
    results = cursor.fetchall()

    now_time = datetime.datetime.now()

    posts = []
    first_post = None
    forum_id = results[0][2]
    for post in results:
        post_author = get_user(cursor, post[4])

        post_details = {
            'post_id': post[0],
            'parent_post_id': post[1],
            'post_title': post[3],
            'post_author': post_author,
            'post_content': post[5],
            'timestamp': timeago.format(post[6], now_time),
            'edited': post[7],
            'edit_timestamp': timeago.format(post[8], now_time) if post[7] == 1 else "",
            'likes': get_post_likes(cursor, post[0]),
            'liked': has_user_liked_post(cursor, user_id, post[0]),
            'options': (user is not None) and (user["user_id"] == post_author["user_id"] or user["admin"] == 1),
            'admin': (user is not None) and user["admin"] == 1
        }

        if first_post is None:
            first_post = post_details

        posts.append(post_details)

    connection_done(conn[1])

    return posts, first_post, forum_id

def has_user_liked_post(cursor, user_id, post_id):
    if user_id != -1: 
        cursor.execute(f"SELECT user_id FROM likes WHERE post_id='{post_id}' AND user_id='{user_id}'")
        return cursor.rowcount != 0
    else:
        return False

def get_post_likes(cursor, post_id):
    cursor.execute(f"SELECT COUNT(*) FROM likes WHERE post_id='{post_id}'")
    likes = cursor.fetchone()[0]
    return likes

# users
def get_user(cursor, user_id):
    cursor.execute(f"SELECT username, password, admin FROM users WHERE user_id='{user_id}'")
    if cursor.rowcount == 0:
        return None
    
    result = cursor.fetchone()
    return {'user_id': user_id, 'username': result[0], 'password': result[1], 'admin': result[2]}

# tokens
def get_token(user_id, username, admin):
    conn = get_connection();

    now = datetime.datetime.now()
    expire_time = now + datetime.timedelta(days=7)

    token = jwt.encode({'user-id': user_id, 'username': username, 'expires': expire_time.isoformat(), 'admin': admin}, server.config['SECRET_KEY'])

    conn[0].execute(f"UPDATE users SET session='{token}' WHERE user_id='{user_id}'")
    conn[1].commit()

    connection_done(conn[1])

    return token

def decode_token(token):
    if token is None:
        return None, None, None, None
    
    decoded_token = jwt.decode(token, server.config['SECRET_KEY'], algorithms=['HS256'])
    expiry = decoded_token['expires']
    user_id = decoded_token['user-id']
    username = decoded_token['username']
    admin = decoded_token['admin']

    return expiry, user_id, username, admin

# misc
def shorten_string(string, max):
    if string is None:
        return None
    return string[:max] + "..." if len(string) > max else string