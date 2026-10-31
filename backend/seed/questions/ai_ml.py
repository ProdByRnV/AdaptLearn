"""Curated fallback questions for AI & ML. Code is Markdown; maths is LaTeX between \\( and \\)."""

from seed.questions import Bank, q

QUESTIONS: Bank = {
    # --- Foundations of ML ------------------------------------------------------------------
    "ml_what_is_ml": [
        q("A model learns from emails already marked spam or not spam. What kind of learning is this?",
          "Supervised learning", ("Unsupervised learning", "Reinforcement learning", "Rule-based programming"),
          "Learning from examples that come with the right answer (labels) is supervised learning."),
        q("A model predicts house prices from size and location. What are size and location?", "Features",
          ("Labels", "Weights", "Hyperparameters"),
          "Features are the inputs; the label is what is predicted (the price). Weights are learned, and "
          "hyperparameters are chosen before training."),
        q("Grouping customers by their behaviour, with no labels to learn from, is an example of what?",
          "Unsupervised learning", ("Supervised learning", "Reinforcement learning", "Regression"),
          "Finding structure in unlabelled data, such as clusters, is unsupervised learning."),
    ],
    "ml_linear_algebra": [
        q("What is the dot product of \\( (1, 2, 3) \\) and \\( (4, 5, 6) \\)?", "32", ("21", "(4, 10, 18)", "15"),
          "Multiply matching entries and add: \\( 1 \\cdot 4 + 2 \\cdot 5 + 3 \\cdot 6 = 4 + 10 + 18 = 32 \\). "
          "The result is a single number, not a vector."),
        q("Matrix A has shape 3 × 2 and matrix B has shape 2 × 4. What is the shape of AB?", "3 × 4",
          ("2 × 2", "3 × 2", "It can't be computed"),
          "The inner sizes (2 and 2) must match and disappear; the result takes the outer sizes, 3 rows by 4 columns."),
        q("A dataset has 500 examples and 8 features. As a matrix with one row per example, what is its shape?",
          "500 × 8", ("8 × 500", "500 × 1", "4,000 × 1"),
          "Rows are examples and columns are features, so the matrix has 500 rows and 8 columns."),
    ],
    "ml_calculus": [
        q("What is the derivative of \\( f(x) = x^2 \\) at \\( x = 3 \\)?", "6", ("9", "3", "2"),
          "The derivative of \\( x^2 \\) is \\( 2x \\), which is 6 at \\( x = 3 \\): the slope of the curve there. "
          "9 is the value of the function itself."),
        q("What does the gradient of a function of several variables point towards?",
          "The direction in which the function increases fastest",
          ("The lowest point the function can reach", "The direction in which the function stays constant",
           "The variable that has the largest value"),
          "The gradient collects the partial derivatives into a vector pointing uphill. Gradient descent steps "
          "the other way to reduce the loss."),
        q("Why does training a neural network rely on the chain rule?",
          "The loss depends on each weight through a chain of functions",
          ("It turns every function in the network into a straight line", "It lets the network skip layers that change slowly",
           "It is the rule that orders the layers from input to output"),
          "Each layer's output feeds the next, so the effect of a weight on the loss is a product of derivatives "
          "along the way. Backpropagation applies the chain rule efficiently."),
    ],
    "ml_train_test": [
        q("Why keep a test set that is never used during training or tuning?",
          "To get an honest estimate of performance on new data",
          ("To give the model extra examples at the end", "To speed up training by using less data",
           "To check that the code runs without errors"),
          "A model can't be judged fairly on data it learned from or was tuned on; an untouched test set stands "
          "in for future data."),
        q("In 5-fold cross-validation, how many times is a model trained?", "5", ("1", "4", "25"),
          "The data is split into 5 parts; each part is held out once while the model trains on the other 4, "
          "giving 5 training runs and 5 scores to average."),
        q("What is the validation set used for?", "Choosing settings such as model type or tree depth",
          ("Training the final model's weights", "Reporting the final score to users",
           "Replacing the test set when it runs out"),
          "The validation set compares candidate models and hyperparameters; the test set is kept for the final "
          "estimate."),
    ],
    # --- Classic models -----------------------------------------------------------------------
    "ml_linear_regression": [
        q("A model predicts price = 50 + 2 × size. What does the 2 mean?",
          "Price rises by 2 for each extra unit of size",
          ("Price doubles whenever size doubles", "Half of the price is explained by size",
           "The model is wrong in 2 of every 100 predictions"),
          "The coefficient is the change in the prediction per unit of the feature. Because of the 50, doubling "
          "the size doesn't double the price."),
        q("What does least squares minimise?",
          "The sum of the squared differences between predictions and actual values",
          ("The number of predictions that are not exactly right", "The largest single difference between prediction and value",
           "The number of features the model needs to use"),
          "Least squares chooses the line that makes the squared residuals as small as possible in total; "
          "squaring stops positive and negative errors cancelling."),
        q("Predictions are 3 and 5; the actual values are 2 and 7. What is the mean squared error?", "2.5",
          ("1.5", "5", "3"),
          "The errors are 1 and -2; squared, 1 and 4; their mean is 2.5. 1.5 is the mean absolute error."),
    ],
    "ml_logistic_regression": [
        q("What does the sigmoid function \\( \\sigma(z) = \\frac{1}{1 + e^{-z}} \\) return when \\( z = 0 \\)?",
          "0.5", ("0", "1", "-1"),
          "\\( e^{0} = 1 \\), so \\( \\sigma(0) = \\frac{1}{2} \\). The sigmoid maps any score to a value between "
          "0 and 1, with 0 in the middle."),
        q("A spam model gives an email a probability of 0.7, and the threshold is 0.5. What happens if the "
          "threshold is raised to 0.8?", "The email is no longer classed as spam",
          ("The email's probability rises to 0.8", "The email is classed as spam with more certainty",
           "The model has to be trained again first"),
          "The threshold turns probabilities into classes without retraining. 0.7 is below 0.8, so the email "
          "is now classed as not spam."),
        q("Why is logistic regression a classification model despite its name?",
          "It predicts a probability that is turned into a class",
          ("It fits a straight line to the class labels 0 and 1", "It sorts the training examples into a fixed order",
           "It can only output the numbers 0 and 1 directly"),
          "It passes a linear score through the sigmoid to get a probability of the class, and a threshold "
          "turns that into a decision."),
    ],
    "ml_evaluation_metrics": [
        q('Only 1% of transactions are fraud. A model labels every transaction "not fraud". What is its accuracy?',
          "99%", ("1%", "50%", "0%"),
          "It is right on the 99% that aren't fraud, yet catches no fraud at all, which is why accuracy misleads "
          "on imbalanced data."),
        q("A model flags 100 emails as spam, and 80 of them really are spam. What is its precision?", "80%",
          ("20%", "100%", "It can't be known without the recall"),
          "Precision is the share of positive predictions that are correct: 80 / 100. Recall would need the "
          "number of spam emails it missed."),
        q("For a cancer screening test, missing a real case is far worse than a false alarm. Which metric "
          "matters most?", "Recall", ("Precision", "Accuracy", "Training loss"),
          "Recall is the share of real cases that are caught, so it falls with every missed case. Precision "
          "falls with false alarms instead."),
    ],
    "ml_overfitting": [
        q("Training accuracy is 99% but validation accuracy is 70%. What is most likely happening?",
          "The model is overfitting the training data",
          ("The model is underfitting the training data", "The validation data is too easy",
           "The learning rate is set to zero"),
          "A large gap between training and validation results means the model learned details of the "
          "training data that don't carry over to new data."),
        q("What does L2 regularisation do?", "Adds a penalty for large weights to the loss",
          ("Removes half of the training examples at random", "Doubles the learning rate every few steps",
           "Adds more layers to the model"),
          "Penalising the squared size of the weights pushes the model towards simpler fits that overfit less."),
        q("A model is too simple and does badly on both training and validation data. What is this called?",
          "Underfitting", ("Overfitting", "Data leakage", "Regularisation"),
          "Underfitting (high bias) means the model can't capture the pattern even in the data it trains on."),
    ],
    "ml_gradient_descent": [
        q("In gradient descent, which way does each step move the weights?",
          "Against the gradient, where the loss falls fastest",
          ("Along the gradient, where the loss rises fastest", "Towards zero, whatever the gradient",
           "In a random direction scaled by the loss"),
          "The gradient points uphill, so the update subtracts it (times the learning rate) to go downhill."),
        q("The loss jumps around and grows from one step to the next. What is the most likely cause?",
          "The learning rate is too large",
          ("The learning rate is too small", "There is too much training data", "The model has too few features"),
          "Steps that are too big overshoot the minimum and can diverge. A learning rate that is too small makes "
          "the loss fall slowly instead."),
        q("What is mini-batch (stochastic) gradient descent?",
          "Updating the weights using a small random batch at each step",
          ("Updating the weights only once, after the whole dataset", "Choosing a random learning rate at every step",
           "Moving the weights in random directions until the loss falls"),
          "Each step estimates the gradient from a few examples, which is much cheaper than using all the data "
          "and still heads downhill on average."),
    ],
    "ml_scikit_learn": [
        q("In scikit-learn, what does `model.fit(X_train, y_train)` do?",
          "Learns the model's parameters from the training data",
          ("Predicts a label for each row of the training data", "Checks that X_train and y_train have the same shape",
           "Splits the data into training and test sets"),
          "fit trains the estimator; predict then uses what it learned. Splitting is done by train_test_split."),
        q("Why put a scaler and a model together in a `Pipeline`?",
          "The scaler is fitted on training data only, every time the model is",
          ("A pipeline makes the model train in parallel on all cores", "scikit-learn models refuse to fit unscaled data",
           "A pipeline stores the predictions for later use"),
          "In cross-validation or a train/test split, the pipeline fits the scaler only on each training part, "
          "so no information from the held-out data leaks in."),
        q("Which call returns predicted labels for new data `X_new`?", "`model.predict(X_new)`",
          ("`model.fit(X_new)`", "`model.score(X_new)`", "`model.transform(X_new)`"),
          "predict uses the fitted model on new rows. score compares predictions with known answers, and "
          "transform belongs to preprocessors such as scalers."),
    ],
    "ml_feature_engineering": [
        q("Why one-hot encode a colour column with the values red, green and blue?",
          "So the model doesn't treat the categories as ordered numbers",
          ("So the column takes up less memory than the text", "So the model can learn which colour is largest",
           "Because models can't accept more than two categories"),
          "Coding red, green and blue as 1, 2 and 3 implies an order and distances that don't exist. One "
          "yes/no column per colour avoids that."),
        q("You scale the features using the mean and spread of the whole dataset, then split it into training "
          "and test sets. What is wrong?", "Information from the test set leaks into training",
          ("Scaling must always happen after training", "The test set becomes larger than the training set",
           "Nothing: scaling doesn't depend on the data"),
          "The test rows influenced the scaling, so the test score is optimistic. Fit the scaler on the training "
          "set only (a pipeline does this)."),
        q("Why do distance-based models such as k-nearest neighbours need features on similar scales?",
          "Distances are dominated by features with large values",
          ("They can only read numbers between 0 and 1", "Large numbers make the algorithm run out of memory",
           "They sort the features alphabetically before measuring"),
          "A feature measured in thousands swamps one measured in single units, so scaling gives each feature a "
          "fair say."),
    ],
    "ml_decision_trees": [
        q("What usually happens if a decision tree is allowed to grow until every leaf is pure?",
          "It overfits, memorising the training data",
          ("It underfits, missing clear patterns", "It stops after a single split", "It turns into a linear model"),
          "A fully grown tree can carve out a leaf for almost every training example. Limiting depth or leaf "
          "size, or using a forest, helps."),
        q("How does a random forest make a prediction?", "It combines the votes or averages of many different trees",
          ("It uses the single tree that scored best in training", "It grows one very deep tree on all of the data",
           "It picks a tree at random for each new example"),
          "Classification takes the majority vote of the trees; regression averages their predictions."),
        q("Why does each tree in a random forest see a random sample of rows and features?",
          "So the trees make different errors that average out",
          ("So training uses less memory than a single tree", "So each tree can be explained to users more easily",
           "So the forest can be trained without any labels"),
          "Diverse trees overfit in different ways; combining them cancels much of that noise, reducing variance."),
    ],
    "ml_clustering": [
        q("What does the k in k-means set?", "The number of clusters to find",
          ("The number of features to use", "The number of iterations to run", "The number of points in each cluster"),
          "k is chosen before running the algorithm; methods such as the elbow plot help pick it."),
        q("In each round of k-means, after every point is assigned to its nearest centre, what happens next?",
          "Each centre moves to the mean of its assigned points",
          ("The points furthest from any centre are removed", "A new centre is added for the largest cluster",
           "Each point moves halfway towards its centre"),
          "k-means alternates between assigning points and moving centres until the assignments stop changing."),
        q("Income ranges up to 100,000 and age up to 90. Why scale them before k-means?",
          "Otherwise income alone decides the distances",
          ("k-means only accepts whole numbers", "Scaling picks the right value of k for you",
           "Unscaled data always produces a single cluster"),
          "Distances add up differences across features, so the feature with the largest numbers dominates "
          "unless all are put on a similar scale."),
    ],
    "ml_pca": [
        q("What is the first principal component?", "The direction along which the data varies most",
          ("The feature with the largest values", "The first column of the original dataset",
           "The direction along which the data varies least"),
          "PCA finds new axes ordered by variance; the first captures the most spread, the second the most of "
          "what remains, and so on."),
        q("The first two principal components explain 90% of the variance. What does that mean?",
          "Two dimensions keep most of the spread in the data",
          ("A model will be 90% accurate with two features", "90% of the rows can be removed safely",
           "Two of the original features can be deleted"),
          "Projecting onto those two directions keeps 90% of the variation. The components mix all the original "
          "features rather than picking two of them."),
        q("Why standardise the features before running PCA?",
          "Otherwise features with large units dominate the components",
          ("PCA refuses to run on data that contains negative numbers", "Standardising chooses how many components to keep",
           "It makes every component explain the same variance"),
          "PCA follows variance, and a feature measured in large units has a large variance just because of its "
          "units."),
    ],
    # --- Deep learning ------------------------------------------------------------------------
    "ml_neural_networks": [
        q("What does a single artificial neuron compute before its activation function?",
          "A weighted sum of its inputs plus a bias",
          ("The largest of its inputs", "The average of the previous layer's outputs", "A random number between 0 and 1"),
          "Each input is multiplied by a learned weight, the results are added and a bias is added; the "
          "activation function is then applied."),
        q("Why do neural networks need non-linear activation functions such as ReLU?",
          "Without them, stacked layers collapse into one linear model",
          ("Without them, the network can't be trained on a GPU", "They make every neuron output a probability",
           "They stop the weights from becoming negative"),
          "A chain of linear layers is itself linear, so depth would add nothing. Non-linear activations let the "
          "network represent curved, complex patterns."),
        q("What does ReLU return for an input of -3?", "0", ("-3", "3", "1"),
          "\\( \\text{ReLU}(x) = \\max(0, x) \\), so negative inputs become 0 and positive inputs pass through "
          "unchanged."),
    ],
    "ml_training_nn": [
        q("What is an epoch?", "One full pass through the training data",
          ("One update of the weights", "One layer of the network", "One prediction for a single example"),
          "With mini-batches, an epoch contains many weight updates: one per batch."),
        q("Validation loss starts rising while training loss keeps falling. What is a sensible response?",
          "Stop training early, keeping the best checkpoint",
          ("Raise the learning rate to speed things up", "Train for many more epochs", "Remove the validation set"),
          "The model has started to overfit. Early stopping keeps the weights from the epoch with the best "
          "validation loss."),
        q("What does dropout do during training?", "Randomly ignores some neurons at each step",
          ("Removes the worst training examples", "Deletes layers that learn slowly",
           "Lowers the learning rate when loss rises"),
          "Turning off random neurons stops the network relying on any single one, which reduces overfitting. "
          "It is switched off when making predictions."),
    ],
    "ml_cnn": [
        q("Why do convolutional layers need far fewer weights than dense layers on images?",
          "The same small filter is reused across the whole image",
          ("They only look at the image's colour, not its shapes", "They shrink every image to one pixel first",
           "They skip training and use fixed weights"),
          "A 3 × 3 filter has 9 weights per input channel wherever it is applied, while a dense layer needs a "
          "weight for every pixel and output pair."),
        q("A 3 × 3 filter slides over a 5 × 5 image with stride 1 and no padding. What size is the output?",
          "3 × 3", ("5 × 5", "1 × 1", "2 × 2"),
          "The filter fits in 5 - 3 + 1 = 3 positions across and 3 down."),
        q("What does max pooling do?", "Keeps the largest value in each small region",
          ("Averages the whole image into one number", "Adds the largest filter to every layer",
           "Picks the best image from each batch"),
          "Pooling shrinks feature maps, for example 2 × 2 regions to one value, keeping the strongest response "
          "and making the network less sensitive to small shifts."),
    ],
    "ml_embeddings": [
        q("What is a word embedding?", "A vector that places words with similar meanings close together",
          ("A dictionary entry giving each word's definition as text", "A code that numbers each word by its alphabetical position",
           "A list of the words that appear most often in a text"),
          "Embeddings are learned so that related words, such as cat and dog, end up near each other in the "
          "vector space."),
        q("Two text embeddings have a cosine similarity close to 1. What does that suggest?",
          "They point in nearly the same direction, so the texts are similar",
          ("They point in opposite directions, so the texts disagree", "They are unrelated, since 1 is the lowest value",
           "They have the same length but unrelated meanings"),
          "Cosine similarity measures the angle between vectors: 1 means the same direction, 0 unrelated and -1 "
          "opposite. Semantic search ranks texts this way."),
        q("Why do language models split text into sub-word tokens?",
          "Rare and new words can be built from known pieces",
          ("It makes every word exactly the same length", "Whole words can't be stored by a computer",
           "It removes spelling mistakes from the text"),
          "A fixed vocabulary of sub-words covers any text, including names and new words, without needing an "
          "entry for every word."),
    ],
    "ml_transformers": [
        q("What does self-attention let each token do?",
          "Weigh how relevant every other token in the input is to it",
          ("Look only at the token immediately before it", "Ignore tokens that appear more than once",
           "Copy the meaning of the first token in the sentence"),
          "Attention scores every pair of tokens and mixes in information from the most relevant ones, wherever "
          "they are in the text."),
        q("What is a GPT-style language model trained to do during pre-training?",
          "Predict the next token from the tokens before it",
          ("Look up answers in a database of facts", "Translate every sentence into English",
           "Sort documents by how reliable they are"),
          "Pre-training on huge amounts of text teaches next-token prediction; fine-tuning then shapes the "
          "model for tasks such as following instructions."),
        q("What is a model's context window?", "The most tokens it can take into account at once",
          ("The number of layers in the network", "The time limit for generating an answer",
           "The set of topics it was trained on"),
          "Everything in a request (instructions, conversation and the answer so far) has to fit in the context "
          "window, measured in tokens."),
    ],
    # --- Using AI -------------------------------------------------------------------------------
    "ml_llm_apis": [
        q("What does setting the temperature to 0 do?",
          "Makes the model favour the most likely tokens, so answers vary less",
          ("Makes the model refuse questions it is unsure about", "Stops the model from using its training data",
           "Makes the model answer faster by using fewer tokens"),
          "Temperature controls how random token sampling is: low values give focused, repeatable answers, high "
          "values more varied ones. It doesn't make answers more correct."),
        q("Why should an app check an LLM's answer before relying on it?",
          "Models can state wrong information with full confidence",
          ("Answers are encrypted and must be decoded first", "The API returns answers in a random order",
           "Models only answer correctly when asked twice"),
          "Language models generate plausible text, which can include invented facts. Validate the format, and "
          "check facts that matter."),
        q("What is a system prompt?", "Instructions that set the model's role and rules for a conversation",
          ("The first question a user types into the chat", "An error message returned when a request fails",
           "A setting that chooses which model version runs"),
          "The system prompt is sent with every request and shapes how the model behaves, for example its tone, "
          "format and limits."),
    ],
    "ml_responsible_ai": [
        q("A hiring model is trained on past decisions that favoured one group. What is the likely result?",
          "The model learns and repeats the same bias",
          ("The model corrects the bias automatically", "The model ignores the past decisions",
           "The bias disappears once there is enough data"),
          "A model learns whatever patterns are in its training data, including unfair ones. More of the same "
          "data doesn't remove the bias."),
        q("Why check a model's error rates separately for different groups of people?",
          "A good overall score can hide much worse results for some groups",
          ("Models must be retrained for every group of users", "It makes the overall accuracy higher",
           "Laws require exactly equal accuracy for everyone"),
          "An average can look fine while a smaller group gets far more errors; breaking results down by group "
          "reveals it."),
        q("Removing the gender column from training data doesn't guarantee a model ignores gender. Why?",
          "Other features, such as job titles, can act as proxies",
          ("The model can still read the deleted column", "Gender is added back automatically during training",
           "Removing columns makes models more biased by design"),
          "Features that correlate with a removed attribute let the model reconstruct it, so fairness has to be "
          "measured, not assumed."),
    ],
}
