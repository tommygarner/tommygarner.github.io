---
layout: default
title: Crowdsourced Recommender System for Music Albums
---

# Introduction

This project focused on building a personalized music album recommender system that moves beyond simple user ratings. By utilizing web scraping and advanced Natural Language Processing (NLP), this recommender algorithm outputs recommendations based on a user's desired musical attributes, such as mood, instrumentation, or lyrical content.

Our team wanted to explore how recommender systems could help expose "long-tail" products. In the music industry, this looks like a handful of songs making top charts or radio hits, while many great songs go unnoticed by mainstream media, and therefore, listeners. To increase music discovery, we wanted to build a model that would take user preferences as input and output albums that match what users are looking for in their albums!

---

## Scraping the Crowd, 

The project began with building a robust web scraper to collect over 8,000 album reviews from rateyourmusic.com, a large crowdsourced music database where fans share opinions and reviews on albums across hundreds of genres. 

The hardest part was up next: cleaning text data.

First, I normalized the text, lowercasing all words to make inputs simple and standardized for NLP. Second, I stripped punctuation, numbers, characters, and tags that served as noise for future word embeddings. Third, I decided to take on translating reviews from other languages (such as French, German, and Spanish) into English. I used `argostranslate`, an open-sourced neural translation library, to both detect non-English words and translate them into English, that way the future Word2Vec model could learn upon a unified corpus. Finally, I tokenized the cleaned text, transforming these large reviews into lists of terms that could be transformed into embeddings, or numerical representations of words.

## Recommendation Methodology

To recommend music albums not just by genre or plays, but by personalized attributes like mood, lyrical style, or instrumentation, I compared three different approaches. Each method was aimed at answering the question: "How do we capture the real fanbase in reviews and turn that into smart recommendations?"

**Example user query:**
For instance, I tested all three models on an end-user query targeting a pallete of:
-  Writing style: content-rich
-  Instrumentation: guitars
-  Mood: spacy

Think Pink Floyd, psychedelic rock, or indie rock (my favorite!). These attributes represent what a listener might articulate when trying to discover a niche of new music.

### 1. Classic Approach: TF-IDF + Sentiment Analysis

This method used frequency-based scoring (TF-IDF) to identify reviews that most strongly mention a user's target attributes ("guitar", "spacy"). By computing cosine similarity, I ranked albums by how often their reviews overlapped with the previous query terms. Additionally, I filtered candidate albums by positive sentiment using VADER to avoid recommending poor albums to the user.

The limitation of this model was that TF-IDF simply catches only exact pairings, and therefore cannot flag synonyms and context. For example, "ethereal" doesn't correlate to "spacy" in this approach.

```
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.sentiment import SentimentIntensityAnalyzer

# 1. Build TF-IDF vectors for all album reviews
tfv_uni = TfidfVectorizer(tokenizer=tokenize_unigrams, 
                          ngram_range=(1,1), 
                          min_df=5, 
                          max_df=0.7)
X_uni = tfv_uni.fit_transform(agg['doc'])

# 2. Build weighted query from attribute keywords
query_text = ' '.join(q_toks)  # e.g., "content space guitars"
q = tfv_uni.transform([query_text])

# 3. Compute cosine similarity
sim = cosine_similarity(q, X_uni).ravel()

# 4. Calculate sentiment scores with VADER
sia = SentimentIntensityAnalyzer()
sentiment_scores = [sia.polarity_scores(text)['compound'] 
                    for text in album_reviews]

# 5. Combine similarity and sentiment
alpha = 0.7
final_score = alpha * sim + (1 - alpha) * sentiment_scores
```

### 2. Semantic Matching: Pre-trained Word Embeddings (spaCy)

Using spaCy's pre-trained word vectors, this approach recommended albums by finding the closest semantic match to the user's query. This allowed for more conceptual recommendations beyond direct keyword matching.

### 3. Context-Aware Recommendations: Custom Word Embeddings (Word2Vec)

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
