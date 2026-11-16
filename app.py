from flask import Flask, render_template, request, jsonify
import joblib
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Health check endpoint for Docker and AWS
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "application": "PhishGuard"
    }), 200

# Load Vectorizer
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

vectorizer = joblib.load(
    os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
)

models = {
    "Random Forest": joblib.load(
        os.path.join(MODEL_DIR, "random_forest_model.pkl")
    ),
    "Logistic Regression": joblib.load(
        os.path.join(MODEL_DIR, "logistic_regression_model.pkl")
    ),
    "Naive Bayes": joblib.load(
        os.path.join(MODEL_DIR, "naive_bayes_model.pkl")
    ),
    "Linear SVM": joblib.load(
        os.path.join(MODEL_DIR, "linear_svm_model.pkl")
    )
}

# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ================= Prediction Route =================

@app.route("/predict", methods=["POST"])
def predict():

    url = request.form["url"]

    vector = vectorizer.transform([url])

    results = {}

    for name, model in models.items():

        prediction = model.predict(vector)[0]

        confidence = None

        if hasattr(model, "predict_proba"):
            confidence = round(max(model.predict_proba(vector)[0])*100,2)

        results[name] = {
            "prediction":"Phishing" if prediction==1 else "Safe",
            "confidence":confidence
        }


  # ================= Save Prediction History =================

    history_path = os.path.join(
    BASE_DIR,
    "prediction_logs",
    "history.csv"
)

    os.makedirs("prediction_logs", exist_ok=True)

    row = {
        "Date": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "URL": url,
        "Random Forest": results["Random Forest"]["prediction"],
        "Logistic Regression": results["Logistic Regression"]["prediction"],
        "Naive Bayes": results["Naive Bayes"]["prediction"],
        "Linear SVM": results["Linear SVM"]["prediction"]
    }

    df = pd.DataFrame([row])

    if os.path.exists(history_path):
        df.to_csv(history_path, mode="a", header=False, index=False)
    else:
        df.to_csv(history_path, index=False)
         
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)