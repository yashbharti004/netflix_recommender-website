from flask import Flask, render_template, request, jsonify
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

app = Flask(__name__)

df = pd.read_csv("flixpatrol_fully_cleaned.csv")
df["Premiere"] = pd.to_numeric(df["Premiere"], errors='coerce')
df["Watchtime in Million"] = df["Watchtime in Million"].str.replace("M", "").astype(float)

@app.route('/')
def index():
    genres = sorted(df["Genre"].dropna().unique())
    return render_template("index.html", genres=genres)

@app.route('/recommend', methods=['POST'])
def recommend():
    movie_type = request.form['type']
    genre = request.form['genre']
    year_start = int(request.form['year_start'])
    year_end = int(request.form['year_end'])
    view_option = request.form['view_option']
    analysis_option = request.form['analysis_option']

    filtered_data = df[
        (df["Type"] == movie_type) &
        (df["Genre"].str.contains(genre, na=False)) &
        (df["Premiere"].between(year_start, year_end, inclusive="both"))
    ]

    if view_option == "Most Viewed":
        filtered_data = filtered_data.sort_values(by="Watchtime in Million", ascending=False)
    else:
        filtered_data = filtered_data.sort_values(by="Watchtime in Million", ascending=True)

    response = {
        "table": filtered_data[["Title", "Genre", "Premiere", "Watchtime in Million"]].head(10).to_dict(orient='records'),
        "insights": [],
        "recommendation": "",
        "feedback": [],
        "plots": []
    }

    if analysis_option == "Netflix Insights":
        response["insights"] = [
            "Find the most popular genre in different regions.",
            "Analyze trends in movie watchtime over the years.",
            "Identify underperforming movies and genres.",
            "Recommend suitable movie categories for different seasons.",
            "Analyze audience preference for new vs. old movies."
        ]
    elif analysis_option == "Movie Purchase Recommendation" and not filtered_data.empty:
        top_movie = filtered_data.iloc[0]
        response["recommendation"] = f"Purchase movies similar to '{top_movie['Title']}' as it has high watchtime in its category."
    elif analysis_option == "Customer Complaints & Suggestions":
        response["feedback"] = [
            "More diversity in content with different genres.",
            "Adding more classic movies based on audience interest.",
            "Increasing availability of highly watched but discontinued shows.",
            "Better regional content selection based on viewing trends.",
            "More frequent updates on trending movie lists."
        ]

    # Add matplotlib plot as base64
    if not filtered_data.empty:
        top_movies = filtered_data[["Title", "Watchtime in Million"]].head(10)

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(top_movies["Title"], top_movies["Watchtime in Million"], color='red', alpha=0.7)
        ax.set_xticklabels(top_movies["Title"], rotation=45, ha="right", fontsize=8)
        ax.set_title("Top 10 Movies by Watchtime")
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        response["plots"].append(f"data:image/png;base64,{image_base64}")

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
