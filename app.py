from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from datetime import datetime
import sqlite3
import os
from lightfm import LightFM
from lightfm.data import Dataset
import pickle
from scipy.sparse import csr_matrix
import pandas as pd



# Veritabanı bağlantısı fonksiyonu
def get_db_connection():
    conn = sqlite3.connect("database.db", timeout=10)
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
# En çok puan alan ünlüleri tutan dictionary
CELEBRITIES = {
    "Leonardo DiCaprio": {"rating": 9.5, "image": "images/Leonardo_DiCaprio.png"},
    "Morgan Freeman": {"rating": 9.4, "image": "images/Morgan_Freeman.png"},
    "Scarlett Johansson": {"rating": 9.3, "image": "images/Scarlett_Johansson.png"},
    "Tom Hanks": {"rating": 9.2, "image": "images/Tom_Hanks.png"},
    "Natalie Portman": {"rating": 9.1, "image": "images/Natalie_Portman.png"},
    "Robert De Niro": {"rating": 9.0, "image": "images/Robert_De_Niro.png"},
}

# Flask uygulamasını başlatıyoruz
app = Flask(__name__)
app.secret_key = 'supersecretkey'
# Modeli ve dataset nesnesini yükle
try:
    with open("recommender_model.pkl", "rb") as f:
        recommender_model, recommender_dataset = pickle.load(f)
    print(" Model yüklendi.")
except Exception as e:
    print(f" Model yüklenemedi: {e}")
    recommender_model, recommender_dataset = None, None


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

    # Celebrities'leri liste haline getiriyoruz
    celebrities_with_images = []
    for name, data in CELEBRITIES.items():
        celebrities_with_images.append({
            "name": name,
            "rating": data["rating"],
            "image": data["image"]
        })

    return render_template(
        "index.html",
        top_movies=movies_with_images,
        categories=category_list,
        celebrities=celebrities_with_images
    )

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
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()

        # kullanıcının veritabanında olup olmadığını kontrol etme
        if user:
            session["user"] = username
            return redirect(url_for("home"))
        else:
            error = "🚫 This user is not registered in the system. Please check your username and password."

    return render_template("login.html", error=error)

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
    # Ortalama puanı ve yorum sayısını hesapla
    avg_row = conn.execute(
        "SELECT AVG(score) AS avg_score, COUNT(*) AS count FROM reviews WHERE movie_title = ?",
        (title,)
    ).fetchone()
    overall_rating = round(avg_row["avg_score"], 1) if avg_row["avg_score"] is not None else None
    review_count = avg_row["count"]

    conn.close()

    trailer_url = TRAILERS.get(movie['Series_Title'], None) 

    return render_template(
        "movie_detail.html",
        movie=movie,
        movie_reviews=movie_reviews,
        overall_rating=overall_rating,
        review_count=review_count,
        error=error,
        trailer_url=trailer_url
    )


# Review düzenleme
@app.route("/edit_review/<int:review_id>", methods=["POST"])
def edit_review(review_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    new_score = int(request.form["score"])
    new_comment = request.form["comment"]

    conn = get_db_connection()
    review = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()

    if review and review["username"] == user:
        conn.execute(
            "UPDATE reviews SET score = ?, comment = ?, date = ? WHERE id = ?",
            (new_score, new_comment, datetime.now().strftime("%Y-%m-%d"), review_id)
        )
        conn.commit()
    conn.close()
    return redirect(url_for("movie_detail", title=review["movie_title"]))

# Watchlist'e film ekleme
@app.route("/add_to_watchlist/<title>", methods=["POST"])
def add_to_watchlist(title):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    conn = get_db_connection()
    existing = conn.execute(
        "SELECT * FROM watchlist WHERE username = ? AND movie_title = ?", (user, title)
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO watchlist (username, movie_title) VALUES (?, ?)", (user, title)
        )
        conn.commit()
    conn.close()
    return redirect(url_for("movie_detail", title=title))

# Watchlist görüntüleme
@app.route("/watchlist")
def watchlist():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    conn = get_db_connection()
    movies = conn.execute(
        "SELECT * FROM watchlist WHERE username = ?", (user,)
    ).fetchall()
    conn.close()
    return render_template("watchlist.html", movies=movies)

# Watchlist'ten silme 
@app.route("/remove_from_watchlist/<int:id>", methods=["POST"])
def remove_from_watchlist(id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM watchlist WHERE id = ? AND username = ?", (id, user))
    conn.commit()
    conn.close()
    return redirect(url_for("watchlist"))

# Review silme
@app.route("/delete_review/<int:review_id>", methods=["POST"])
def delete_review(review_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    conn = get_db_connection()
    review = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()

    if review and review["username"] == user:
        conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
    conn.close()
    return redirect(url_for("movie_detail", title=review["movie_title"]))

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
# Filmleri arama yapma
@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    conn = get_db_connection()
    if query:
        movies = conn.execute("SELECT * FROM movies WHERE Series_Title LIKE ?", (f"%{query}%",)).fetchall()
    else:
        movies = conn.execute("SELECT * FROM movies ORDER BY IMDB_Rating DESC LIMIT 6").fetchall()
    conn.close()

    # Görsel yollarını hazırlayalım
    movies_with_images = []
    for movie in movies:
        title_safe = movie['Series_Title'].replace(" ", "_").replace("/", "_")
        image_path = f"images/{title_safe}.png"
        movies_with_images.append({
            **dict(movie),
            'image': image_path
        })

    # Aynı index.html'i döneceğiz ama sadece sonuçlarla
    categories = [row['Genre'] for row in get_db_connection().execute("SELECT DISTINCT Genre FROM movies").fetchall()]
    conn.close()
    return render_template("index.html", top_movies=movies_with_images, categories=categories, current_category=f'Search: {query}')
    
    #çalıştırma
    if __name__ == "__main__":
        app.run(debug=True, threaded=False)

# === Öneri Sistemi Route'u ===
import pickle
from lightfm import LightFM
from lightfm.data import Dataset
import numpy as np

# Eğitimli modeli başta bir kere yükle (isteğe bağlı olarak global de yapabiliriz)
with open("recommender_model.pkl", "rb") as f:
    recommender_model, recommender_dataset = pickle.load(f)

@app.route("/recommendations")
def recommendations():
    import numpy as np  # Gerekli import

    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]

    try:
        # Model ve dataset yoksa hata ver
        if recommender_model is None or recommender_dataset is None:
            return " Model yüklenemedi."

        # Mapping bilgilerini al
        user_id_map, _, item_id_map, _ = recommender_dataset.mapping()

        if username not in user_id_map:
            return " Bu kullanıcı modele göre tanımlı değil."

        user_id = user_id_map[username]
        n_items = len(item_id_map)

        # Öneri skorlarını hesapla
        scores = recommender_model.predict(user_id, np.arange(n_items))
        top_items = np.argsort(-scores)[:10]

        # ID → Film adı eşlemesi
        reverse_item_map = {v: k for k, v in item_id_map.items()}
        recommended_titles = [reverse_item_map[i] for i in top_items]

        # Veritabanından detaylı bilgileri çek
        conn = sqlite3.connect("database.db")
        movies_df = pd.read_sql_query("SELECT Series_Title, IMDB_Rating FROM movies", conn)
        conn.close()

        # Sadece önerilen filmleri detaylarıyla getir
        recommended_movies = []
        for title in recommended_titles:
            match = movies_df[movies_df["Series_Title"] == title]
            if not match.empty:
                recommended_movies.append({
                    "Series_Title": title,
                    "IMDB_Rating": match.iloc[0]["IMDB_Rating"]
                })

        return render_template("recommendation.html", movies=recommended_movies)

    except Exception as e:
        return f" Öneri alınırken hata oluştu: {e}"
    
if __name__ == "__main__":
    app.run(debug=True)
