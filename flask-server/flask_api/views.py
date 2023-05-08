from flask import render_template

def forum_view(forums):
    return render_template('index.html', title="Forums", forums=forums)

def posts_view(posts, forum_details):
    return render_template('posts.html', title=forum_details["name"], posts=posts, forum_details=forum_details)

def login_view():
    return render_template('login.html', title="Login")

def register_view():
    return render_template('signup.html', title="Sign Up")

def post_create_view(forum_details):
    return render_template('post-create.html', title="Start Topic", forum_details=forum_details)

def not_found_view():
    return render_template('not-found.html', title="Not Found")

def post_view(first_post, forum_details, posts, logged_in):
    return render_template('post.html', title="Post", first_post=first_post, forum_details=forum_details, posts=posts, logged_in=logged_in)