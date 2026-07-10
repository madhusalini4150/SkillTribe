from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import (StringField, PasswordField, BooleanField,
                     TextAreaField, SelectField, FloatField,
                     IntegerField, SubmitField)
from wtforms.validators import (DataRequired, Email, EqualTo,
                                Length, NumberRange, Optional, ValidationError)
from models import User


class RegisterForm(FlaskForm):
    username  = StringField('Username',  validators=[DataRequired(), Length(3, 80)])
    email     = StringField('Email',     validators=[DataRequired(), Email()])
    password  = PasswordField('Password', validators=[DataRequired(), Length(6)])
    confirm   = PasswordField('Confirm Password', validators=[
                    DataRequired(), EqualTo('password', message='Passwords must match')])
    is_teacher= BooleanField('I want to teach a skill')
    submit    = SubmitField('Create Account')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class LoginForm(FlaskForm):
    email    = StringField('Email',    validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit   = SubmitField('Log In')


class ProfileForm(FlaskForm):
    username    = StringField('Username',  validators=[DataRequired(), Length(3, 80)])
    bio         = TextAreaField('Bio',     validators=[Optional(), Length(max=500)])
    location    = StringField('Location', validators=[Optional(), Length(max=100)])
    avatar      = FileField('Profile photo', validators=[
                     Optional(),
                     FileAllowed(['jpg','jpeg','png','gif','webp'], 'Images only!'),
                     FileSize(max_size=2*1024*1024, message='Max file size is 2MB.')
                 ])
    is_teacher  = BooleanField('I teach skills')
    is_paid     = BooleanField('I charge for my lessons')
    hourly_rate = FloatField('Hourly Rate', validators=[Optional(), NumberRange(min=0)])
    currency    = SelectField('Currency', choices=[('INR','INR ₹'),('USD','USD $'),('EUR','EUR €')])
    submit      = SubmitField('Save Profile')


class AddSkillForm(FlaskForm):
    skill_name = StringField('Skill', validators=[DataRequired(), Length(2, 100)])
    category   = SelectField('Category', choices=[
        ('General','General'), ('Language','Language'),
        ('Technology','Technology'), ('Arts & Crafts','Arts & Crafts'),
        ('Music','Music'), ('Fitness','Fitness'), ('Cooking','Cooking'),
        ('Business','Business'), ('Science','Science'), ('Other','Other'),
    ])
    submit     = SubmitField('Add Skill')


class MessageForm(FlaskForm):
    body   = TextAreaField('Message', validators=[DataRequired(), Length(1, 1000)])
    submit = SubmitField('Send Message')


class ReviewForm(FlaskForm):
    rating  = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(1, 5)])
    comment = TextAreaField('Comment', validators=[Optional(), Length(max=500)])
    submit  = SubmitField('Submit Review')
class BookingForm(FlaskForm):
    session_date = StringField(
        "Session Date",
        validators=[DataRequired()]
    )

    session_time = SelectField(
        "Session Time",
        choices=[
            ("09:00 AM", "09:00 AM"),
            ("10:00 AM", "10:00 AM"),
            ("11:00 AM", "11:00 AM"),
            ("12:00 PM", "12:00 PM"),
            ("02:00 PM", "02:00 PM"),
            ("03:00 PM", "03:00 PM"),
            ("04:00 PM", "04:00 PM"),
            ("05:00 PM", "05:00 PM"),
            ("06:00 PM", "06:00 PM"),
        ]
    )

    duration = SelectField(
        "Duration",
        choices=[
            ("30 Minutes", "30 Minutes"),
            ("1 Hour", "1 Hour"),
            ("2 Hours", "2 Hours"),
        ]
    )

    submit = SubmitField("Continue to Payment")
class DemoVideoForm(FlaskForm):
    title = StringField(
        "Video Title",
        validators=[DataRequired(), Length(max=150)]
    )

    video = FileField(
        "Demo Video",
        validators=[
            DataRequired(),
            FileAllowed(
                ["mp4", "mov", "avi", "mkv", "webm"],
                "Video files only!"
            )
        ]
    )

    submit = SubmitField("Upload Demo Video")
class SearchForm(FlaskForm):
    q        = StringField('Search skill or name')
    category = SelectField('Category', choices=[
        ('','All Categories'), ('Language','Language'),
        ('Technology','Technology'), ('Arts & Crafts','Arts & Crafts'),
        ('Music','Music'), ('Fitness','Fitness'), ('Cooking','Cooking'),
        ('Business','Business'), ('Science','Science'), ('General','General'),
    ])
    free_only = BooleanField('Free only')
    submit    = SubmitField('Search')
