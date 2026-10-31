"""Data Science: answering questions with data, from notebooks and pandas to statistics and experiments.

Builds on Python (and Data Formats from Foundations). Linear Regression is defined in AI & ML and
shared here; the statistics topics need no programming, so Descriptive Statistics is a starting topic.
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- Tools ----------------------------------------------------------------------------
    Topic(
        "ds_jupyter", "Jupyter Notebooks",
        "Working in Jupyter notebooks: code and Markdown cells, running cells in any order and why "
        "that can mislead, the kernel and its state, restarting and running everything, and sharing "
        "notebooks.",
        1,
        (
            docs("Jupyter: Try Jupyter", "https://docs.jupyter.org/en/latest/start/index.html"),
            docs("JupyterLab: Get started", "https://jupyterlab.readthedocs.io/en/stable/getting_started/overview.html"),
            video("Jupyter Notebook Tutorial (Corey Schafer)", "https://www.youtube.com/watch?v=HW29067qVWk"),
        ),
    ),
    Topic(
        "ds_numpy", "NumPy Arrays",
        "Fast numerical arrays with NumPy: creating arrays, shape and dtype, indexing and slicing, "
        "vectorised arithmetic instead of loops, broadcasting, and aggregations such as sum and mean "
        "along an axis.",
        2,
        (
            docs("NumPy: The absolute basics for beginners", "https://numpy.org/doc/stable/user/absolute_beginners.html"),
            docs("NumPy: Broadcasting", "https://numpy.org/doc/stable/user/basics.broadcasting.html"),
            video("Complete Python NumPy Tutorial (Keith Galli)", "https://www.youtube.com/watch?v=GB9ByFAIAH4"),
        ),
    ),
    Topic(
        "ds_pandas_basics", "pandas DataFrames",
        "Tables in pandas: Series and DataFrames, reading CSV files, selecting rows and columns with "
        "loc and iloc, filtering with conditions, sorting, and adding new columns.",
        2,
        (
            docs("pandas: 10 minutes to pandas", "https://pandas.pydata.org/docs/user_guide/10min.html"),
            docs("pandas: How do I read and write tabular data?", "https://pandas.pydata.org/docs/getting_started/intro_tutorials/02_read_write.html"),
            video("Complete Python Pandas Data Science Tutorial (Keith Galli)", "https://www.youtube.com/watch?v=vmEHCJofslg"),
        ),
    ),
    Topic(
        "ds_data_cleaning", "Data Cleaning",
        "Making messy data usable: finding and handling missing values, removing duplicates, fixing "
        "types and inconsistent categories, dealing with outliers, and keeping a record of every "
        "change.",
        2,
        (
            docs("pandas: Working with missing data", "https://pandas.pydata.org/docs/user_guide/missing_data.html"),
            article("Kaggle Learn: Data Cleaning", "https://www.kaggle.com/learn/data-cleaning"),
            article("Python Data Science Handbook: Handling missing data", "https://jakevdp.github.io/PythonDataScienceHandbook/03.04-missing-values.html"),
        ),
    ),
    Topic(
        "ds_pandas_grouping", "Grouping & Joining Data",
        "Summarising and combining tables: groupby with aggregations, pivot tables, and merging "
        "DataFrames on keys with inner, left, right and outer joins.",
        3,
        (
            docs("pandas: Group by (split-apply-combine)", "https://pandas.pydata.org/docs/user_guide/groupby.html"),
            docs("pandas: Merge, join, concatenate and compare", "https://pandas.pydata.org/docs/user_guide/merging.html"),
            article("Python Data Science Handbook: Aggregation and grouping", "https://jakevdp.github.io/PythonDataScienceHandbook/03.08-aggregation-and-grouping.html"),
        ),
    ),
    Topic(
        "ds_visualisation", "Data Visualisation",
        "Charts with Matplotlib and seaborn: line, bar, scatter and histogram plots, choosing the "
        "right chart for the question, labelling axes, and avoiding misleading scales.",
        2,
        (
            docs("Matplotlib: Quick start guide", "https://matplotlib.org/stable/users/explain/quick_start.html"),
            docs("seaborn: User guide and tutorial", "https://seaborn.pydata.org/tutorial.html"),
            video("Matplotlib Tutorial Part 1 (Corey Schafer)", "https://www.youtube.com/watch?v=UO98lJQ3QGI"),
        ),
    ),
    Topic(
        "ds_time_series", "Dates & Time Series",
        "Working with dates in pandas: parsing datetimes, date indexes, resampling to days, weeks or "
        "months, rolling averages, and time zones.",
        3,
        (
            docs("pandas: Time series / date functionality", "https://pandas.pydata.org/docs/user_guide/timeseries.html"),
            docs("pandas: How to handle time series data", "https://pandas.pydata.org/docs/getting_started/intro_tutorials/09_timeseries.html"),
            article("Python Data Science Handbook: Working with time series", "https://jakevdp.github.io/PythonDataScienceHandbook/03.11-working-with-time-series.html"),
        ),
    ),
    # --- Statistics -----------------------------------------------------------------------
    Topic(
        "ds_descriptive_stats", "Descriptive Statistics",
        "Summarising data with numbers: mean, median and mode, range, variance and standard "
        "deviation, percentiles and the interquartile range, and when the median tells the truer "
        "story.",
        1,
        (
            video("Calculating the Mean, Variance and Standard Deviation (StatQuest)", "https://www.youtube.com/watch?v=SzZ6GpcfoQY"),
            video("Histograms, Clearly Explained (StatQuest)", "https://www.youtube.com/watch?v=qBigTkBLU6g"),
        ),
    ),
    Topic(
        "ds_probability", "Probability Basics",
        "The rules of chance: events and outcomes, adding and multiplying probabilities, "
        "independence, conditional probability and Bayes' theorem, and expected value.",
        2,
        (
            article("Seeing Theory: Basic probability", "https://seeing-theory.brown.edu/basic-probability/index.html"),
            article("Seeing Theory: Compound probability", "https://seeing-theory.brown.edu/compound-probability/index.html"),
        ),
    ),
    Topic(
        "ds_distributions", "Probability Distributions",
        "Common patterns of variation: the binomial and normal distributions, z-scores, the "
        "68-95-99.7 rule, and the central limit theorem.",
        3,
        (
            article("Seeing Theory: Probability distributions", "https://seeing-theory.brown.edu/probability-distributions/index.html"),
            video("The Normal Distribution, Clearly Explained (StatQuest)", "https://www.youtube.com/watch?v=rzFX5NWojp0"),
        ),
    ),
    Topic(
        "ds_sampling", "Sampling & Confidence Intervals",
        "Learning about a population from a sample: random sampling and bias, sampling error, the "
        "standard error, and what a 95% confidence interval does and does not mean.",
        3,
        (
            article("Seeing Theory: Frequentist inference", "https://seeing-theory.brown.edu/frequentist-inference/index.html"),
            video("Confidence Intervals, Clearly Explained (StatQuest)", "https://www.youtube.com/watch?v=TqOeMYtOc1w"),
        ),
    ),
    Topic(
        "ds_hypothesis_testing", "Hypothesis Testing",
        "Deciding whether an effect is real: null and alternative hypotheses, p-values, significance "
        "levels, type I and type II errors, multiple comparisons, and common tests such as the t-test.",
        3,
        (
            video("Hypothesis Testing and the Null Hypothesis (StatQuest)", "https://www.youtube.com/watch?v=0oc49DyA3hU"),
            video("p-values: What they are and how to interpret them (StatQuest)", "https://www.youtube.com/watch?v=vemZtEM63GY"),
            article("OpenIntro Statistics (free textbook)", "https://www.openintro.org/book/os/"),
        ),
    ),
    Topic(
        "ds_ab_testing", "A/B Testing",
        "Running controlled experiments on products: randomly splitting users, choosing a metric and "
        "sample size in advance, why peeking at results inflates false positives, and reading the "
        "outcome.",
        4,
        (
            article("Evan Miller: How not to run an A/B test", "https://www.evanmiller.org/how-not-to-run-an-ab-test.html"),
        ),
    ),
    Topic(
        "ds_correlation", "Correlation",
        "Measuring how two variables move together: scatter plots, Pearson's correlation coefficient "
        "from -1 to 1, what it misses (curved patterns, outliers), and why correlation does not prove "
        "causation.",
        2,
        (
            video("Pearson's Correlation, Clearly Explained (StatQuest)", "https://www.youtube.com/watch?v=xZ_z8KWkhXE"),
            article("Seeing Theory: Regression analysis", "https://seeing-theory.brown.edu/regression-analysis/index.html"),
            article("Tyler Vigen: Spurious correlations", "https://www.tylervigen.com/spurious-correlations"),
        ),
    ),
    # --- Analysis -----------------------------------------------------------------------
    Topic(
        "ds_eda", "Exploratory Data Analysis",
        "Getting to know a dataset before modelling: its size and types, summary statistics, "
        "distributions and outliers, relationships between variables, and questions worth asking "
        "next.",
        3,
        (
            article("Think Stats: Exploratory data analysis in Python", "https://allendowney.github.io/ThinkStats/"),
            article("Fundamentals of Data Visualization: Directory of visualizations", "https://clauswilke.com/dataviz/directory-of-visualizations.html"),
        ),
    ),
    Topic(
        "ds_communicating", "Communicating Findings",
        "Turning analysis into decisions: leading with the answer, one clear chart per message, "
        "honest axes and uncertainty, and writing for people who did not do the analysis.",
        3,
        (
            article("Fundamentals of Data Visualization: Telling a story", "https://clauswilke.com/dataviz/telling-a-story.html"),
            article("Fundamentals of Data Visualization (free book)", "https://clauswilke.com/dataviz/"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("python_basics", "ds_jupyter"),
    ("ds_jupyter", "ds_numpy"),
    ("python_lists_tuples", "ds_numpy"),
    ("ds_numpy", "ds_pandas_basics"),
    ("python_dicts_sets", "ds_pandas_basics"),
    ("data_formats", "ds_pandas_basics"),
    ("ds_pandas_basics", "ds_data_cleaning"),
    ("ds_pandas_basics", "ds_pandas_grouping"),
    ("ds_pandas_basics", "ds_visualisation"),
    ("ds_pandas_grouping", "ds_time_series"),

    ("ds_descriptive_stats", "ds_probability"),
    ("ds_probability", "ds_distributions"),
    ("ds_distributions", "ds_sampling"),
    ("ds_sampling", "ds_hypothesis_testing"),
    ("ds_hypothesis_testing", "ds_ab_testing"),
    ("ds_descriptive_stats", "ds_correlation"),

    ("ds_data_cleaning", "ds_eda"),
    ("ds_visualisation", "ds_eda"),
    ("ds_descriptive_stats", "ds_eda"),
    ("ds_eda", "ds_communicating"),
)

DATA_SCIENCE = Domain(
    id="data-science",
    name="Data Science",
    description=(
        "Turning data into answers with Python: notebooks, NumPy and pandas, cleaning and "
        "visualising data, the statistics behind conclusions, experiments, and communicating what "
        "the data shows."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
    shared=("ml_linear_regression",),
)
