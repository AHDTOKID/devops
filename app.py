from flask import Flask, render_template, request, redirect, session, send_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
import time
import os

app = Flask(__name__)
app.secret_key = "secret123"


def init_db():
    conn = sqlite3.connect('database.db')

    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS screenshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        url TEXT,
        file TEXT
    )''')

    conn.close()

init_db()


def take_screenshot(url):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)
    time.sleep(2)

    filename = f"static/screenshots/{int(time.time())}.png"
    driver.save_screenshot(filename)
    driver.quit()

    return filename


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        url = request.form['url']
        file = take_screenshot(url)

        conn = sqlite3.connect('database.db')
        conn.execute("INSERT INTO screenshots (user_id, url, file) VALUES (?, ?, ?)",
                     (session['user_id'], url, file))
        conn.commit()
        conn.close()

        return redirect('/')

    conn = sqlite3.connect('database.db')
    data = conn.execute("SELECT * FROM screenshots WHERE user_id=?",
                        (session['user_id'],)).fetchall()
    conn.close()

    return render_template('index.html', data=data)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                     (username, password))
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?",
                            (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect('/')
        else:
            return "Invalid Credentials"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    row = cur.execute("SELECT file FROM screenshots WHERE id=?", (id,)).fetchone()

    if row:
        if os.path.exists(row[0]):
            os.remove(row[0])
        cur.execute("DELETE FROM screenshots WHERE id=?", (id,))
        conn.commit()

    conn.close()
    return redirect('/')


@app.route('/download/<path:filename>')
def download(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists('static/screenshots'):
        os.makedirs('static/screenshots')
    app.run(debug=True)