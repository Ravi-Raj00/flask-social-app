import os
import secrets
import bleach 
from PIL import Image
from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app, send_from_directory
from app import db, create_app
from sqlalchemy import or_
from app.forms import RegistrationForm, LoginForm, PostForm, UpdateAccountForm, MessageForm
from app.models import User, Post, Message 
from flask_login import login_user, current_user, logout_user, login_required

main = Blueprint('main', __name__)

@main.route("/user/<string:username>")
def user_posts(username):
    # 404 if user doesn't exist
    user = User.query.filter_by(username=username).first_or_404()
    # Get posts for this user
    posts = Post.query.filter_by(author=user).order_by(Post.timestamp.desc()).all()
    return render_template('user_posts.html', posts=posts, user=user)

@main.route("/")
@main.route("/index")
def index():
    # Get all posts, ordered by newest first
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create user, set password (hashing is handled by the model method we wrote), and save.
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # Check if user exists AND the password matches the hash
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            # Redirect to the next page if it exists (e.g., if they tried to access a protected page)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route("/post/new", methods=['GET', 'POST'])
@login_required # This decorator protects the route.
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        # Handel image if uploaded
        picture_file = None
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 'post_pics')

        # --- SECURITY FIX: Sanitize input ---
        clean_body = bleach.clean(form.body.data)
        # ----------------------------------------

        # Create a new Post instance, linking it to the current_user
        post = Post(body=clean_body, author=current_user, image_file=picture_file)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.index')) # Redirect to the homepage
    
    return render_template('create_post.html', title='New Post', form=form)

def save_picture(form_picture, folder):
    # Generate a random hex for the picture filename
    random_hex = secrets.token_hex(8)
    # Get the file extension (e.g., .jpg, .png)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    # Create the full path to save the picture
    picture_path = os.path.join(current_app.root_path, 'static', folder, picture_fn)

    # Resize the image using Pillow to save and speed up page loads
    i = Image.open(form_picture)
    if folder == 'profile_pics':
       i.thumbnail((125, 125))
    elif folder == 'post_pics':
       max_dim = 280
       if i.width > max_dim or i.height > max_dim:
           #.thumbnail scales down maintaining aspect ratio
           i.thumbnail((max_dim, max_dim)) 

    # Save the resized image
    i.save(picture_path)

    return picture_fn

@main.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        # If they uploaded a picture, save it and update the DB field
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 'profile_pics')
            current_user.image_file = picture_file
        
        # Update username and email
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account'))
    elif request.method == 'GET':
        # Pre-fill the form with current data
        form.username.data = current_user.username
        form.email.data = current_user.email

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

@main.route("/chat/<username>", methods=['GET', 'POST'])
@login_required
def chat(username):
    other_user = User.query.filter_by(username=username).first_or_404()
    
    if other_user == current_user:
        flash('You cannot chat with yourself.', 'warning')
        return redirect(url_for('main.index'))

    form = MessageForm()

    # --- POST: A new message is being sent (for HTMX) ---
    if form.validate_on_submit():
        clean_body = bleach.clean(form.message.data)
        msg = Message(sender=current_user, recipient=other_user, body=clean_body)
        db.session.add(msg)
        db.session.commit()
        
        # --- HTMX Response ---
        # Return the new list of messages, sorted .asc()
        messages = Message.query.filter(
            or_(
                (Message.sender == current_user) & (Message.recipient == other_user),
                (Message.sender == other_user) & (Message.recipient == current_user)
            )
        ).order_by(Message.timestamp.asc()).all() # <-- Must be .asc() (ascending)
        
        return render_template('_chat_messages.html', 
                               messages=messages, 
                               recipient=other_user)

    # --- GET: Just load the page "shell" ---
    return render_template('chat.html', title=f'Chat with {username}', 
                           form=form, recipient=other_user, messages=[])


@main.route("/messages")
@login_required
def messages():
    # Get all messages sent OR received by the current user
    sent_messages = Message.query.filter_by(sender=current_user).all()
    received_messages = Message.query.filter_by(recipient=current_user).all()
    
    # Use a set to find all unique users (conversation partners)
    users_chatted_with = set()
    for msg in sent_messages:
        users_chatted_with.add(msg.recipient)
    for msg in received_messages:
        users_chatted_with.add(msg.sender)
    
    return render_template('messages.html', conversations=list(users_chatted_with))

@main.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'User {username} not found.', 'danger')
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot follow yourself!', 'warning')
        return redirect(url_for('main.user_posts', username=username))
        
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {username}!', 'success')
    return redirect(url_for('main.user_posts', username=username))

@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'User {username} not found.', 'danger')
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot unfollow yourself!', 'warning')
        return redirect(url_for('main.user_posts', username=username))
        
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You have unfollowed {username}.', 'info')
    return redirect(url_for('main.user_posts', username=username))

@main.route("/post/<int:post_id>/delete", methods=['GET', 'POST']) # Must accept POST
@login_required
def delete_post(post_id):
    # 1. Find the post or return 404 (Not Found)
    post = Post.query.get_or_404(post_id)

    # 2. --- THE CRITICAL IDOR CHECK ---
    # This part is for security, not HTMX.
    # If a user tries to delete a post that isn't theirs,
    # we DO flash and redirect them.
    if post.author != current_user:
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('main.index'))

    # 3. If the check passes, delete the image file
    if post.image_file:
        try:
            image_path = os.path.join(current_app.root_path, 'static/post_pics', post.image_file)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting post image {post.image_file}: {e}")

    # 4. Delete the post from the database
    db.session.delete(post)
    db.session.commit()

    # 5. --- THE HTMX FIX ---
    # Return an empty string. HTMX sees this "200 OK" response
    # and knows the delete was successful. It then removes
    # the element defined in hx-target.
    return ""

@main.route("/chat/<username>/messages")
@login_required
def chat_messages(username):
    other_user = User.query.filter_by(username=username).first_or_404()

    messages = Message.query.filter(
        or_(
            (Message.sender == current_user) & (Message.recipient == other_user),
            (Message.sender == other_user) & (Message.recipient == current_user)
        )
    ).order_by(Message.timestamp.asc()).all() # <-- Must be .asc() (ascending)

    # Render the PARTIAL template
    return render_template('_chat_messages.html', 
                           messages=messages, 
                           recipient=other_user)