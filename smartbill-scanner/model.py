import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "vectorizer.pkl")

def train_and_save_model(csv_path='training_data.csv'):
    df = pd.read_csv(os.path.join(BASE_DIR, csv_path))
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df['item'])
    y = df['category']
    model = MultinomialNB()
    model.fit(X, y)
    # Save model and vectorizer
    import joblib
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

def load_model_and_vectorizer():
    import joblib
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    return model, vectorizer

def predict_category(item, model, vectorizer):
    X_item = vectorizer.transform([item])
    return model.predict(X_item)[0] 