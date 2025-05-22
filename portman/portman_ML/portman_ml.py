
from dj_bridge import DSLAMPort
from scripts.profile_recommender import ProfileRecommender


if __name__ == '__main__':
    recommender = ProfileRecommender()
    X_train, X_test, y_train, y_test = recommender.load_and_prepare_data()
    recommender.train(X_train, X_test, y_train, y_test)
    recommender.evaluate(X_test, y_test)
    recommender.save_model()
    recommender.predict_new(X_test.head())
