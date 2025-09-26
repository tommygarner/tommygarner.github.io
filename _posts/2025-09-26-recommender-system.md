---
layout: post
title: Crowdsourced Recommender System for Music Albums
categories: [Data Science, NLP]
tags: [python, machine-learning, nlp, recommender-system]
---

# Crowdsourced Recommender System for Music Albums

This project focused on building a personalized music album recommender system that moves beyond simple user ratings. By leveraging web scraping and advanced Natural Language Processing (NLP) techniques, the system provides recommendations based on a user's desired musical attributes, such as mood, instrumentation, or lyrical content.

---

## Data Acquisition and Preprocessing

The project began with building a robust web scraper to collect over 8,000 album reviews from rateyourmusic.com. The data was then rigorously cleaned to ensure quality and consistency for model training.

- **Web Scraping:** Used `undetected_chromedriver` and `BeautifulSoup` to bypass bot detection and extract album review data.
- **Data Cleaning:** Handled missing values, tokenized text, and converted non-English reviews to English using `argostranslate`.

A simple preprocessing function looked like this:

```python
import re
from argostranslate import package, translate

def clean_reviews(text):
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Convert to lowercase
    text = text.lower()
    # Handle translation if review is not English
    if not is_english(text):
        translated_text = translate.translate(text, 'en')
        return translated_text
    return text
```

## Recommendation Methodology

Three distinct recommendation methods were explored and compared to find the most effective approach for attribute-based recommendations.

### 1. TF-IDF + Sentiment Analysis

This method combined `TF-IDF` cosine similarity with a VADER sentiment score. Albums were recommended if their reviews contained high-frequency keywords that matched the user's query and had a positive sentiment, ensuring relevant and well-regarded suggestions.

### 2. Pre-trained Word Embeddings

Using spaCy's pre-trained word vectors, this approach recommended albums by finding the closest semantic match to the user's query. This allowed for more conceptual recommendations beyond direct keyword matching.

### 3. Custom Word Embeddings (Word2Vec)

The most effective method involved training a custom `Word2Vec` model on the scraped album review corpus. This model learned the specific nuances and relationships between musical terms used in the reviews, leading to highly relevant and context-specific recommendations.

```python
from gensim.models import Word2Vec

# Assume 'tokenized_reviews' is a list of tokenized sentences
model = Word2Vec(sentences=tokenized_reviews, 
                 vector_size=100, 
                 window=5, 
                 min_count=1, 
                 workers=4)

# Example of finding similar words based on the custom model
similar_words = model.wv.most_similar('guitar')
```

## Analysis & Conclusion

| method | album_name | artist | n_reviews | avg_rating | tfidf + sent score | similarity_spacy | similarity_emb |
|---|---|---|---|---|---|---|---|
| TF-IDF+sent | The Thief Next to Jesus | Ka | 9 | 3.888889 | 0.357302 | NaN | NaN |
| TF-IDF+sent | Dots and Loops | Stereolab | 8 | 4.437500 | 0.354284 | NaN | NaN |
| TF-IDF+sent | Bleeds | Wednesday | 16 | 3.875000 | 0.351459 | NaN | NaN |
| spaCy-pretrained | Winged Victory | Willi Carlisle | 4 | 3.500000 | NaN | 0.623368 | NaN |
| spaCy-pretrained | Night Reign | Arooj Aftab | 9 | 3.666667 | NaN | 0.618952 | NaN |
| spaCy-pretrained | A Single Flower | We Lost the Sea | 4 | 4.250000 | NaN | 0.616543 | NaN |
| Custom-W2V | XII: A gyönyörű álmok ezután jönnek | Thy Catafalque | 9 | 4.000000 | NaN | NaN | 0.884650 |
| Custom-W2V | Blue Heeler in Ugly Snowlight, Grey on Gray on... | Kitchen | 3 | 4.000000 | NaN | NaN | 0.883030 |
| Custom-W2V | Winged Victory | Willi Carlisle | 4 | 3.500000 | NaN | NaN | 0.880547 |

A comparative analysis of the three methods demonstrated that the custom `Word2Vec` model provided the most accurate and context-aware recommendations. It successfully captured the unique vocabulary of music reviews, outperforming generic models that were not trained on this specific domain. Furthermore, the project showed how using mean-centered word vectors could improve the discrimination of similarity scores, leading to a more refined ranking of recommended albums.

---

## Technologies Used

* **Programming Language:** Python
* **Libraries:** `Pandas`, `NumPy`, `scikit-learn`, `BeautifulSoup`, `undetected_chromedriver`, `argostranslate`, `spaCy`, `Gensim`
