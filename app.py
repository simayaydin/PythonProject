from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from datetime import datetime
import sqlite3
import os

# Veritabanı bağlantısı fonksiyonu
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row  
    return conn

# Fragman URL'lerini saklayan dictionary
TRAILERS = {
    "The Shawshank Redemption": "https://www.youtube.com/watch?v=NmzuHjWmXOc",
    "The Godfather": "https://www.youtube.com/watch?v=sY1S34973zA",
    "The Dark Knight": "https://www.youtube.com/watch?v=EXeTwQWrcwY",
    "Pulp Fiction": "https://www.youtube.com/watch?v=s7EdQ4FqbhY",
    "Forrest Gump": "https://www.youtube.com/watch?v=bLvqoHBptjg",
    "Inception": "https://www.youtube.com/watch?v=YoHD9XEInc0",
    "Friends": "https://www.youtube.com/watch?v=hDNNmeeJs1Q",
    "Prens": "https://www.youtube.com/watch?v=JyiSPKZoqF8",
    "The Last of Us": "https://www.youtube.com/watch?v=uLtkt8BonwM",
    "The Conjuring": "https://www.youtube.com/watch?v=k10ETZ41q5o",
    "Hereditary": "https://www.youtube.com/watch?v=V6wWKNij_1M",
    "It": "https://www.youtube.com/watch?v=xKJmEC5ieOk",
    "A Quiet Place": "https://www.youtube.com/watch?v=WR7cc5t7tv8",
    "The Ring": "https://www.youtube.com/watch?v=TuH5FaUpFm4",
    "Insidious": "https://www.youtube.com/watch?v=zuZnRUcoWos",
    "Fight Club": "https://www.youtube.com/watch?v=SUXWAEX2jlg",
    "Parasite": "https://www.youtube.com/watch?v=5xH0HfJHsaY",
    "The Green Mile": "https://www.youtube.com/watch?v=Ki4haFrqSrw",
    "The Hangover": "https://www.youtube.com/watch?v=tcdUhdOlz9M",
    "Superbad": "https://www.youtube.com/watch?v=4eaZ_48ZYog",
    "Step Brothers": "https://www.youtube.com/watch?v=CewglxElBK0",
    "Bridesmaids": "https://www.youtube.com/watch?v=FNppLrmdyug",
    "Brooklyn Nine-Nine": "https://www.youtube.com/watch?v=2RrreVthWRw",
    "Pride & Prejudice": "https://www.youtube.com/watch?v=1dYv5u6v55Y",
    "Aşk Tesadüfleri Sever": "https://www.youtube.com/watch?v=6C_X3J_Kw40",
    "La La Land": "https://www.youtube.com/watch?v=0pdqf4P9MB8",
    "Titanic": "https://www.youtube.com/watch?v=2e-eXJ6HgkQ",
    "Issız Adam": "https://www.youtube.com/watch?v=F8VYoF6kXSk",
    "The Notebook": "https://www.youtube.com/watch?v=FC6biTjEyZw",
    "Interstellar": "https://www.youtube.com/watch?v=zSWdZVtXT7E",
    "The Matrix": "https://www.youtube.com/watch?v=vKQi3bBA1y8",
    "Yarına Tek Bilet": "https://www.youtube.com/watch?v=Ctw49atb0f0",
    "Arrival": "https://www.youtube.com/watch?v=tFMo3UJ4B4g",
    "Stranger Things": "https://www.youtube.com/watch?v=b9EkMc79ZSU",
    "Frozen": "https://www.youtube.com/watch?v=TbQm5doF_Uc",
    "Toy Story 3": "https://www.youtube.com/watch?v=JcpWXaA2qeg",
    "Moana": "https://www.youtube.com/watch?v=LKFuXETZUsI",
    "Up": "https://www.youtube.com/watch?v=pkqzFUhGPJg",
    "Niloya": "https://www.youtube.com/watch?v=z7RFLPkhkzA"
}

# Flask uygulamasını başlatıyoruz
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Film/Dizileri database'den alma ve kategorilere ayırma
@app.route("/")
def home():
    conn = get_db_connection()
    top_movies = conn.execute("SELECT * FROM movies ORDER BY IMDB_Rating DESC LIMIT 6").fetchall()
    categories = conn.execute("SELECT DISTINCT Genre FROM movies").fetchall()
    conn.close()

    # Kategorileri liste haline getirme
    category_list = [row['Genre'] for row in categories]

    # Filmlerin fotoğraf yollarını ayarlama
    movies_with_images = []
    for movie in top_movies:
        title_safe = movie['Series_Title'].replace(" ", "_").replace("/", "_") # Dosya ismi olarak kullanılacak film adı için düzenleme
        image_path = f"images/{title_safe}.png"
        movies_with_images.append({
            **dict(movie),
            'image': image_path
        })

    return render_template("index.html", top_movies=movies_with_images, categories=category_list)

# Kategoriye göre filmleri filtreleme
@app.route("/filter")
def filter_movies():
    category = request.args.get('category')
    conn = get_db_connection()
    movies = conn.execute("SELECT * FROM movies WHERE Genre = ?", (category,)).fetchall()
    conn.close()
    movie_list = []
    for movie in movies:
        movie_list.append({
            "Series_Title": movie["Series_Title"],
            "IMDB_Rating": movie["IMDB_Rating"]
        })
    return jsonify(movie_list)

# Login yapma
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()

        if user: # Database'deki user ile girilen user'ın eşleşmesi kontrolü
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return "Invalid username or password."

    return render_template("login.html")

# çıkış yapma
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

#filmleri database'den alma
@app.route("/movies")
def movies_page():
    conn = get_db_connection()
    movies = conn.execute("SELECT * FROM movies").fetchall()
    categories = conn.execute("SELECT DISTINCT Genre FROM movies").fetchall()
    conn.close()
    return render_template(
        "movies.html",
        movies=movies,
        categories=[row['Genre'] for row in categories],
        page_title="All Movies"
    )

# Belirli bir kategoriye ait filmleri listeleme
@app.route("/category/<category_name>")
def category_page(category_name):
    conn = get_db_connection()
    movies = conn.execute("SELECT * FROM movies WHERE Genre LIKE ?", ('%' + category_name + '%',)).fetchall()
    categories = conn.execute("SELECT DISTINCT Genre FROM movies").fetchall()
    conn.close()
    return render_template(
        "movies.html",
        movies=movies,
        categories=[row['Genre'] for row in categories],
        page_title=f"{category_name} Movies"
    )

# film detaylarını gösteren fonksiyon
@app.route("/movie/<title>", methods=["GET", "POST"])
def movie_detail(title):
    conn = get_db_connection()
    movie = conn.execute("SELECT * FROM movies WHERE Series_Title = ?", (title,)).fetchone()

    if not movie:
        conn.close()
        return "Movie not found", 404

    error = None
    user = session.get("user")
    # Bir kullanıcının aynı filme birden fazla yorum yapamaması kontrolü
    if request.method == "POST" and user:
        score = int(request.form["score"])
        comment = request.form["comment"]
        existing = conn.execute(
            'SELECT * FROM reviews WHERE movie_title = ? AND username = ?', (title, user)
        ).fetchone()

        if existing:
            error = "You have already reviewed this movie."
        else:
            conn.execute(
                'INSERT INTO reviews (movie_title, username, score, comment, date) VALUES (?, ?, ?, ?, ?)',
                (title, user, score, comment, datetime.now().strftime("%Y-%m-%d"))
            )
            conn.commit()
            conn.close()
            return redirect(url_for("movie_detail", title=title))

    movie_reviews = conn.execute(
        'SELECT * FROM reviews WHERE movie_title = ?', (title,)
    ).fetchall()
    conn.close()

    trailer_url = TRAILERS.get(movie['Series_Title'], None) 

    return render_template(
        "movie_detail.html",
        movie=movie,
        movie_reviews=movie_reviews,
        error=error,
        trailer_url=trailer_url
    )

# kayıt olma
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        name = request.form["name"]
        surname = request.form["surname"]
        mail = request.form["mail"]
        gender = request.form["gender"]
        birth = int(request.form["birth"])

        conn = get_db_connection()
        existing_user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if existing_user:
            conn.close()
            return "Username already exists."

        conn.execute("""
            INSERT INTO users (username, password, name, surname, mail, gender, birth)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, password, name, surname, mail, gender, birth))
        conn.commit()
        conn.close()

        session["user"] = username 
        return redirect(url_for("home"))

    return render_template("register.html")

#çalıştırma
if __name__ == "__main__":
    app.run(debug=True)
