import sqlite3
import pandas as pd
from lightfm import LightFM
from lightfm.data import Dataset
import pickle

try:
    # === Veritabanını oku ===
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT username, movie_title, score FROM reviews", conn)
    conn.close()

    if df.empty:
        print("⚠️ Uyarı: reviews tablosunda hiç veri yok!")
        exit()

    print(f"✅ {len(df)} satır veri bulundu. Model eğitimi başlatılıyor...")

    # === Küçük veri için çoğaltma ===
    if len(df) < 20:
        print("🧪 Veri çok küçük, test için çoğaltılıyor (x100)...")
        df = pd.concat([df] * 100, ignore_index=True)

    # === Dataset hazırla ===
    dataset = Dataset()
    dataset.fit(df["username"], df["movie_title"])

    (interactions, weights) = dataset.build_interactions([
        (row["username"], row["movie_title"], float(row["score"]))
        for _, row in df.iterrows()
    ])

    print("📐 Interaction matrix shape:", interactions.shape)
    print("👥 Kullanıcı sayısı:", df['username'].nunique())
    print("🎬 Film sayısı:", df['movie_title'].nunique())

    if interactions.shape[0] < 2 or interactions.shape[1] < 2:
        print("❌ Çok az kullanıcı veya film var. Eğitim yapılamaz.")
        exit()

    # === Model oluştur ===
    model = LightFM(loss="logistic")  # Daha hafif loss ile

    print("🔁 Eğitim başlıyor (tek çekirdekli)...")
    try:
        for epoch in range(1, 5):
            print(f"📦 Epoch {epoch}", flush=True)
            model.fit(interactions, epochs=1, num_threads=1)
        print("✅ Eğitim tamamlandı.")
    except Exception as fit_err:
        print(f"❌ Eğitim sırasında hata oluştu: {fit_err}")
        exit()

    # === Modeli kaydet ===
    print("💾 Dosya kaydediliyor...")
    with open("recommender_model.pkl", "wb") as f:
        pickle.dump((model, dataset), f)
    print("✅ Model başarıyla kaydedildi: recommender_model.pkl")

except Exception as e:
    print(f"❌ Genel hata oluştu: {e}")
