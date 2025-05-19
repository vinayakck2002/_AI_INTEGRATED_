import pandas as pd
# import pickle
from sentence_transformers import SentenceTransformer

# Initialize Sentence-BERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Function to process and vectorize reviews for a course
def process_reviews(reviews):
    """Vectorize each review and return the average vector."""
    if reviews:  # If there are reviews
        review_list = reviews.split(',')  # Split reviews into individual comments
        review_vectors = model.encode(review_list)  # Vectorize each review separately
        review_vector = review_vectors.mean(axis=0)  # Calculate average of review vectors
        return review_vector
    else:
        return None  # No reviews available
    

def process_search(search):
    if search:
        search_list = search.split(',')
        search_vectors = model.encode(search_list)
        search_vector = search_vectors.mean(axis=0)
        return search_vector

# Function to combine product data and reviews to create a vector
def combine_product_with_reviews(product_data):
    """Combine product metadata and the review essence to generate a combined vector."""
    combined_text = f"Product Name: {product_data['name']}, Rating: {product_data['rating']}, " \
                    f"shoe_category: {product_data['shoe_category']}, " \
                    f"Description: {product_data['description']}"
    
    product_vector = model.encode(combined_text)  # Vectorize the course metadata
    review_vector = process_reviews(product_data['reviews'])  # Vectorize the reviews
    
    if review_vector is not None:
        combined_vector = product_vector + review_vector  # Combine the course vector and review vector
    else:
        combined_vector = product_vector  # If no reviews, just use the course data
    print(combined_vector)
    return combined_vector


# Vectorize all courses with reviews
def vectorize_product_with_reviews(df):
    """Vectorize all product in the dataframe."""
    product_vectors = []
    for _, product in df.iterrows():
        product_vector = combine_product_with_reviews(product)
        product_vectors.append(product_vector)
    return product_vectors

def combine_user_with_search(user_data):
    combined_text = f"user_id: {user_data['user_id']},  " \
                    f"product: {user_data['product']}, " 
    user_vector = model.encode(combined_text)
    search_vector = process_search(user_data['search'])
    if search_vector is not None:
        combined_vector = user_vector + search_vector
    else:
        combined_vector = user_vector
    return combined_vector
def vectorize_user_with_search(df): 
    user_vectors = []    
    for _, user in df.iterrows():
        user_vector = combine_user_with_search(user)
        user_vectors.append(user_vector)
    return user_vectors