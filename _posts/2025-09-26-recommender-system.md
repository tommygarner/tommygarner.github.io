---
layout: default
title: Crowdsourced Recommender System for Music Albums
---

# Introduction

This project focused on building a personalized music album recommender system that moves beyond simple user ratings. By utilizing web scraping and advanced Natural Language Processing (NLP), this recommender algorithm outputs recommendations based on a user's desired musical attributes, such as mood, instrumentation, or lyrical content.

Our team wanted to explore how recommender systems could help expose "long-tail" products. In the music industry, this looks like a handful of songs making top charts or radio hits, while many great songs go unnoticed by mainstream media, and therefore, listeners. To increase music discovery, we wanted to build a model that would take user preferences as input and output albums that match what users are looking for in their albums!

---

## Scraping the Crowd

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

Next I wanted to begin modeling with word vectors, so I decided to incorporate spaCy's pre-trained word vectors. By turning each album's reviews and the user's query into embeddings, I recommended albums whose reviews conceptually matched the query in vector space, even if the exact wording was different. This model makes up for the limitation of the previous TF-IDF model. However, these pre-trained word embeddings are built upon spaCy's corpus, which is the `en_core_web_md` model containing over 20k unique word vectors in 300-dimension space.

These embeddings are trained on commonly written web English such as blogs, news, or product reviews. But what if we could make these embeddings specific to our context?

```
import spacy

# Load pre-trained spaCy model with word vectors
nlp = spacy.load('en_core_web_md')

# Get query embedding
query_embedding = nlp(user_query).vector

# Get album review embeddings
review_embeddings = [nlp(review).vector for review in album_reviews]

# Compute cosine similarity
from sklearn.metrics.pairwise import cosine_similarity
similarities = cosine_similarity([query_embedding], review_embeddings)
```

### 3. Context-Aware Recommendations: Custom Word Embeddings (Word2Vec)

This model was the most effective as the embeddings were created based on our domain-specific reviews corpus. I trained a Word2Vec model directly on these 8k user reviews, learning the relationships, slang, and other expressions particular to music fans. This contextual model was able to make approximate connections in vector space, where albums are suggested by reviewer vocabular and meaning. 

This model proved to be most accurate as it caught most of the nuances the previous models could not, but it also requires a large corpus of text to train on, and possible 8k reviews wasn't enough!

```
from gensim.models import Word2Vec
import numpy as np

# 1. Train custom Word2Vec on tokenized reviews
w2v = Word2Vec(sentences=tokenized_reviews, 
               vector_size=100, 
               window=5, 
               min_count=2, 
               workers=4)

# 2. Create TF-IDF weighted document embeddings
def doc_embedding_weighted(text: str):
    toks = tokenize_unigrams(text)
    weights, vecs = [], []
    
    for t in toks:
        if t in w2v.wv and t in idf_map:
            weights.append(idf_map[t])
            vecs.append(w2v.wv[t])
    
    if not vecs:
        return None
    W = np.asarray(weights, float)
    V = np.vstack(vecs)
    return (V * W[:,None]).sum(axis=0) / (W.sum() + 1e-9)

# 3. Build query vector from attribute keywords
query_vec = np.average(np.vstack(vecs), axis=0, weights=np.array(weights))

# 4. Compute similarity
sim_emb = cosine_similarity([query_vec], doc_embeddings)
```

## Results

| Method | Album | Artist | Reviews | Avg Rating | Score |
|--------|-------|--------|---------|------------|-------|
| TF-IDF+sent | The Thief Next to Jesus | Ka | 9 | 3.89 | 0.357 |
| TF-IDF+sent | Dots and Loops | Stereolab | 8 | 4.44 | 0.354 |
| TF-IDF+sent | Bleeds | Wednesday | 16 | 3.88 | 0.351 |
| spaCy-pretrained | Winged Victory | Willi Carlisle | 4 | 3.50 | 0.623 |
| spaCy-pretrained | Night Reign | Arooj Aftab | 9 | 3.67 | 0.619 |
| spaCy-pretrained | A Single Flower | We Lost the Sea | 4 | 4.25 | 0.617 |
| Custom-W2V | XII: A gyönyörű álmok ezután jönnek | Thy Catafalque | 9 | 4.00 | 0.885 |
| Custom-W2V | Blue Heeler in Ugly Snowlight... | Kitchen | 3 | 4.00 | 0.883 |
| Custom-W2V | Winged Victory | Willi Carlisle | 4 | 3.50 | 0.881 |

<img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/49e17608-1bbe-42f9-a3a9-cddefa1e9c74" />
<img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/5e144e3f-3d57-4840-9bc6-6b8e67fe1d6f" />
<img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/53731f38-f13c-4345-a97d-7597435f79b4" />




To test each approach, I queried all 3 recommendation systems with the same user requrest and found the top 3 albums. You can see that each model suggests almost entirely different songs with unique scores based on our recommendation logic.

**TF-IDF + Sentiment:**
-  Struggled clearly, showing genre diveristy. Ka and Wednesday are strong artists but don't pair conceptually with the user's query. These artists are more hip-hop and slowcore than guitar-driven or spacy mood. The keyword-matching algo worked, but the model didn't understand context as well as the others. 

**spaCy:**
-  spaCy's model was more semantic in modeling concepts that the keyword pairing missed. We Lost the Sea and Kitchen fit the "spacy" vibe, as these artists are known by post-rock instrumentals and ambient jazz, respectively. Winged Victory is the top recommended album in this model (and shows up in the next), yet has a different similarity score than the custom embeddings model.

**W2V:**
-  The domain-trained model performed great and was able to score much higher than the pre-trained embedding model. Thy Catafalque is known for expansive and guitar-heavy progressive metal. Willie Carlisle's Winged Victory again shows up as recommended. As previously mentioned, the custom Word2Vec model produces a wider range in score, meaning this model can more confidently rank the recommendations because this model understands the music-specific language patterns.

---

## Final Takeaways
I learned that domain adaptation matters in this album-specific context. Training embeddings to music-specific context allows us to understand the nuanced vocabulary of fans, which benefits end users who are given more confident recommendations for their music discovery! 

Likewise, our W2V model recommended Hungarian avant-garde metal, an album that probably never would've entered the user's rotation of music had it not been for the discovery tool.

If I were to take this project further, I would have gathered much more reviews for training, since the above results show that our model relies on albums with only 3 or 4 reviews. Ideally, I'd like to use albums with > 10 reviews, but that would require finding a more popular site and making sure that these albums don't live in the head of the long tail, which negates the whole point of music discovery.

---

## Technologies Used

* **Programming Language:** Python
* **Libraries:** `Pandas`, `NumPy`, `scikit-learn`, `BeautifulSoup`, `undetected_chromedriver`, `argostranslate`, `spaCy`, `Gensim`
