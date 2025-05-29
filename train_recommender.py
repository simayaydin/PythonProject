import sqlite3
import pandas as pd
from lightfm import LightFM
from lightfm.data import Dataset
import pickle

try:
    conn = sqlite3.connect("database.db")
    df_reviews = pd.read_sql_query("SELECT username, movie_title, score FROM reviews", conn)
    df_movies = pd.read_sql_query("SELECT Series_Title, Genre FROM movies", conn)
    conn.close()

    if df_reviews.empty:
        print("⚠️ Uyarı: reviews tablosunda hiç veri yok!")
        exit()

    print(f"✅ {len(df_reviews)} satır veri bulundu. Model eğitimi başlatılıyor...")

    if len(df_reviews) < 20:
        print("🧪 Veri çok küçük, test için çoğaltılıyor (x100)...")
        df_reviews = pd.concat([df_reviews] * 100, ignore_index=True)

    dataset = Dataset()
    all_users = df_reviews["username"].unique()
    all_items = df_reviews["movie_title"].unique()

    df_movies = df_movies.dropna()
    df_movies = df_movies[df_movies["Series_Title"].isin(all_items)]
    item_features_list = list(set(df_movies["Genre"]))

    dataset.fit(
        users=all_users,
        items=all_items,
        item_features=item_features_list
    )

    interactions, _ = dataset.build_interactions([
        (row["username"], row["movie_title"], float(row["score"]))
        for _, row in df_reviews.iterrows()
    ])

    item_features = dataset.build_item_features([
        (row["Series_Title"], [row["Genre"]])
        for _, row in df_movies.iterrows()
    ])

    print("📐 Interaction matrix shape:", interactions.shape)
    print("👥 Kullanıcı sayısı:", len(all_users))
    print("🎬 Film sayısı:", len(all_items))

    model = LightFM(loss="warp")

    print("🔁 Eğitim başlıyor (tek çekirdekli)...")
    model.fit(interactions, item_features=item_features, epochs=5, num_threads=1)
    print("✅ Eğitim tamamlandı.")

    print("💾 Dosya kaydediliyor...")
    with open("recommender_model.pkl", "wb") as f:
        pickle.dump((model, dataset), f)
    print("✅ Model başarıyla kaydedildi: recommender_model.pkl")

except Exception as e:
    print(f"❌ Genel hata oluştu: {e}")
