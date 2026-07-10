from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

user_skills = db.Table(
    'user_skills',
    db.Column('user_id',  db.Integer, db.ForeignKey('user.id'),  primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)

    bio        = db.Column(db.Text,        default='')
    location   = db.Column(db.String(100), default='')
    avatar     = db.Column(db.String(200), default='')   # filename in static/images/

    is_teacher = db.Column(db.Boolean, default=False)
    is_paid    = db.Column(db.Boolean, default=False)
    hourly_rate= db.Column(db.Float,   default=0.0)
    currency   = db.Column(db.String(10), default='INR')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen  = db.Column(db.DateTime, default=datetime.utcnow)

    skills     = db.relationship('Skill', secondary=user_skills, backref='users', lazy='dynamic')
    sent_messages     = db.relationship('Message', foreign_keys='Message.sender_id',   backref='sender',   lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy='dynamic')
    given_reviews     = db.relationship('Review',  foreign_keys='Review.reviewer_id',  backref='reviewer', lazy='dynamic')
    received_reviews  = db.relationship('Review',  foreign_keys='Review.reviewed_id',  backref='reviewed', lazy='dynamic')
    
    @property
    def avg_rating(self):
        reviews = self.received_reviews.all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    @property
    def review_count(self):
        return self.received_reviews.count()

    @property
    def skill_names(self):
        return [s.name for s in self.skills]

    @property
    def avatar_url(self):
        if self.avatar:
            return '/static/images/' + self.avatar
        return None

    def unread_messages(self):
        return self.received_messages.filter_by(is_read=False).count()

    def __repr__(self):
        return f'<User {self.username}>'


class Skill(db.Model):
    __tablename__ = 'skill'
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50),  default='General')
    slug     = db.Column(db.String(120), unique=True)

    def __repr__(self):
        return f'<Skill {self.name}>'


class Message(db.Model):
    __tablename__ = 'message'
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body        = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.sender_id}->{self.receiver_id}>'


class Review(db.Model):
    __tablename__ = 'review'
    id          = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating      = db.Column(db.Integer, nullable=False)
    comment     = db.Column(db.Text, default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Review {self.reviewer_id}->{self.reviewed_id} {self.rating} stars>'
class Booking(db.Model):
    __tablename__ = "booking"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    amount = db.Column(db.Float, nullable=False)

    currency = db.Column(db.String(10), default="INR")

    status = db.Column(
        db.String(20),
        default="Pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    student = db.relationship(
        "User",
        foreign_keys=[student_id]
    )

    teacher = db.relationship(
        "User",
        foreign_keys=[teacher_id]
    )

    def __repr__(self):
        return f"<Booking {self.id}>"
class DemoVideo(db.Model):
    __tablename__ = "demo_video"

    id = db.Column(db.Integer, primary_key=True)

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    teacher = db.relationship(
        "User",
        backref="demo_videos"
    )

    def __repr__(self):
        return f"<DemoVideo {self.title}>"