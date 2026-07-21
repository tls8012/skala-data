from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


RANDOM_STATE = 42
TEST_SIZE = 0.2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "adult_data.csv"
MODEL_PATH = Path(__file__).resolve().parent / "best_classifier.joblib"
REPORT_PATH = Path(__file__).resolve().parent / "classification_report.png"

CATEGORICAL_COLUMNS = [
    "workclass",
    "education",
    "marital-status",
    "occupation",
    "race",
    "relationship",
    "sex",
    "native-country"
]

NUMERIC_COLUMNS = [
    "age",
    "fnlwgt",
    "education-num",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
]

FEATURE_COLUMNS = CATEGORICAL_COLUMNS + NUMERIC_COLUMNS
TARGET_COLUMN = "income"


def load_data() -> tuple[pd.DataFrame, pd.Series]:
    """Load Adult data, remove '?' rows, and split features from the target."""
    data = pd.read_csv(DATA_PATH, na_values="?", skipinitialspace=True)
    data.columns = data.columns.str.strip()

    # Treat whitespace-surrounded question marks as missing too, then drop every
    # row containing a missing value anywhere in the original data.
    string_columns = [
        column
        for column in data.columns
        if pd.api.types.is_string_dtype(data[column].dtype)
    ]
    data[string_columns] = data[string_columns].apply(
        lambda column: column.str.strip().replace("?", pd.NA)
    )
    data = data.dropna().copy()

    data[TARGET_COLUMN] = data[TARGET_COLUMN].str.rstrip(".").map(
        {">50K": 0, "<=50K": 1}
    )
    if data[TARGET_COLUMN].isna().any():
        unexpected = sorted(
            data.loc[data[TARGET_COLUMN].isna(), TARGET_COLUMN]
            .astype(str)
            .unique()
        )
        raise ValueError(f"Unexpected income values: {unexpected}")

    # Selecting only the requested columns drops native-country and also leaves
    # out relationship, which was not included in the requested X columns.
    X = data[FEATURE_COLUMNS]
    y = data[TARGET_COLUMN].astype(int)
    return X, y


def build_grid_search() -> GridSearchCV:
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", categorical_pipeline, CATEGORICAL_COLUMNS),
            ("numeric", numeric_pipeline, NUMERIC_COLUMNS),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(max_iter=2_000, random_state=RANDOM_STATE),
            ),
        ]
    )

    parameter_grid = [
        {
            "classifier": [
                LogisticRegression(max_iter=2_000, random_state=RANDOM_STATE)
            ],
            "classifier__C": [0.1, 1.0, 10.0],
            "classifier__solver": ["liblinear", "lbfgs"],
        },
        {
            "classifier": [
                RandomForestClassifier(
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                )
            ],
            "classifier__n_estimators": [100, 200],
            "classifier__max_depth": [None, 10, 20],
            "classifier__min_samples_split": [2, 5],
        },
    ]

    return GridSearchCV(
        estimator=pipeline,
        param_grid=parameter_grid,
        scoring="accuracy",
        cv=5,
        n_jobs=-1,
        verbose=1,
        refit=True,
    )


def save_classification_report_plot(
    y_test: pd.Series, y_pred, output_path: Path
) -> None:
    """Save precision, recall, and F1 scores as an annotated heatmap."""
    class_names = [">50K", "<=50K"]
    report = classification_report(
        y_test,
        y_pred,
        target_names=class_names,
        output_dict=True,
    )
    report_df = pd.DataFrame(report).transpose()
    plot_df = report_df.loc[
        class_names + ["macro avg", "weighted avg"],
        ["precision", "recall", "f1-score"],
    ]

    figure, axis = plt.subplots(figsize=(8, 5))
    sns.heatmap(
        plot_df,
        annot=True,
        fmt=".3f",
        cmap="Blues",
        vmin=0,
        vmax=1,
        linewidths=0.5,
        ax=axis,
    )
    axis.set_title("Classification Report")
    axis.set_xlabel("Metric")
    axis.set_ylabel("")
    figure.tight_layout()
    figure.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    search = build_grid_search()
    search.fit(X_train, y_train)

    print(f"Rows after dropping missing values: {len(X):,}")
    print(f"Best cross-validation accuracy: {search.best_score_:.4f}")
    print(f"Best parameters: {search.best_params_}")

    joblib.dump(search.best_estimator_, MODEL_PATH)
    print(f"Saved best classifier to: {MODEL_PATH}")

    # Round-trip test: reload the exact persisted pipeline and evaluate it on
    # the held-out data that was not used by GridSearchCV.
    loaded_classifier = joblib.load(MODEL_PATH)
    # first, test original classifier
    y_pred = search.best_estimator_.predict(X_test)
    print(f"Reloaded model test accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred, target_names=[">50K", "<=50K"]))
    y_pred = loaded_classifier.predict(X_test)
    print(f"Reloaded model test accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred, target_names=[">50K", "<=50K"]))
    save_classification_report_plot(y_test, y_pred, REPORT_PATH)
    print(f"Saved classification report plot to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
