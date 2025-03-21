from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'linkedin-clone-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///linkedin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    headline = db.Column(db.String(100))
    about = db.Column(db.Text)
    location = db.Column(db.String(100))
    profile_picture = db.Column(db.String(200), default='default-profile.jpg')
    background_image = db.Column(db.String(200), default='default-background.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True)
    experiences = db.relationship('Experience', backref='user', lazy=True)
    educations = db.relationship('Education', backref='user', lazy=True)
    skills = db.relationship('Skill', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    addressee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    requester = db.relationship('User', foreign_keys=[requester_id], backref=db.backref('sent_connections', lazy=True))
    addressee = db.relationship('User', foreign_keys=[addressee_id], backref=db.backref('received_connections', lazy=True))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.relationship('Like', backref='post', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('likes', lazy=True))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('comments', lazy=True))

class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    degree = db.Column(db.String(100))
    field_of_study = db.Column(db.String(100))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    endorsements = db.Column(db.Integer, default=0)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy=True))
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy=True))

# Helper functions
def is_connected(user1_id, user2_id):
    connection = Connection.query.filter(
        ((Connection.requester_id == user1_id) & (Connection.addressee_id == user2_id) |
         (Connection.requester_id == user2_id) & (Connection.addressee_id == user1_id)) &
        (Connection.status == 'accepted')
    ).first()
    return connection is not None

def get_connection_status(user1_id, user2_id):
    connection = Connection.query.filter(
        ((Connection.requester_id == user1_id) & (Connection.addressee_id == user2_id) |
         (Connection.requester_id == user2_id) & (Connection.addressee_id == user1_id))
    ).first()
    
    if not connection:
        return None
    
    if connection.status == 'accepted':
        return 'connected'
    elif connection.status == 'pending':
        if connection.requester_id == user1_id:
            return 'pending_sent'
        else:
            return 'pending_received'
    return connection.status

def get_user_connections(user_id):
    connections = []
    
    # Get connections where user is requester and status is accepted
    requester_connections = Connection.query.filter_by(
        requester_id=user_id, status='accepted'
    ).all()
    
    # Get connections where user is addressee and status is accepted
    addressee_connections = Connection.query.filter_by(
        addressee_id=user_id, status='accepted'
    ).all()
    
    # Add connected users to the list
    for conn in requester_connections:
        connections.append(User.query.get(conn.addressee_id))
    
    for conn in addressee_connections:
        connections.append(User.query.get(conn.requester_id))
    
    return connections

def get_connection_requests(user_id):
    # Get connection requests where user is addressee and status is pending
    requests = Connection.query.filter_by(
        addressee_id=user_id, status='pending'
    ).all()
    
    requesters = []
    for req in requests:
        requesters.append(User.query.get(req.requester_id))
    
    return requesters

def save_file(file, folder=''):
    if not file:
        return None
    
    filename = secure_filename(file.filename)
    # Generate unique filename to prevent overwriting
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, unique_filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    file.save(save_path)
    return os.path.join(folder, unique_filename)

# Context processor to make current user available to all templates
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return {'current_user': user}
    return {'current_user': None}

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('feed'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.')
            return redirect(url_for('login'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password. Please try again.')
            return redirect(url_for('login'))
        
        # Set session
        session['user_id'] = user.id
        session['user_name'] = f"{user.first_name} {user.last_name}"
        
        return redirect(url_for('feed'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/feed')
def feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get user's connections
    connections = get_user_connections(user_id)
    connection_ids = [conn.id for conn in connections] + [user_id]
    
    # Get posts from user and connections
    posts = Post.query.filter(Post.user_id.in_(connection_ids)).order_by(Post.created_at.desc()).all()
    
    # Get connection requests
    connection_requests = get_connection_requests(user_id)
    
    return render_template('feed.html', 
                          user=user, 
                          posts=posts, 
                          connections=connections,
                          connection_requests=connection_requests)

@app.route('/profile/<int:user_id>')
def profile(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user_id = session['user_id']
    profile_user = User.query.get_or_404(user_id)
    
    # Get connection status
    connection_status = get_connection_status(current_user_id, user_id)
    
    # Get user's posts
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()
    
    # Get user's experiences, education, and skills
    experiences = Experience.query.filter_by(user_id=user_id).order_by(Experience.start_date.desc()).all()
    educations = Education.query.filter_by(user_id=user_id).order_by(Education.start_date.desc()).all()
    skills = Skill.query.filter_by(user_id=user_id).order_by(Skill.endorsements.desc()).all()
    
    return render_template('profile.html',
                          user=profile_user,
                          current_user_id=current_user_id,
                          connection_status=connection_status,
                          posts=posts,
                          experiences=experiences,
                          educations=educations,
                          skills=skills)

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.headline = request.form.get('headline')
        user.about = request.form.get('about')
        user.location = request.form.get('location')
        
        # Handle profile picture upload
        if 'profile_picture' in request.files and request.files['profile_picture'].filename:
            profile_pic = request.files['profile_picture']
            file_path = save_file(profile_pic, 'profile_pictures')
            if file_path:
                user.profile_picture = file_path
        
        # Handle background image upload
        if 'background_image' in request.files and request.files['background_image'].filename:
            bg_image = request.files['background_image']
            file_path = save_file(bg_image, 'background_images')
            if file_path:
                user.background_image = file_path
        
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('profile', user_id=user_id))
    
    return render_template('edit_profile.html', user=user)

@app.route('/add-experience', methods=['GET', 'POST'])
def add_experience():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        title = request.form.get('title')
        company = request.form.get('company')
        location = request.form.get('location')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        is_current = 'is_current' in request.form
        
        end_date = None
        if not is_current and request.form.get('end_date'):
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        
        description = request.form.get('description')
        
        experience = Experience(
            user_id=user_id,
            title=title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            description=description
        )
        
        db.session.add(experience)
        db.session.commit()
        
        flash('Experience added successfully!')
        return redirect(url_for('profile', user_id=user_id))
    
    return render_template('add_experience.html')

@app.route('/add-education', methods=['GET', 'POST'])
def add_education():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        school = request.form.get('school')
        degree = request.form.get('degree')
        field_of_study = request.form.get('field_of_study')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        is_current = 'is_current' in request.form
        
        end_date = None
        if not is_current and request.form.get('end_date'):
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        
        description = request.form.get('description')
        
        education = Education(
            user_id=user_id,
            school=school,
            degree=degree,
            field_of_study=field_of_study,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            description=description
        )
        
        db.session.add(education)
        db.session.commit()
        
        flash('Education added successfully!')
        return redirect(url_for('profile', user_id=user_id))
    
    return render_template('add_education.html')

@app.route('/add-skill', methods=['GET', 'POST'])
def add_skill():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        skill_name = request.form.get('skill_name')
        
        skill = Skill(
            user_id=user_id,
            name=skill_name
        )
        
        db.session.add(skill)
        db.session.commit()
        
        flash('Skill added successfully!')
        return redirect(url_for('profile', user_id=user_id))
    
    return render_template('add_skill.html')

@app.route('/create-post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    content = request.form.get('content')
    
    post = Post(
        content=content,
        user_id=user_id
    )
    
    # Handle image upload
    if 'image' in request.files and request.files['image'].filename:
        image = request.files['image']
        file_path = save_file(image, 'post_images')
        if file_path:
            post.image = file_path
    
    db.session.add(post)
    db.session.commit()
    
    flash('Post created successfully!')
    return redirect(url_for('feed'))

@app.route('/like-post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    
    # Check if user already liked the post
    existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if existing_like:
        # Unlike the post
        db.session.delete(existing_like)
        action = 'unliked'
    else:
        # Like the post
        like = Like(user_id=user_id, post_id=post_id)
        db.session.add(like)
        action = 'liked'
    
    db.session.commit()
    
    # Get updated like count
    like_count = Like.query.filter_by(post_id=post_id).count()
    
    return jsonify({
        'success': True,
        'action': action,
        'likeCount': like_count
    })

@app.route('/comment-post/<int:post_id>', methods=['POST'])
def comment_post(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    content = request.form.get('content')
    
    comment = Comment(
        content=content,
        user_id=user_id,
        post_id=post_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # Get user info for the response
    user = User.query.get(user_id)
    
    return jsonify({
        'success': True,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'user_name': f"{user.first_name} {user.last_name}",
            'user_profile_picture': url_for('static', filename=f'uploads/{user.profile_picture}'),
            'created_at': comment.created_at.strftime('%B %d, %Y %I:%M %p')
        }
    })

@app.route('/connect/<int:user_id>', methods=['POST'])
def connect(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    requester_id = session['user_id']
    
    # Check if connection already exists
    existing_connection = Connection.query.filter(
        ((Connection.requester_id == requester_id) & (Connection.addressee_id == user_id) |
         (Connection.requester_id == user_id) & (Connection.addressee_id == requester_id))
    ).first()
    
    if existing_connection:
        flash('Connection request already exists.')
    else:
        connection = Connection(
            requester_id=requester_id,
            addressee_id=user_id
        )
        
        db.session.add(connection)
        db.session.commit()
        
        flash('Connection request sent!')
    
    return redirect(url_for('profile', user_id=user_id))

@app.route('/accept-connection/<int:user_id>', methods=['POST'])
def accept_connection(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    addressee_id = session['user_id']
    
    connection = Connection.query.filter_by(
        requester_id=user_id,
        addressee_id=addressee_id,
        status='pending'
    ).first()
    
    if connection:
        connection.status = 'accepted'
        db.session.commit()
        flash('Connection accepted!')
    else:
        flash('Connection request not found.')
    
    return redirect(url_for('feed'))

@app.route('/reject-connection/<int:user_id>', methods=['POST'])
def reject_connection(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    addressee_id = session['user_id']
    
    connection = Connection.query.filter_by(
        requester_id=user_id,
        addressee_id=addressee_id,
        status='pending'
    ).first()
    
    if connection:
        connection.status = 'rejected'
        db.session.commit()
        flash('Connection rejected.')
    else:
        flash('Connection request not found.')
    
    return redirect(url_for('feed'))

@app.route('/search', methods=['GET'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('q', '')
    
    if not query:
        return render_template('search.html', results=[], query='')
    
    # Search for users
    users = User.query.filter(
        (User.first_name.ilike(f'%{query}%')) |
        (User.last_name.ilike(f'%{query}%')) |
        (User.headline.ilike(f'%{query}%'))
    ).all()
    
    return render_template('search.html', results=users, query=query)

@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user's connections
    connections = get_user_connections(user_id)
    
    # Get selected user if any
    selected_user_id = request.args.get('user_id')
    selected_user = None
    chat_messages = []
    
    if selected_user_id:
        selected_user_id = int(selected_user_id)
        selected_user = User.query.get(selected_user_id)
        
        # Get messages between current user and selected user
        chat_messages = Message.query.filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == selected_user_id) |
             (Message.sender_id == selected_user_id) & (Message.receiver_id == user_id))
        ).order_by(Message.created_at).all()
        
        # Mark unread messages as read
        unread_messages = Message.query.filter_by(
            sender_id=selected_user_id,
            receiver_id=user_id,
            is_read=False
        ).all()
        
        for msg in unread_messages:
            msg.is_read = True
        
        db.session.commit()
    
    return render_template('messages.html', 
                          connections=connections,
                          selected_user=selected_user,
                          messages=chat_messages)

@app.route('/send-message/<int:receiver_id>', methods=['POST'])
def send_message(receiver_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    sender_id = session['user_id']
    content = request.form.get('content')
    
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'created_at': message.created_at.strftime('%B %d, %Y %I:%M %p'),
            'is_sender': True
        }
    })

@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get connection requests
    connection_requests = get_connection_requests(user_id)
    
    # Get unread messages
    unread_messages = Message.query.filter_by(
        receiver_id=user_id,
        is_read=False
    ).all()
    
    # Group messages by sender
    message_senders = {}
    for msg in unread_messages:
        if msg.sender_id not in message_senders:
            message_senders[msg.sender_id] = {
                'user': User.query.get(msg.sender_id),
                'count': 0
            }
        message_senders[msg.sender_id]['count'] += 1
    
    return render_template('notifications.html',
                          connection_requests=connection_requests,
                          message_senders=message_senders)

@app.route('/jobs')
def jobs():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # In a real application, you would fetch jobs from a database
    # For this example, we'll use dummy data
    jobs = [
        {
            'id': 1,
            'title': 'Software Engineer',
            'company': 'Tech Corp',
            'location': 'San Francisco, CA',
            'description': 'We are looking for a skilled software engineer...',
            'posted_date': '2023-05-15'
        },
        {
            'id': 2,
            'title': 'Product Manager',
            'company': 'Innovate Inc',
            'location': 'New York, NY',
            'description': 'Join our team as a product manager...',
            'posted_date': '2023-05-10'
        },
        {
            'id': 3,
            'title': 'Data Scientist',
            'company': 'Data Analytics Co',
            'location': 'Remote',
            'description': 'Seeking a data scientist with experience in...',
            'posted_date': '2023-05-12'
        }
    ]
    
    return render_template('jobs.html', jobs=jobs)

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)