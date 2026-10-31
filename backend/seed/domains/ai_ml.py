"""AI & ML: how machines learn from data, from the maths and classic models to neural networks and LLMs.

Builds on Data Science (correlation, pandas, data cleaning) and Python (web APIs). Linear
Regression is defined here and shared with Data Science. What Is Machine Learning? and Linear
Algebra for ML are starting topics.
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- Foundations of ML ------------------------------------------------------------------
    Topic(
        "ml_what_is_ml", "What Is Machine Learning?",
        "What machine learning is and isn't: learning patterns from examples instead of writing "
        "rules, supervised, unsupervised and reinforcement learning, features and labels, and "
        "training versus prediction.",
        1,
        (
            docs("Google for Developers: What is machine learning?", "https://developers.google.com/machine-learning/intro-to-ml/what-is-ml"),
            article("Python Data Science Handbook: What is machine learning?", "https://jakevdp.github.io/PythonDataScienceHandbook/05.01-what-is-machine-learning.html"),
            article("IBM: What is machine learning?", "https://www.ibm.com/think/topics/machine-learning"),
        ),
    ),
    Topic(
        "ml_linear_algebra", "Linear Algebra for ML",
        "The maths of data as vectors and matrices: vectors, dot products and what they measure, "
        "matrix multiplication and shapes, and how a dataset becomes a matrix of examples by "
        "features.",
        2,
        (
            video("Vectors: Essence of linear algebra, chapter 1 (3Blue1Brown)", "https://www.youtube.com/watch?v=fNk_zzaMoSs"),
            video("Linear transformations and matrices (3Blue1Brown)", "https://www.youtube.com/watch?v=kYB8IZa5AuE"),
            article("Mathematics for Machine Learning (free book)", "https://mml-book.github.io/"),
        ),
    ),
    Topic(
        "ml_calculus", "Calculus for ML",
        "Derivatives for machine learning: a derivative as a rate of change, partial derivatives and "
        "the gradient, the chain rule, and why the gradient points uphill.",
        3,
        (
            video("The essence of calculus (3Blue1Brown)", "https://www.youtube.com/watch?v=WUvTyaaNkzM"),
        ),
    ),
    Topic(
        "ml_train_test", "Training, Validation & Test Sets",
        "Measuring how well a model generalises: splitting data into training, validation and test "
        "sets, cross-validation, and keeping the test set untouched until the end.",
        2,
        (
            article("Python Data Science Handbook: Hyperparameters and model validation", "https://jakevdp.github.io/PythonDataScienceHandbook/05.03-hyperparameters-and-model-validation.html"),
            docs("scikit-learn: Cross-validation", "https://scikit-learn.org/stable/modules/cross_validation.html"),
            video("Machine Learning Fundamentals: Cross Validation (StatQuest)", "https://www.youtube.com/watch?v=fSytzGwwBVw"),
        ),
    ),
    # --- Classic models -----------------------------------------------------------------------
    Topic(
        "ml_linear_regression", "Linear Regression",
        "Predicting a number with a straight line: the model's weights and bias, residuals and mean "
        "squared error, fitting by least squares, and reading the coefficients.",
        2,
        (
            docs("Google ML Crash Course: Linear regression", "https://developers.google.com/machine-learning/crash-course/linear-regression"),
            video("Linear Regression, Clearly Explained (StatQuest)", "https://www.youtube.com/watch?v=nk2CQITm_eo"),
            article("Python Data Science Handbook: Linear regression", "https://jakevdp.github.io/PythonDataScienceHandbook/05.06-linear-regression.html"),
        ),
    ),
    Topic(
        "ml_logistic_regression", "Logistic Regression & Classification",
        "Predicting a category: the sigmoid function turning a score into a probability, log loss, "
        "decision thresholds, and extending to several classes.",
        3,
        (
            docs("Google ML Crash Course: Logistic regression", "https://developers.google.com/machine-learning/crash-course/logistic-regression"),
            video("StatQuest: Logistic Regression", "https://www.youtube.com/watch?v=yIYKR4sgzI8"),
        ),
    ),
    Topic(
        "ml_evaluation_metrics", "Evaluation Metrics",
        "Judging a model by the right number: the confusion matrix, accuracy and why it misleads on "
        "imbalanced data, precision, recall and F1, ROC curves, and error measures for regression.",
        3,
        (
            docs("Google ML Crash Course: Accuracy, recall and precision", "https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall"),
            video("Machine Learning Fundamentals: The Confusion Matrix (StatQuest)", "https://www.youtube.com/watch?v=Kdsp6soqA7o"),
            docs("scikit-learn: Metrics and scoring", "https://scikit-learn.org/stable/modules/model_evaluation.html"),
        ),
    ),
    Topic(
        "ml_overfitting", "Overfitting & Regularisation",
        "When a model memorises instead of learning: overfitting and underfitting, the bias-variance "
        "trade-off, learning curves, and regularisation with L1 and L2 penalties.",
        3,
        (
            docs("Google ML Crash Course: Datasets, generalisation and overfitting", "https://developers.google.com/machine-learning/crash-course/overfitting"),
            docs("Google ML Crash Course: L2 regularisation", "https://developers.google.com/machine-learning/crash-course/overfitting/regularization"),
            video("Machine Learning Fundamentals: Bias and Variance (StatQuest)", "https://www.youtube.com/watch?v=EuBBz3bI-aA"),
        ),
    ),
    Topic(
        "ml_gradient_descent", "Gradient Descent",
        "How models learn their weights: the loss surface, stepping against the gradient, the "
        "learning rate and what happens when it is too big or too small, and batch, mini-batch and "
        "stochastic variants.",
        3,
        (
            docs("Google ML Crash Course: Gradient descent", "https://developers.google.com/machine-learning/crash-course/linear-regression/gradient-descent"),
            video("Gradient Descent, Step-by-Step (StatQuest)", "https://www.youtube.com/watch?v=sDv4f4s2SB8"),
        ),
    ),
    Topic(
        "ml_scikit_learn", "Machine Learning with scikit-learn",
        "Building models with scikit-learn: the fit and predict pattern, estimators and "
        "transformers, splitting data, pipelines that keep preprocessing and the model together, "
        "and scoring.",
        3,
        (
            docs("scikit-learn: Getting started", "https://scikit-learn.org/stable/getting_started.html"),
            article("Python Data Science Handbook: Introducing scikit-learn", "https://jakevdp.github.io/PythonDataScienceHandbook/05.02-introducing-scikit-learn.html"),
            article("Kaggle Learn: Intro to machine learning", "https://www.kaggle.com/learn/intro-to-machine-learning"),
        ),
    ),
    Topic(
        "ml_feature_engineering", "Feature Engineering",
        "Preparing inputs a model can use: scaling numbers, one-hot encoding categories, handling "
        "missing values, creating new features, and avoiding data leakage from the test set.",
        3,
        (
            docs("scikit-learn: Preprocessing data", "https://scikit-learn.org/stable/modules/preprocessing.html"),
            docs("scikit-learn: Common pitfalls (data leakage)", "https://scikit-learn.org/stable/common_pitfalls.html"),
            article("Kaggle Learn: Feature engineering", "https://www.kaggle.com/learn/feature-engineering"),
        ),
    ),
    Topic(
        "ml_decision_trees", "Decision Trees & Random Forests",
        "Models that ask a series of questions: how a tree chooses its splits, depth and "
        "overfitting, and random forests that combine many trees trained on random samples of rows "
        "and features.",
        3,
        (
            video("Decision and Classification Trees, Clearly Explained (StatQuest)", "https://www.youtube.com/watch?v=_L39rN6gz7Y"),
            video("StatQuest: Random Forests Part 1", "https://www.youtube.com/watch?v=J4Wdy0Wc_xQ"),
            docs("scikit-learn: Decision trees", "https://scikit-learn.org/stable/modules/tree.html"),
        ),
    ),
    Topic(
        "ml_clustering", "Clustering with k-Means",
        "Finding groups in unlabelled data: k-means step by step, choosing k, why scaling matters "
        "for distances, and the limits of round clusters.",
        3,
        (
            docs("Google for Developers: What is k-means clustering?", "https://developers.google.com/machine-learning/clustering/kmeans/overview"),
            video("StatQuest: K-means clustering", "https://www.youtube.com/watch?v=4b5d3muPQmA"),
            article("Python Data Science Handbook: k-means clustering", "https://jakevdp.github.io/PythonDataScienceHandbook/05.11-k-means.html"),
        ),
    ),
    Topic(
        "ml_pca", "Dimensionality Reduction (PCA)",
        "Reducing many features to a few: principal components as directions of greatest variance, "
        "explained variance, and using PCA to visualise data and speed up models.",
        4,
        (
            video("Principal Component Analysis (PCA), Step-by-Step (StatQuest)", "https://www.youtube.com/watch?v=FgakZw6K1QQ"),
            article("Python Data Science Handbook: Principal component analysis", "https://jakevdp.github.io/PythonDataScienceHandbook/05.09-principal-component-analysis.html"),
            docs("scikit-learn: Decomposing signals in components", "https://scikit-learn.org/stable/modules/decomposition.html"),
        ),
    ),
    # --- Deep learning ------------------------------------------------------------------------
    Topic(
        "ml_neural_networks", "Neural Network Basics",
        "How a neural network computes: neurons as weighted sums, activation functions such as ReLU "
        "and sigmoid, layers, and why stacking non-linear layers lets it learn complex patterns.",
        3,
        (
            video("But what is a neural network? (3Blue1Brown)", "https://www.youtube.com/watch?v=aircAruvnKk"),
            docs("Google ML Crash Course: Neural networks", "https://developers.google.com/machine-learning/crash-course/neural-networks"),
            video("The Essential Main Ideas of Neural Networks (StatQuest)", "https://www.youtube.com/watch?v=CqOfi41LfDw"),
        ),
    ),
    Topic(
        "ml_training_nn", "Training Neural Networks",
        "Training deep networks in practice: backpropagation, epochs and mini-batches, choosing a "
        "learning rate, watching validation loss, and dropout and early stopping against "
        "overfitting.",
        4,
        (
            video("Backpropagation, intuitively (3Blue1Brown)", "https://www.youtube.com/watch?v=Ilg3gGewQ5U"),
            docs("PyTorch: Learn the basics", "https://docs.pytorch.org/tutorials/beginner/basics/intro.html"),
            video("Gradient descent, how neural networks learn (3Blue1Brown)", "https://www.youtube.com/watch?v=IHZwWFHWa-w"),
        ),
    ),
    Topic(
        "ml_cnn", "Convolutional Neural Networks",
        "Neural networks for images: convolution filters that detect local patterns, stride and "
        "padding, pooling, feature maps, and why sharing weights needs far fewer parameters than "
        "dense layers.",
        4,
        (
            article("CS231n: Convolutional neural networks", "https://cs231n.github.io/convolutional-networks/"),
            video("But what is a convolution? (3Blue1Brown)", "https://www.youtube.com/watch?v=KuXjwB4LzSA"),
        ),
    ),
    Topic(
        "ml_embeddings", "Text, Tokens & Embeddings",
        "Turning text into numbers: tokenising into words or sub-words, embeddings that place "
        "similar meanings close together, cosine similarity, and how embeddings power search.",
        4,
        (
            docs("Hugging Face LLM Course: Tokenizers", "https://huggingface.co/learn/llm-course/chapter2/4"),
            docs("Google ML Crash Course: Embeddings", "https://developers.google.com/machine-learning/crash-course/embeddings"),
            article("Jay Alammar: The illustrated Word2vec", "https://jalammar.github.io/illustrated-word2vec/"),
        ),
    ),
    Topic(
        "ml_transformers", "Transformers & Large Language Models",
        "The architecture behind modern language models: self-attention, positional information, "
        "predicting the next token, pre-training and fine-tuning, and the context window.",
        4,
        (
            article("Jay Alammar: The illustrated Transformer", "https://jalammar.github.io/illustrated-transformer/"),
            video("Transformers, the tech behind LLMs (3Blue1Brown)", "https://www.youtube.com/watch?v=wjZofJX0v4M"),
            docs("Hugging Face LLM Course: How do Transformers work?", "https://huggingface.co/learn/llm-course/chapter1/4"),
        ),
    ),
    # --- Using AI -------------------------------------------------------------------------------
    Topic(
        "ml_llm_apis", "Building with LLM APIs",
        "Using a language model from code: sending messages to a chat API, system prompts, "
        "temperature, tokens and cost, asking for structured output, and checking answers because "
        "models can be confidently wrong.",
        3,
        (
            article("Prompt Engineering Guide", "https://www.promptingguide.ai/"),
            docs("Google AI for Developers: Prompt design strategies", "https://ai.google.dev/gemini-api/docs/prompting-strategies"),
            docs("Claude docs: Prompt engineering overview", "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview"),
        ),
    ),
    Topic(
        "ml_responsible_ai", "Responsible AI",
        "Building AI that treats people fairly: bias in data and models, checking results across "
        "groups, privacy, being open about what a model can't do, and keeping people in charge of "
        "important decisions.",
        2,
        (
            docs("Google ML Crash Course: Fairness", "https://developers.google.com/machine-learning/crash-course/fairness"),
            article("IBM: What is AI ethics?", "https://www.ibm.com/think/topics/ai-ethics"),
            docs("NIST: AI Risk Management Framework", "https://www.nist.gov/itl/ai-risk-management-framework"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("ml_what_is_ml", "ml_linear_regression"),
    ("ds_correlation", "ml_linear_regression"),
    ("ml_linear_algebra", "ml_calculus"),
    ("ml_what_is_ml", "ml_train_test"),
    ("ml_linear_regression", "ml_logistic_regression"),
    ("ml_train_test", "ml_overfitting"),
    ("ml_linear_regression", "ml_overfitting"),
    ("ml_logistic_regression", "ml_evaluation_metrics"),
    ("ml_train_test", "ml_evaluation_metrics"),
    ("ml_calculus", "ml_gradient_descent"),
    ("ml_linear_regression", "ml_gradient_descent"),

    ("ds_pandas_basics", "ml_scikit_learn"),
    ("ml_train_test", "ml_scikit_learn"),
    ("ds_data_cleaning", "ml_feature_engineering"),
    ("ml_scikit_learn", "ml_feature_engineering"),
    ("ml_evaluation_metrics", "ml_decision_trees"),
    ("ml_what_is_ml", "ml_clustering"),
    ("ml_linear_algebra", "ml_clustering"),
    ("ml_linear_algebra", "ml_pca"),
    ("ml_feature_engineering", "ml_pca"),

    ("ml_gradient_descent", "ml_neural_networks"),
    ("ml_logistic_regression", "ml_neural_networks"),
    ("ml_neural_networks", "ml_training_nn"),
    ("ml_overfitting", "ml_training_nn"),
    ("ml_training_nn", "ml_cnn"),
    ("ml_neural_networks", "ml_embeddings"),
    ("ml_embeddings", "ml_transformers"),
    ("ml_training_nn", "ml_transformers"),

    ("python_http_requests", "ml_llm_apis"),
    ("ml_what_is_ml", "ml_llm_apis"),
    ("ml_what_is_ml", "ml_responsible_ai"),
)

AI_ML = Domain(
    id="ai-ml",
    name="AI & ML",
    description=(
        "How machines learn from data: the maths behind it, classic models with scikit-learn, "
        "evaluating them honestly, neural networks and language models, and using AI responsibly."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
)
