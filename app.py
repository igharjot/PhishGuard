
from flask import Flask, render_template, request, jsonify
import joblib
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Application directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
LOG_DIR = os.path.join(BASE_DIR, "prediction_logs")

os.makedirs(LOG_DIR, exist_ok=True)


# Health check endpoint
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "application": "PhishGuard"
    }), 200


# Load TF-IDF Vectorizer
vectorizer = joblib.load(
    os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
)

# Load trained ML models
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

print("\n========== MODEL LABEL DIAGNOSTICS ==========")

for name, model in models.items():
    print(f"{name}: {model.classes_}")

print("=============================================\n")

# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Prediction endpoint

@app.route("/predict", methods=["POST"])
def predict():

    url = request.form.get("url", "").strip()

    if not url:
        return jsonify({
            "error": "URL is required"
        }), 400

    vector = vectorizer.transform([url])

    results = {}

    for name, model in models.items():

        raw_prediction = model.predict(vector)[0]

        # Convert actual model labels into application labels
        if str(raw_prediction).lower() == "bad":
            prediction = "Phishing"

        elif str(raw_prediction).lower() == "good":
            prediction = "Safe"

        else:
            # Do not silently assume unknown labels mean Safe
            return jsonify({
                "error": f"Unknown prediction label from {name}: {raw_prediction}"
            }), 500

        confidence = None

        # Calculate confidence using the probability
        # of the GOOD (Safe) class, as in the original code
        if hasattr(model, "predict_proba"):

            probabilities = model.predict_proba(vector)[0]

            classes = [str(c).lower() for c in model.classes_]

            if "good" in classes:
                good_index = classes.index("good")

                confidence = round(
                    probabilities[good_index] * 100,
                    2
                )

        results[name] = {
            "prediction": prediction,
            "confidence": confidence
        }

    # Save prediction history
    history_path = os.path.join(LOG_DIR, "history.csv")

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
        df.to_csv(
            history_path,
            mode="a",
            header=False,
            index=False
        )
    else:
        df.to_csv(
            history_path,
            index=False
        )

    return jsonify(results)


# Local development only
# Production uses Gunicorn
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
