from flask_wtf import FlaskForm
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    name = StringField('Имя и фамилия', validators=[DataRequired()])
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    about = TextAreaField("Информация о себе")
    submit = SubmitField('Зарегистрироваться')


class JobsForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    is_private = BooleanField("Приватность")
    payment = IntegerField('Оплата за задание')
    submit = SubmitField('Применить')


class ThemeForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    category = StringField('Категория', validators=[DataRequired()])
    is_private = BooleanField("Приватность")
    submit = SubmitField("Применить")


class QuestionForm(FlaskForm):
    theme = StringField('Тема/Категория')
    title = StringField('Текст вопроса')
    email = StringField('Ваша почта')
    is_anon = BooleanField("Отправить анонимно?")
    submit = SubmitField("Применить")