from app import create_app, db
from app.models import User, Post

# Create the app instance using our factory
app = create_app()

# This 'shell context' is useful for development.
# It pre-imports our 'app' and 'db' when we run 'flask shell'
@app.shell_context_processor
def make_shell_context():
    # We will add our models here as we create them
    # return {'db': db, 'User': User, 'Post': Post}
    return {'db': db, 'User': User, 'Post': Post}

if __name__ == '__main__':
    app.run(debug=True)