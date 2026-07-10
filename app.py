import os
import re
import uuid
import razorpay
from datetime import datetime

from flask import (Flask, render_template, redirect, url_for,
                   request, flash, abort, jsonify)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename

from config import Config
from models import (
    db,
    User,
    Skill,
    Message,
    Review,
    Booking,
    user_skills,
    DemoVideo
)
from forms import (
    RegisterForm,
    LoginForm,
    ProfileForm,
    AddSkillForm,
    MessageForm,
    ReviewForm,
    SearchForm,
    DemoVideoForm
)

# ── App factory ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)
razorpay_client = razorpay.Client(
    auth=(
        app.config["RAZORPAY_KEY_ID"],
        app.config["RAZORPAY_KEY_SECRET"]
    )
)

db.init_app(app)
migrate   = Migrate(app, db)
bcrypt    = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
login_mgr = LoginManager(app)
login_mgr.login_view      = 'login'
login_mgr.login_message   = 'Please log in to access this page.'
login_mgr.login_message_category = 'info'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@login_mgr.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Helpers ──────────────────────────────────────────────────────────────────
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text


def get_or_create_skill(name, category='General'):
    name = name.strip().title()
    skill = Skill.query.filter_by(name=name).first()
    if not skill:
        skill = Skill(name=name, category=category, slug=slugify(name))
        db.session.add(skill)
        db.session.flush()
    return skill


def allowed_file(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in app.config['ALLOWED_EXTENSIONS']


def save_avatar(file_storage):
    """Save an uploaded profile photo, resized to a square thumbnail.
    Returns the new filename, or None if no file was provided."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None

    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        from PIL import Image
        img = Image.open(file_storage)
        img = img.convert('RGB')
        # Center-crop to square, then resize to 300x300
        w, h = img.size
        side = min(w, h)
        left, top = (w - side) // 2, (h - side) // 2
        img = img.crop((left, top, left + side, top + side)).resize((300, 300))
        img.save(filepath, quality=85)
    except Exception:
        # Pillow not available or image processing failed — save raw file instead
        file_storage.stream.seek(0)
        file_storage.save(filepath)

    return filename


# ── Color system ─────────────────────────────────────────────────────────────
# Every skill category gets its own color, like a badge color — this is how
# the UI tells categories apart at a glance instead of everything looking the
# same shade of beige. Same 5-hue set reused across categories on purpose,
# so the palette stays disciplined rather than sprawling.
ACCENT_COLORS = ['#FF5D73', '#7C5CFC', '#FFC34D', '#1FC79B', '#38BDF8']

CATEGORY_COLOR_MAP = {
    'Language':       '#7C5CFC',  # violet
    'Business':       '#7C5CFC',
    'Technology':     '#1FC79B',  # mint
    'Science':        '#1FC79B',
    'Arts & Crafts':  '#FF5D73',  # coral
    'Cooking':        '#FF5D73',
    'Music':          '#FFC34D',  # sun
    'Fitness':        '#38BDF8',  # sky
}
DEFAULT_CATEGORY_COLOR = '#9B8FC4'  # muted violet-gray for General/Other


def category_color(category):
    return CATEGORY_COLOR_MAP.get(category, DEFAULT_CATEGORY_COLOR)


def user_accent(user):
    """Deterministic color per user, so the same person always gets the
    same colored avatar — like a consistent badge color, not random noise."""
    if not user or not getattr(user, 'username', None):
        return ACCENT_COLORS[0]
    idx = sum(ord(c) for c in user.username) % len(ACCENT_COLORS)
    return ACCENT_COLORS[idx]


# ── Context processors ───────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    search_form = SearchForm()
    unread = 0
    if current_user.is_authenticated:
        unread = current_user.unread_messages()
    return dict(search_form=search_form, unread_count=unread,
                category_color=category_color, user_accent=user_accent)


# ════════════════════════════════════════════════════════════════════════════
#  HEALTH CHECK  (used by Render/Railway to confirm the app is alive)
# ════════════════════════════════════════════════════════════════════════════

@app.route('/healthz')
def healthz():
    return jsonify(status='ok'), 200


# ════════════════════════════════════════════════════════════════════════════
#  PUBLIC ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    featured = (User.query
                .filter_by(is_teacher=True)
                .order_by(User.created_at.desc())
                .limit(6).all())

    categories = (db.session.query(Skill.category,
                                   db.func.count(Skill.id).label('cnt'))
                  .group_by(Skill.category)
                  .order_by(db.desc('cnt'))
                  .all())

    total_teachers = User.query.filter_by(is_teacher=True).count()
    total_skills   = Skill.query.count()
    return render_template('index.html',
                           featured=featured,
                           categories=categories,
                           total_teachers=total_teachers,
                           total_skills=total_skills)


@app.route('/search')
def search():
    q        = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    free_only= request.args.get('free_only') == 'y'
    page     = request.args.get('page', 1, type=int)

    query = User.query.filter_by(is_teacher=True)

    if q:
        skill_user_ids = (db.session.query(user_skills.c.user_id)
                          .join(Skill, Skill.id == user_skills.c.skill_id)
                          .filter(Skill.name.ilike(f'%{q}%')))
        query = query.filter(
            (User.username.ilike(f'%{q}%')) |
            (User.bio.ilike(f'%{q}%')) |
            (User.id.in_(skill_user_ids))
        )

    if category:
        cat_user_ids = (db.session.query(user_skills.c.user_id)
                        .join(Skill, Skill.id == user_skills.c.skill_id)
                        .filter(Skill.category == category))
        query = query.filter(User.id.in_(cat_user_ids))

    if free_only:
        query = query.filter_by(is_paid=False)

    pagination = query.paginate(page=page,
                                per_page=app.config['TEACHERS_PER_PAGE'],
                                error_out=False)
    teachers = pagination.items

    all_categories = (db.session.query(Skill.category)
                      .distinct().order_by(Skill.category).all())

    return render_template('search.html',
                           teachers=teachers,
                           pagination=pagination,
                           q=q,
                           category=category,
                           free_only=free_only,
                           all_categories=[c[0] for c in all_categories])


@app.route('/profile/<int:user_id>')
def profile(user_id):
    user    = User.query.get_or_404(user_id)
    reviews = user.received_reviews.order_by(Review.created_at.desc()).all()
    review_form = ReviewForm()
    msg_form    = MessageForm()
    already_reviewed = False
    if current_user.is_authenticated:
        already_reviewed = Review.query.filter_by(
            reviewer_id=current_user.id,
            reviewed_id=user.id
        ).first() is not None
    return render_template('profile.html',
                           user=user,
                           reviews=reviews,
                           review_form=review_form,
                           msg_form=msg_form,
                           already_reviewed=already_reviewed)


# ════════════════════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username   = form.username.data,
            email      = form.email.data,
            password   = hashed,
            is_teacher = form.is_teacher.data
        )
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {user.username}! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            user.last_seen = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    inbox = (current_user.received_messages
             .order_by(Message.created_at.desc())
             .limit(5).all())
    my_skills = current_user.skills.all()
    add_form  = AddSkillForm()
    return render_template('dashboard.html',
                           inbox=inbox,
                           my_skills=my_skills,
                           add_form=add_form)


# ════════════════════════════════════════════════════════════════════════════
#  PROFILE EDIT  (now with avatar upload)
# ════════════════════════════════════════════════════════════════════════════

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        if form.username.data != current_user.username:
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already taken.', 'danger')
                return render_template('settings.html', form=form)

        current_user.username    = form.username.data
        current_user.bio         = form.bio.data
        current_user.location    = form.location.data
        current_user.is_teacher  = form.is_teacher.data
        current_user.is_paid     = form.is_paid.data
        current_user.hourly_rate = form.hourly_rate.data or 0.0
        current_user.currency    = form.currency.data

        # Handle profile photo upload
        if form.avatar.data:
            filename = save_avatar(form.avatar.data)
            if filename:
                current_user.avatar = filename

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('settings.html', form=form)


# ════════════════════════════════════════════════════════════════════════════
#  SKILLS
# ════════════════════════════════════════════════════════════════════════════

@app.route('/skills/add', methods=['POST'])
@login_required
def add_skill():
    form = AddSkillForm()
    if form.validate_on_submit():
        skill = get_or_create_skill(form.skill_name.data, form.category.data)
        if skill not in current_user.skills.all():
            current_user.skills.append(skill)
            db.session.commit()
            flash(f'"{skill.name}" added to your skills!', 'success')
        else:
            flash(f'You already have "{skill.name}" listed.', 'info')
    else:
        flash('Please enter a valid skill name.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/skills/remove/<int:skill_id>', methods=['POST'])
@login_required
def remove_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    if skill in current_user.skills.all():
        current_user.skills.remove(skill)
        db.session.commit()
        flash(f'"{skill.name}" removed from your skills.', 'info')
    return redirect(url_for('dashboard'))


# ════════════════════════════════════════════════════════════════════════════
#  MESSAGES
# ════════════════════════════════════════════════════════════════════════════

@app.route('/message/<int:user_id>', methods=['GET', 'POST'])
@login_required
def send_message(user_id):
    recipient = User.query.get_or_404(user_id)
    if recipient.id == current_user.id:
        flash("You can't message yourself.", 'warning')
        return redirect(url_for('profile', user_id=user_id))

    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(
            sender_id   = current_user.id,
            receiver_id = recipient.id,
            body        = form.body.data
        )
        db.session.add(msg)
        db.session.commit()
        flash(f'Message sent to {recipient.username}!', 'success')
        return redirect(url_for('profile', user_id=user_id))
    return render_template('message.html', form=form, recipient=recipient)


@app.route('/inbox')
@login_required
def inbox():
    messages = (current_user.received_messages
                .order_by(Message.created_at.desc())
                .all())
    for m in messages:
        if not m.is_read:
            m.is_read = True
    db.session.commit()
    return render_template('inbox.html', messages=messages)


@app.route('/conversation/<int:user_id>', methods=['GET'])
@login_required
def conversation(user_id):
    other = User.query.get_or_404(user_id)
    thread = (Message.query
              .filter(
                  ((Message.sender_id   == current_user.id) & (Message.receiver_id == other.id)) |
                  ((Message.sender_id   == other.id)        & (Message.receiver_id == current_user.id))
              )
              .order_by(Message.created_at.asc())
              .all())
    for m in thread:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()
    form = MessageForm()
    return render_template('conversation.html', other=other, thread=thread, form=form)


# ════════════════════════════════════════════════════════════════════════════
#  REVIEWS
# ════════════════════════════════════════════════════════════════════════════

@app.route('/review/<int:user_id>', methods=['POST'])
@login_required
def leave_review(user_id):
    reviewed = User.query.get_or_404(user_id)
    if reviewed.id == current_user.id:
        flash("You can't review yourself.", 'warning')
        return redirect(url_for('profile', user_id=user_id))

    existing = Review.query.filter_by(
        reviewer_id=current_user.id,
        reviewed_id=reviewed.id
    ).first()
    if existing:
        flash('You have already reviewed this person.', 'info')
        return redirect(url_for('profile', user_id=user_id))

    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            reviewer_id = current_user.id,
            reviewed_id = reviewed.id,
            rating      = form.rating.data,
            comment     = form.comment.data
        )
        db.session.add(review)
        db.session.commit()
        flash('Review submitted. Thank you!', 'success')
    else:
        flash('Invalid review - rating must be 1-5.', 'danger')
    return redirect(url_for('profile', user_id=user_id))

@app.route('/book/<int:user_id>')
@login_required
def book_session(user_id):
    teacher = User.query.get_or_404(user_id)

    if teacher.id == current_user.id:
        flash("You can't book yourself.", "warning")
        return redirect(url_for("profile", user_id=user_id))

    return render_template("book_session.html", teacher=teacher)


@app.route('/payment/<int:user_id>')
@login_required
def payment(user_id):
    teacher = User.query.get_or_404(user_id)

    amount = int(teacher.hourly_rate * 100)  # Razorpay uses paise

    razorpay_order = razorpay_client.order.create({
        "amount": amount,
        "currency": teacher.currency,
        "payment_capture": 1
    })

    return render_template(
        "payment.html",
        teacher=teacher,
        order=razorpay_order,
        razorpay_key=app.config["RAZORPAY_KEY_ID"]
    )
@app.route('/payment/complete/<int:user_id>', methods=['POST'])
@login_required
def payment_complete(user_id):

    teacher = User.query.get_or_404(user_id)

    booking = Booking(
        student_id=current_user.id,
        teacher_id=teacher.id,
        amount=teacher.hourly_rate,
        currency=teacher.currency,
        status="Paid"
    )

    db.session.add(booking)
    db.session.commit()

    return jsonify({
        "redirect": url_for(
            "payment_success",
            booking_id=booking.id
        )
    })
@app.route('/payment/success/<int:booking_id>')
@login_required
def payment_success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template("payment_success.html", booking=booking)
@app.route('/my-bookings')
@login_required
def my_bookings():

    student_bookings = Booking.query.filter_by(
        student_id=current_user.id
    ).all()

    teacher_bookings = Booking.query.filter_by(
        teacher_id=current_user.id
    ).all()

    return render_template(
        "my_bookings.html",
        student_bookings=student_bookings,
        teacher_bookings=teacher_bookings
    )
@app.route("/upload-demo", methods=["GET", "POST"])
@login_required
def upload_demo():

    if not current_user.is_teacher:
        flash("Only teachers can upload demo videos.", "warning")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        if "video" not in request.files:
            flash("Select a video.", "danger")
            return redirect(request.url)

        file = request.files["video"]

        if file.filename == "":
            flash("Select a video.", "danger")
            return redirect(request.url)

        filename = secure_filename(file.filename)

        folder = os.path.join(
            app.config["UPLOAD_FOLDER"],
            "demo_videos"
        )

        os.makedirs(folder, exist_ok=True)

        filepath = os.path.join(folder, filename)
        file.save(filepath)

        demo = DemoVideo(
            teacher_id=current_user.id,
            title=request.form["title"],
            filename=filename
        )

        db.session.add(demo)
        db.session.commit()

        flash("Demo video uploaded successfully!", "success")

        return redirect(url_for("profile", user_id=current_user.id))

    return render_template("upload_demo.html")
# ════════════════════════════════════════════════════════════════════════════
#  API  (JSON)
# ════════════════════════════════════════════════════════════════════════════

@app.route('/api/skills/autocomplete')
def api_skill_autocomplete():
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    skills = Skill.query.filter(Skill.name.ilike(f'%{q}%')).limit(10).all()
    return jsonify([{'id': s.id, 'name': s.name, 'category': s.category} for s in skills])


@app.route('/api/teachers')
def api_teachers():
    q   = request.args.get('q', '')
    cat = request.args.get('category', '')
    query = User.query.filter_by(is_teacher=True)
    if q:
        skill_ids = (db.session.query(user_skills.c.user_id)
                     .join(Skill, Skill.id == user_skills.c.skill_id)
                     .filter(Skill.name.ilike(f'%{q}%')))
        query = query.filter((User.username.ilike(f'%{q}%')) | (User.id.in_(skill_ids)))
    if cat:
        cat_ids = (db.session.query(user_skills.c.user_id)
                   .join(Skill, Skill.id == user_skills.c.skill_id)
                   .filter(Skill.category == cat))
        query = query.filter(User.id.in_(cat_ids))
    teachers = query.limit(20).all()
    return jsonify([{
        'id': t.id, 'username': t.username, 'bio': t.bio, 'location': t.location,
        'is_paid': t.is_paid, 'rate': t.hourly_rate, 'currency': t.currency,
        'rating': t.avg_rating, 'reviews': t.review_count, 'skills': t.skill_names,
        'avatar': t.avatar_url,
    } for t in teachers])


# ════════════════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.errorhandler(413)
def too_large(e):
    flash('File too large — max 2MB.', 'danger')
    return redirect(request.referrer or url_for('dashboard'))


# ════════════════════════════════════════════════════════════════════════════
#  DB SEED  (demo data — only runs if SEED_DEMO=true AND db is empty)
# ════════════════════════════════════════════════════════════════════════════

def seed_demo_data():
    if User.query.first():
        return

    demo_users = [
        dict(username='aiko_tanaka', email='aiko@demo.com',
             bio='Native Japanese speaker. Conversational Japanese & JLPT prep (N4-N2).',
             location='Online', is_teacher=True, is_paid=False, hourly_rate=0,
             skills=[('Japanese','Language'),('JLPT','Language'),('Japanese Conversation','Language')]),
        dict(username='ravi_mehta', email='ravi@demo.com',
             bio='Senior data engineer. I teach Python, pandas and ML from scratch.',
             location='Hyderabad, India', is_teacher=True, is_paid=True, hourly_rate=200, currency='INR',
             skills=[('Python','Technology'),('Data Science','Technology'),('Machine Learning','Technology')]),
        dict(username='priya_sharma', email='priya@demo.com',
             bio='Textile artist teaching hand embroidery and Zardozi.',
             location='Mumbai, India', is_teacher=True, is_paid=False, hourly_rate=0,
             skills=[('Embroidery','Arts & Crafts'),('Stitching','Arts & Crafts'),('Zardozi','Arts & Crafts')]),
        dict(username='lucas_ferreira', email='lucas@demo.com',
             bio='10-year guitar teacher. Beginner chords to fingerstyle.',
             location='Online', is_teacher=True, is_paid=True, hourly_rate=150, currency='INR',
             skills=[('Guitar','Music'),('Music Theory','Music'),('Ukulele','Music')]),
        dict(username='meera_nair', email='meera@demo.com',
             bio='Certified French teacher. DELF B1/B2 prep & conversational French.',
             location='Kerala, India', is_teacher=True, is_paid=False, hourly_rate=0,
             skills=[('French','Language'),('DELF Prep','Language')]),
        dict(username='demo_user', email='demo@demo.com',
             bio='Just here to learn new skills!',
             location='Chennai', is_teacher=False, is_paid=False, hourly_rate=0,
             skills=[]),
    ]

    pw_hash = bcrypt.generate_password_hash('demo1234').decode('utf-8')

    for ud in demo_users:
        user = User(
            username=ud['username'], email=ud['email'], password=pw_hash,
            bio=ud['bio'], location=ud['location'], is_teacher=ud['is_teacher'],
            is_paid=ud['is_paid'], hourly_rate=ud['hourly_rate'],
            currency=ud.get('currency', 'INR'),
        )
        db.session.add(user)
        db.session.flush()
        for sname, scat in ud['skills']:
            skill = get_or_create_skill(sname, scat)
            user.skills.append(skill)

    db.session.flush()
    demo = User.query.filter_by(username='demo_user').first()
    aiko = User.query.filter_by(username='aiko_tanaka').first()
    if demo and aiko:
        db.session.add(Review(reviewer_id=demo.id, reviewed_id=aiko.id,
                              rating=5, comment='Amazing teacher! Very patient and clear.'))

    db.session.commit()
    print('Demo data seeded. Login: demo@demo.com / demo1234')


# ════════════════════════════════════════════════════════════════════════════
#  VIDEO / VOICE CALL ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.route('/call/<int:user_id>')
@login_required
def call(user_id):
    """Initiate a call to another user."""
    callee = User.query.get_or_404(user_id)
    if callee.id == current_user.id:
        flash("You can't call yourself.", 'warning')
        return redirect(url_for('dashboard'))
    # Room ID is always the sorted pair so both sides land in the same room
    room_id = f"call_{'_'.join(sorted([str(current_user.id), str(callee.id)]))}"
    return render_template('call.html',
                           other=callee,
                           room_id=room_id,
                           is_caller=True)


@app.route('/call/<int:user_id>/join')
@login_required
def join_call(user_id):
    """Answer an incoming call from another user."""
    caller = User.query.get_or_404(user_id)
    room_id = f"call_{'_'.join(sorted([str(current_user.id), str(caller.id)]))}"
    return render_template('call.html',
                           other=caller,
                           room_id=room_id,
                           is_caller=False)


# ════════════════════════════════════════════════════════════════════════════
#  SOCKETIO SIGNALING  (WebRTC offer / answer / ICE exchange)
# ════════════════════════════════════════════════════════════════════════════

@socketio.on('join_call_room')
def on_join_call_room(data):
    """Both peers join the same room so they can exchange SDP/ICE."""
    room = data.get('room_id')
    join_room(room)
    # Tell the OTHER person in the room a peer has arrived
    emit('peer_joined', {'user_id': data.get('user_id')}, to=room, include_self=False)


@socketio.on('call_offer')
def on_call_offer(data):
    """Caller sends WebRTC offer SDP → relay to callee."""
    emit('call_offer', data, to=data['room_id'], include_self=False)


@socketio.on('call_answer')
def on_call_answer(data):
    """Callee sends WebRTC answer SDP → relay to caller."""
    emit('call_answer', data, to=data['room_id'], include_self=False)


@socketio.on('ice_candidate')
def on_ice_candidate(data):
    """Relay ICE candidates between peers."""
    emit('ice_candidate', data, to=data['room_id'], include_self=False)


@socketio.on('call_ended')
def on_call_ended(data):
    """Notify the other peer the call was ended."""
    emit('call_ended', {}, to=data['room_id'], include_self=False)
    leave_room(data['room_id'])


@socketio.on('call_rejected')
def on_call_rejected(data):
    """Callee rejected the call."""
    emit('call_rejected', {}, to=data['room_id'], include_self=False)


# ════════════════════════════════════════════════════════════════════════════
#  STARTUP
# ════════════════════════════════════════════════════════════════════════════

with app.app_context():
    db.create_all()
    if Config.SEED_DEMO:
        seed_demo_data()


if __name__ == '__main__':
    debug_mode = not Config.IS_PRODUCTION
    port = int(os.environ.get('PORT', 5000))
    app.run(host="127.0.0.1", port=5000, debug=True)