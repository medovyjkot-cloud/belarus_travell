import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATABASE'] = 'database.db'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


# Инициализация базы данных с абсолютным путем для сервера Render
def init_db():
    # Находим точную папку, где лежит app.py, и создаем базу прямо там
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, app.config['DATABASE'])

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Создаем таблицу для постов
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            image_path TEXT NOT NULL
        )
    ''')

    # Создаем таблицу для оценок
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stars INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# Вызываем создание базы данных ДО запуска маршрутов
init_db()


def get_db_connection():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, app.config['DATABASE'])
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error loading homepage: {str(e)}", 500


@app.route('/volozhin', methods=['GET', 'POST'])
def volozhin():
    conn = get_db_connection()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        file = request.files.get('photo')

        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            conn.execute('INSERT INTO posts (title, description, image_path) VALUES (?, ?, ?)',
                         (title, description, filename))
            conn.commit()
            conn.close()
            return redirect(url_for('volozhin'))

    posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('volozhin.html', posts=posts)


@app.route('/landmarks')
def landmarks():
    return render_template('landmarks.html')


@app.route('/rate', methods=['GET', 'POST'])
def rate():
    conn = get_db_connection()
    if request.method == 'POST':
        stars = request.form.get('stars')
        if stars:
            conn.execute('INSERT INTO ratings (stars) VALUES (?)', (int(stars),))
            conn.commit()
            conn.close()
            return redirect(url_for('rate'))

    stats = conn.execute('SELECT COUNT(*) as count, AVG(stars) as avg FROM ratings').fetchone()
    conn.close()

    avg_rating = round(stats['avg'], 1) if stats['avg'] else 0
    total_votes = stats['count']

    return render_template('rate.html', avg_rating=avg_rating, total_votes=total_votes)


if __name__ == '__main__':
    app.run(debug=True)



