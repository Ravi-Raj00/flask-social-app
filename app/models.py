from app import db, login_manager, bcrypt, login_manager
from datetime import datetime
from flask_login import UserMixin

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# This is the "user_loader" callback.
# Flask-Login uses this to reload the user object
# from the user ID stored in the session.
@login_manager.user_loader
def load_user(user_id):
    # We now have the User model, so we can return the user object
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    """
    User model for our database.
    Includes id, username, email, and a hashed passsword.
    UserMixin adds required properties for Flask-Login.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password_hash = db.Column(db.String(60), nullable=False) # 60 chars for bcrypt hash
    posts = db.relationship('Post', backref='author', lazy=True)

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        # Checks if the current user is already following the given 'user'
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def set_password(self, password):
        """Creates a password hash from a plain-text password."""
        # We use bcrypt to generate a hash
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check if a plain-text password matches the stored hash."""
        # We use bcrypt to compare the stored hash with the one
        # generated from the provided password.
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        """A friendly representation of the User object."""
        return f"User('{self.username}', '{self.email}')"
    

class Post(db.Model):
    """
    Post model for our database.
    """
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    # We use default=datetime.utcnow to store the creation time.
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # --- This Is The Foreign Key ---
    # This is column links the post to a user
    # 'user.id' is the *table* and *column* name (all lowercase)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # nullable=True because not every post will have an image
    image_file = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        """A friendly representation of the Post object."""
        return f"Post('{self.body[:50]}...', '{self.timestamp}')"
    
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # Two foreign keys to the SAME User table
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship
    # We use 'foreign_keys' to tell SQLALchemy specifically which colum to use for which relationship
    # 'backref' automatically adds 'sen_messages' and 'received_message' lists to the User model.
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

    def __repr__(self):
        return f"Message('{self.body}"