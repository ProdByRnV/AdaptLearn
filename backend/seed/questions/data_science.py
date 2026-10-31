"""Curated fallback questions for Data Science. Code is Markdown; maths is LaTeX between \\( and \\)."""

from seed.questions import Bank, q

QUESTIONS: Bank = {
    # --- Tools ----------------------------------------------------------------------------
    "ds_jupyter": [
        q("In a notebook you run cell 1 (`x = 1`), then cell 2 (`x = x + 1`), then cell 2 again. What is `x`?",
          "`3`", ("`2`", "`1`", "An error: x is defined twice"),
          "The kernel keeps every variable between runs, so each run of cell 2 adds 1 again. The order cells "
          "were run in matters, not their order on the page."),
        q("Why is Restart Kernel and Run All a good check before sharing a notebook?",
          "It proves the cells work from top to bottom on a fresh start",
          ("It makes the notebook's code run faster next time", "It deletes the outputs so the file is smaller",
           "It saves the notebook in a format others can open"),
          "Cells run out of order can depend on variables that no longer match the code. A clean run from the "
          "top shows the notebook gives the same results for someone else."),
        q("What is a Markdown cell in a notebook for?", "Formatted text, such as headings and explanations",
          ("Code that runs before every other cell", "Storing the notebook's variables between sessions",
           "Installing packages for the kernel"),
          "Markdown cells hold text that explains the analysis; code cells hold the code the kernel runs."),
    ],
    "ds_numpy": [
        q("What is `np.array([1, 2, 3]) * 2`?", "`array([2, 4, 6])`",
          ("`array([1, 2, 3, 1, 2, 3])`", "The Python list `[2, 4, 6]`", "An error: arrays can't be multiplied"),
          "Arithmetic on an array applies to every element and returns a new array. Multiplying a Python list by "
          "2 repeats it instead."),
        q("An array `a` has shape `(3, 4)`. What is the shape of `a.sum(axis=0)`?", "`(4,)`",
          ("`(3,)`", "`(3, 4)`", "`()`"),
          "axis=0 adds down the rows, collapsing that axis: one total for each of the 4 columns. axis=1 would "
          "give one total per row, shape (3,)."),
        q("Why is `arr * 2` usually much faster than a Python loop over the same numbers?",
          "The work runs in compiled code over the whole array at once",
          ("NumPy skips numbers that would not change the result", "NumPy runs every operation on the graphics card",
           "The loop has to convert every number to text first"),
          "Vectorised operations loop in fast compiled code on tightly packed numbers, instead of running Python "
          "code once per element."),
    ],
    "ds_pandas_basics": [
        q("A DataFrame `df` has a column `age`. Which keeps only the rows where age is over 30?",
          "`df[df['age'] > 30]`", ("`df['age'] > 30`", "`df.loc['age' > 30]`", "`df.filter(age > 30)`"),
          "df['age'] > 30 gives a True/False Series; using it inside df[...] keeps the rows marked True. On its "
          "own it is just the mask, not the filtered table."),
        q("What is the difference between `df.loc[2]` and `df.iloc[2]`?",
          "loc finds the row labelled 2; iloc takes the third row",
          ("loc takes the third row; iloc finds the row labelled 2", "loc returns a copy; iloc returns the original row",
           "None: iloc is an older name for loc"),
          "loc selects by index label and iloc by position, counting from 0. They agree only when the index is "
          "0, 1, 2 and so on."),
        q("What does `pd.read_csv('sales.csv')` return?", "A DataFrame with one column per CSV column",
          ("A list of dictionaries, one per row", "A NumPy array of strings", "A file object to read line by line"),
          "read_csv parses the file into a DataFrame, using the first row as column names by default."),
    ],
    "ds_data_cleaning": [
        q("What does `df.dropna()` do by default?", "Removes every row that has at least one missing value",
          ("Removes only the rows where every value is missing", "Replaces missing values with zero",
           "Removes every column that has a missing value"),
          "By default dropna drops rows (axis=0) with any missing value. how='all' drops only fully empty rows, "
          "and fillna replaces values instead."),
        q('A city column holds "London", "london " and "LONDON". What should you do before counting by city?',
          "Strip spaces and use one letter case, e.g. `.str.strip().str.title()`",
          ("Drop the rows whose spelling differs from the most common one", "Leave them: pandas treats them as one city",
           "Sort the column so the variants sit together"),
          "pandas compares text exactly, so these count as three cities. Normalising spaces and case first makes "
          "them one, without losing any rows."),
        q("Why can filling every missing income with the column's mean be a problem?",
          "It shrinks the spread and can hide why values were missing",
          ("pandas can't calculate a mean while values are missing", "It changes the number of rows in the table",
           "Means can only be used for whole numbers"),
          "Many identical filled-in values make the data look less varied than it is, and the missing values may "
          "follow a pattern worth knowing. pandas skips missing values when it calculates a mean."),
    ],
    "ds_pandas_grouping": [
        q("What does `df.groupby('region')['sales'].sum()` return?", "Total sales for each region",
          ("The total of all sales", "Each row's sales, sorted by region", "The number of rows in each region"),
          "groupby splits the rows by region, then sum adds up sales within each group: one total per region."),
        q("Orders are merged with customers using `how='left'` on customer_id, orders on the left. What happens "
          "to an order whose customer isn't in the customers table?",
          "It is kept, with empty customer columns",
          ("It is dropped from the result", "The merge raises a KeyError", "It is matched to the first customer"),
          "A left join keeps every row from the left table and fills the right table's columns with missing "
          "values where there is no match. An inner join would drop it."),
        q("Which pandas tool turns rows of (region, month, sales) into a table with a row per region and a column "
          "per month?", "`pivot_table`", ("`concat`", "`merge`", "`dropna`"),
          "pivot_table spreads one column's values across new columns and aggregates the values in each cell."),
    ],
    "ds_visualisation": [
        q("Which chart best shows how one numeric variable is distributed?", "A histogram",
          ("A pie chart", "A line chart", "A scatter plot"),
          "A histogram counts values in ranges (bins), showing the shape, centre and spread. A scatter plot "
          "needs two variables."),
        q("Why can a bar chart whose value axis starts at 95 instead of 0 mislead?",
          "Small differences look much larger than they are",
          ("It changes the order the bars appear in", "Bars can't be drawn for values above 95",
           "It makes the chart too large to print"),
          "Bar length is read as the size of the value, so cutting off the base exaggerates differences."),
        q("Which chart suits the relationship between two numeric variables, such as height and weight?",
          "A scatter plot", ("A pie chart", "A histogram of height", "A stacked bar chart"),
          "A scatter plot gives each person a point with both values, showing any trend, clusters and outliers."),
    ],
    "ds_time_series": [
        q("Daily sales are in a DataFrame with a DatetimeIndex. What does `df.resample('MS').sum()` give?",
          "Total sales for each month",
          ("The sales on the first day of each month only", "Average daily sales over the whole period",
           "The rows sorted by the name of the month"),
          "resample groups rows into time periods (MS: months, labelled by their first day) and sum totals each "
          "period."),
        q("What does `s.rolling(7).mean()` compute for a daily series?",
          "The average of each day and the six days before it",
          ("The average of every seventh day", "The mean of the whole series, repeated seven times",
           "The average of the next seven days"),
          "A rolling window moves along the series; each result averages the current value and the 6 before it. "
          "The first 6 results are missing because the window isn't full yet."),
        q("Why convert a date column with `pd.to_datetime` before analysing it?",
          "So pandas can sort, filter and group it as dates, not text",
          ("So the column takes less space when saved as CSV", "So the dates are shown in the user's own time zone",
           "Because pandas refuses to sort columns of text"),
          'As text, "10/02/2026" sorts before "9/01/2026" and can\'t be resampled. As datetimes, pandas understands '
          "the order, parts and gaps between dates."),
    ],
    # --- Statistics -----------------------------------------------------------------------
    "ds_descriptive_stats": [
        q("For the values 2, 3, 3, 4 and 100, which is the better summary of a typical value?",
          "The median, 3, because 100 pulls the mean up",
          ("The mean, 22.4, because it uses every value", "The range, 98, because it covers every value",
           "The mode, 100, because it is the largest"),
          "The mean (112 / 5 = 22.4) is dragged towards the outlier, while the median (the middle value, 3) is "
          "not. The mode here is 3, not 100."),
        q("What does a standard deviation of 0 tell you about a set of values?", "Every value is the same",
          ("The mean is 0", "The values are normally distributed", "Half the values are above 0"),
          "Standard deviation measures how far values typically are from the mean; it is 0 only when every value "
          "equals the mean."),
        q("Which measure of spread ignores the lowest and highest quarter of the values?", "The interquartile range",
          ("The range", "The standard deviation", "The variance"),
          "The IQR is the third quartile minus the first, the span of the middle 50%, so extreme values don't "
          "affect it. The others use every value."),
    ],
    "ds_probability": [
        q("A fair coin is flipped twice. What is the probability of two heads?", "\\( \\frac{1}{4} \\)",
          ("\\( \\frac{1}{2} \\)", "\\( \\frac{1}{3} \\)", "\\( \\frac{3}{4} \\)"),
          "The flips are independent, so multiply: \\( \\frac{1}{2} \\times \\frac{1}{2} = \\frac{1}{4} \\). The "
          "four equally likely outcomes are HH, HT, TH and TT."),
        q("A test detects 99% of people who have a condition and wrongly flags 1% of people who don't. 1 in "
          "1,000 people has it. Someone tests positive. Roughly how likely are they to have it?",
          "About 9%", ("About 99%", "About 50%", "About 1%"),
          "Out of 100,000 people, about 99 of the 100 with the condition test positive, but so do about 999 of "
          "the 99,900 without it. 99 / (99 + 999) is about 9%: Bayes' theorem."),
        q("Events A and B are independent. Which is true?", "\\( P(A \\text{ and } B) = P(A) \\times P(B) \\)",
          ("\\( P(A \\text{ and } B) = P(A) + P(B) \\)", "\\( P(A) = P(B) \\)", "\\( P(A \\text{ or } B) = 1 \\)"),
          "Independence means one event doesn't change the chance of the other, so the probability of both is "
          "the product."),
    ],
    "ds_distributions": [
        q("In a normal distribution, about what share of values lie within one standard deviation of the mean?",
          "68%", ("50%", "95%", "99.7%"),
          "The 68-95-99.7 rule: about 68% lie within one standard deviation, 95% within two and 99.7% within three."),
        q("Exam scores have a mean of 70 and a standard deviation of 5. What is the z-score of a score of 80?",
          "2", ("10", "0.5", "16"),
          "A z-score counts standard deviations from the mean: (80 - 70) / 5 = 2."),
        q("What does the central limit theorem say?",
          "Means of large samples are roughly normal, whatever the data's shape",
          ("Large samples always have the same mean as each other", "The data itself becomes normal once you have enough",
           "The median and mean are equal in every large sample"),
          "Even when the data is skewed, the means of many large samples form a near-normal distribution around "
          "the true mean. That is what makes confidence intervals for means work."),
    ],
    "ds_sampling": [
        q("Survey results come only from people who chose to answer an online poll. What is the main risk?",
          "The sample may not represent the population",
          ("The sample size will always be too small", "The margin of error becomes exactly zero",
           "Online answers can't be analysed statistically"),
          "People who choose to answer often differ from those who don't (self-selection bias). A larger sample "
          "of the same kind doesn't fix that."),
        q("What happens to the standard error of a sample mean when the sample size goes from 100 to 400?",
          "It halves", ("It quarters", "It doubles", "It stays the same"),
          "The standard error shrinks with the square root of the sample size: four times the sample gives half "
          "the standard error."),
        q("What does a 95% confidence interval mean?", "The method captures the true value in about 95% of samples",
          ("95% of the data values lie inside the interval", "The sample mean is correct to within 95%",
           "The true value is in the middle 95% of the sample"),
          "The 95% describes the procedure: intervals built this way from many samples would contain the true "
          "value about 95% of the time. It isn't about where the data lies."),
    ],
    "ds_hypothesis_testing": [
        q("What does a p-value of 0.03 mean?",
          "If there were no real effect, data this extreme would appear about 3% of the time",
          ("There is a 3% chance that the null hypothesis is true", "The effect being tested is 3% larger than expected",
           "There is a 97% chance that the result will repeat"),
          "A p-value assumes the null hypothesis and asks how surprising the data is. It isn't the probability "
          "that the null hypothesis is true."),
        q("What is a type I error?", "Rejecting the null hypothesis when it is actually true",
          ("Keeping the null hypothesis when it is actually false", "Using the wrong test for the kind of data collected",
           "Collecting a sample that is too small to analyse"),
          "A type I error is a false positive. Missing a real effect (keeping a false null hypothesis) is a type "
          "II error."),
        q("Why does testing 20 different metrics, each at the 5% level, cause trouble?",
          "About one may look significant by chance even with no effect",
          ("Each extra test lowers the p-value of the others", "Tests must be run one at a time or they fail",
           "Twenty metrics are too many for a t-test to accept"),
          "Each test has a 5% false-positive rate, so across 20 about one is expected by chance. Corrections "
          "such as Bonferroni adjust for this."),
    ],
    "ds_ab_testing": [
        q("Why are users assigned to version A or B at random?", "So the groups differ only in the change being tested",
          ("So each group ends up exactly the same size", "So the test finishes faster than a planned split",
           "So users can't tell which version they are seeing"),
          "Random assignment balances everything else (devices, habits, countries) between the groups, so a "
          "difference in results can be put down to the change."),
        q("You check an A/B test every day and stop as soon as it shows p < 0.05. What is the problem?",
          "Repeated peeking makes a false positive far more likely",
          ("The test needs at least 30 days to run correctly", "Daily checks change which users see each version",
           "p-values can only be calculated once a test is over"),
          "Each look is another chance for noise to cross the line. Stopping at the first crossing turns a 5% "
          "false-positive rate into a much higher one."),
        q("Why decide the sample size before starting an A/B test?",
          "So the test can detect the smallest effect that matters",
          ("So every user of the product takes part in the test", "Because the p-value formula needs it in advance",
           "So both versions can be released on the same day"),
          "A power calculation gives the sample needed to reliably detect an effect of the size you care about; "
          "fixing it in advance also avoids stopping early on noise."),
    ],
    "ds_correlation": [
        q("What does a correlation coefficient of -0.9 indicate?",
          "A strong relationship where one rises as the other falls",
          ("A weak relationship that is barely there", "No relationship, because the value is negative",
           "A strong relationship where both rise together"),
          "The sign gives the direction and the size the strength: -0.9 is a strong negative (downhill) "
          "straight-line relationship."),
        q("Ice-cream sales and drownings are strongly correlated. What is the most likely explanation?",
          "Hot weather drives both",
          ("Ice cream causes drowning", "Drownings increase ice-cream sales", "The correlation must be a calculation error"),
          "A third factor (a confounder) can make two things move together without either causing the other. "
          "Correlation alone doesn't show causation."),
        q("Points form a clear U-shape, yet Pearson's r is close to 0. Why?",
          "r only measures straight-line relationships",
          ("The points have too many outliers to measure", "U-shaped data always has a correlation of 1",
           "r can't be calculated for curved data"),
          "Pearson's r measures how well a straight line fits. A strong curved pattern can still give r near 0, "
          "which is why you plot the data first."),
    ],
    # --- Analysis -----------------------------------------------------------------------
    "ds_eda": [
        q("What should usually come first when you receive a new dataset?",
          "Check its size, column types, missing values and summary statistics",
          ("Train a model on it to see how accurate it can be", "Delete the rows with outliers so results are clean",
           "Choose the final charts for the report"),
          "Knowing what the data contains, and what is wrong with it, comes before cleaning, modelling or "
          "reporting. Outliers may be errors or the most interesting rows."),
        q("A histogram of delivery times has a long tail to the right. What does that suggest?",
          "Most deliveries are quick, but a few take much longer",
          ("Most deliveries are slow, but a few are very quick", "Delivery times are spread evenly across the range",
           "The data must contain an error and should be dropped"),
          "A right (positive) skew means most values are low with a few large ones; the mean will be above the "
          "median."),
        q("Which pandas call gives the count, mean, standard deviation and quartiles of numeric columns?",
          "`df.describe()`", ("`df.info()`", "`df.head()`", "`df.value_counts()`"),
          "describe summarises numeric columns; info lists column types and non-missing counts, and head shows "
          "the first rows."),
    ],
    "ds_communicating": [
        q("What should come first in a summary for busy decision makers?", "The main finding and what it means for them",
          ("A full description of the data cleaning steps", "Every chart produced during the analysis",
           "The code used, so they can check the work"),
          "Lead with the answer and its consequence; methods and detail can follow for those who want them."),
        q("An estimate shows a 4% uplift with a 95% interval from -1% to 9%. How should you report it?",
          "Give the range and say the effect could be zero",
          ("Report a 4% uplift, since that is the best estimate", "Report 9%, the most the change could achieve",
           "Report that the change made things 1% worse"),
          "The interval includes 0 (and small losses), so the data is consistent with no effect. Reporting only "
          "4% would overstate the certainty."),
        q("Which chart best compares sales across 12 product categories?", "A bar chart sorted by value",
          ("A pie chart with 12 slices", "A line chart in alphabetical order", "A histogram of the sales figures"),
          "Sorted bars make ranking and differences easy to read. Twelve slices are hard to compare by angle, and "
          "a line implies an order that categories don't have."),
    ],
}
