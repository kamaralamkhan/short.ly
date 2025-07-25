from flask import Flask, render_template, request, redirect
import sqlite3
import string
import random
from datetime import datetime

app = Flask(__name__)


# Utility: DB Initialization
def init_db():
    with sqlite3.connect('urls.db') as conn:
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            url TEXT,
            clicks INTEGER DEFAULT 0
        )''')
        conn.commit()


# Utility: Short Code Generator
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


@app.route('/', methods=['GET', 'POST'])
def index():
    shorten_result = []
    if request.method == 'POST':
        urls = request.form['urls'].splitlines()
        with sqlite3.connect('urls.db') as conn:
            c = conn.cursor()
            for u in urls:
                u = u.strip()
                if u:
                    c.execute('SELECT code FROM links WHERE url=?', (u,))
                    row = c.fetchone()
                    if row:
                        code = row[0]
                    else:
                        # Generate unique code, ensure collision avoidance
                        while True:
                            code = generate_code()
                            c.execute('SELECT 1 FROM links WHERE code=?', (code,))
                            if not c.fetchone():
                                break
                        c.execute('INSERT INTO links (code, url) VALUES (?, ?)', (code, u))
                        conn.commit()
                    shorten_result.append({'original': u, 'short': request.host_url + code})
        return render_template('result.html', results=shorten_result, current_year=datetime.now().year)
    return render_template('index.html', current_year=datetime.now().year)


@app.route('/<code>')
def redirect_url(code):
    with sqlite3.connect('urls.db') as conn:
        c = conn.cursor()
        c.execute('SELECT url, clicks FROM links WHERE code=?', (code,))
        row = c.fetchone()
        if row:
            url, clicks = row
            c.execute('UPDATE links SET clicks=? WHERE code=?', (clicks + 1, code))
            conn.commit()
            return redirect(url)
    return 'Invalid or expired link.', 404


if __name__ == '__main__':
    init_db()
    app.run(debug=True)  # Remember to use debug=False in production!
