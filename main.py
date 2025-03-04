from data.imports import *


app = Flask(__name__)
app.config['SECRET_KEY'] = 'PASSWORD'
app.config['UPLOAD_FOLDER'] = 'static\img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/')
def index():
    session = db_session.create_session()
    jobs = session.query(Jobs).filter(Jobs.is_private != True, Jobs.request == 0)[::-1]
    return render_template("index.html", jobs=jobs, title='Доступные работы')


@app.route('/my_jobs')
def my_jobs():
    session = db_session.create_session()
    jobs = session.query(Jobs).filter(
        (Jobs.user == current_user) | (Jobs.is_private == True))[::-1]
    return render_template("index.html", jobs=jobs, title='Мои работы')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        file = request.files['ava']
        if file and allowed_file(file.filename):
            user.is_ava = True
            if not os.path.isdir(app.config['UPLOAD_FOLDER']):
                os.mkdir(app.config["UPLOAD_FOLDER"])
            path = os.path.join(app.config['UPLOAD_FOLDER'], f'{user.name}.png')
            file.save(path)
            file.close()
            file = Image.open(path)
            file.thumbnail((128, 128))
            file.save(path)
        session.add(user)
        session.commit()
        login_user(user, remember=True)
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/jobs',  methods=['GET', 'POST'])
@login_required
def add_jobs():
    form = JobsForm()
    if form.validate_on_submit():
        session = db_session.create_session()

        jobs = Jobs()
        jobs.title = form.title.data
        jobs.content = form.content.data
        jobs.is_private = form.is_private.data
        jobs.payment = form.payment.data

        current_user.jobs.append(jobs)
        session.merge(current_user)
        session.commit()
        return redirect('/')
    return render_template('jobs.html', title='Добавление новости', 
                           form=form)


@app.route('/jobs/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_jobs(id):
    form = JobsForm()
    if request.method == "GET":
        session = db_session.create_session()
        jobs = session.query(Jobs).filter(Jobs.id == id,
                                          Jobs.user == current_user).first()
        if jobs:
            form.title.data = jobs.title
            form.content.data = jobs.content
            form.is_private.data = jobs.is_private
            form.payment.data = jobs.payment
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        jobs = session.query(Jobs).filter(Jobs.id == id,
                                          Jobs.user == current_user).first()
        if jobs:
            jobs.title = form.title.data
            jobs.content = form.content.data
            jobs.is_private = form.is_private.data
            form.payment.data = jobs.payment
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('jobs.html', title='Редактирование новости', form=form)


@app.route('/user/<int:id>', methods=['GET', 'POST'])
@login_required
def open_user(id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == id).first()
    jobs = user.jobs
    return render_template('profile.html', user=user, jobs=jobs)


@app.route('/jobs_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def jobs_delete(id):
    session = db_session.create_session()
    jobs = session.query(Jobs).filter(Jobs.id == id,
                                      Jobs.user == current_user).first()
    if jobs:
        session.delete(jobs)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/requests/<int:id>')
@login_required
def set_request(id):
    session = db_session.create_session()
    job = session.query(Jobs).filter(Jobs.id == id).first()
    job.request = current_user.id
    job.request_name = current_user.name
    session.commit()
    return redirect('/')


@app.route('/my_requests')
@login_required
def my_requests():
    session = db_session.create_session()
    jobs = session.query(Jobs).filter(Jobs.is_complete == False, Jobs.user == current_user, Jobs.request != 0)[::-1]
    return render_template('requests.html', jobs=jobs, title='Мои запросы')


@app.route('/requests_endorse/<int:id><int:user>')
@login_required
def requests_endorse(id, user):
    session = db_session.create_session()
    job = session.query(Jobs).filter(Jobs.id == id).first()
    user = session.query(User).filter(User.id == user).first()

    job.is_complete = True
    # session.merge(user)
    user.balance += job.payment
    session.merge(current_user)
    current_user.balance -= job.payment
    session.commit()
    return redirect('/my_requests')


@app.route('/requests_cancel/<int:id>')
@login_required
def requests_cancel(id):
    session = db_session.create_session()
    job = session.query(Jobs).filter(Jobs.id == id).first()
    job.request = 0
    session.commit()
    return redirect('/my_requests')


@app.route('/theme_add', methods=['GET', 'POST'])
@login_required
def add_forum():
    form = ThemeForm()
    if form.validate_on_submit():
        session = db_session.create_session()

        theme = Theme()
        theme.title = form.title.data
        theme.user_id = current_user.id
        theme.category = form.category.data
        theme.is_private = form.is_private.data
        session.add(theme)
        session.commit()
        return redirect('/forum')
    return render_template('theme.html', title='Добавление тему на форум',
                           form=form)


@app.route('/theme_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def theme_delete(id):
    session = db_session.create_session()
    theme = session.query(Theme).filter(Theme.id == id,
                                      Theme.creator == current_user).first()
    if theme:
        session.delete(theme)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/theme_edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_theme(id):
    form = ThemeForm()
    if request.method == "GET":
        session = db_session.create_session()
        theme = session.query(Theme).filter(Theme.id == id,
                                          Theme.creator == current_user).first()
        if theme:
            form.title.data = theme.title
            form.category.data = theme.category
            form.is_private.data = theme.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        theme = session.query(Theme).filter(Theme.id == id,
                                          Theme.creator == current_user).first()
        if theme:
            theme.title = form.title.data
            theme.category = form.category.data
            theme.is_private = form.is_private.data
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('theme.html', title='Редактирование темы', form=form)


@app.route('/forum')
def forum():
    session = db_session.create_session()
    themes = session.query(Theme).all()[::-1]
    return render_template('forum.html', themes=themes, title='Форум')


@app.route('/defers_add/<int:id>', methods=['GET', 'POST'])
def set_defers(id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    if str(id) not in user.defers.split(','):
        user.defers += f",{id}"
    session.commit()
    return redirect('/')


@app.route('/defers_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def defers_delete(id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    defers = user.defers.split(',')
    defers.remove(str(id))
    defers = ','.join(defers)
    user.defers = defers
    session.commit()
    return redirect('/defers')


@app.route('/defers')
def defers():
    session = db_session.create_session()
    jobs = session.query(Jobs).all()
    user = session.query(User).filter(User.id == current_user.id).first()
    jobs = session.query(Jobs).filter(Jobs.id.in_(list(map(lambda x: int(x), user.defers.split(',')[1:]))))[::-1]
    return render_template('index.html', jobs=jobs, title='Отложенные')


@app.route('/help')
def help():
    return render_template('help.html', title='Вопросы и ответы')


@app.route('/about')
def about():
    return render_template('about.html', title='О нас')


@app.route('/complete')
@login_required
def complete():
    session = db_session.create_session()
    jobs = session.query(Jobs).filter(Jobs.request == current_user.id, Jobs.is_complete == 1)
    return render_template('index.html', title="Выполненные работы", jobs=jobs)



@app.route('/question', methods=['GET', 'POST'])
def question():
    form = QuestionForm()

    if form.validate_on_submit():
        return redirect('/')
    return render_template('question.html', form=form, title='Вопросы и ответы')


@app.route('/user/<int:id>/complete')
def info_complete(id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == id).first()
    jobs = session.query(Jobs).filter(Jobs.request == id)
    return render_template('profile_info.html', title='complete', jobs=jobs, user=user)


@app.route('/user/<int:id>/jobs')
def info_jobs(id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == id).first()
    jobs = session.query(Jobs).filter(Jobs.user_id == id)
    return render_template('profile_info.html', title='jobs', jobs=jobs, user=user)


if __name__ == '__main__':
    db_session.global_init("db/redwork.sqlite")
    app.run(port=8080, host='127.0.0.1')