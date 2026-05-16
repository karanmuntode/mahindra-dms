from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def recommend_docs(documents, query):
    if not documents or not query:
        return []
    try:
        texts = [f"{d.part_no} {d.unique_id} {d.doc_type}" for d in documents]
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(texts + [query])
        similarity = cosine_similarity(vectors[-1], vectors[:-1])
        ranked = similarity[0].argsort()[::-1]
        return [documents[i] for i in ranked[:5]]
    except Exception as e:
        print("Recommend error:", e)
        return documents[:5]
