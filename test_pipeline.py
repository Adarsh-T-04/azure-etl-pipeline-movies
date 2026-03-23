"""
Unit Tests — Azure ETL Pipeline (Movies Dataset)
Run: pytest tests/ -v
"""

import pytest
import pandas as pd
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from extractor import CSVExtractor
from transformer import DataTransformer


MOVIES_CSV = os.path.join(os.path.dirname(__file__), "../data/movies.csv")

@pytest.fixture
def extract_config():
    return {"encoding": "utf-8", "delimiter": ",", "required_cols": ["id", "name", "year", "rating"]}

@pytest.fixture
def transform_config():
    return {
        "drop_nulls_in": ["id", "name", "rating"],
        "fill_nulls": {"certificate": "Not Rated", "description": "No description available"},
        "rename_cols": {}, "date_cols": [],
        "deduplicate_on": ["id"],
        "numeric_cols": ["rating", "year"],
    }

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "id": ["tt0068646", "tt5113044", "tt7657566", "tt0068646"],
        "name": ["The Godfather", "Movie B", None, "The Godfather"],
        "year": [1972, 2019, 2022, 1972],
        "rating": [9.2, 7.1, 6.5, 9.2],
        "certificate": ["A", None, "U", "A"],
        "duration": ["175 min", "87 min", "127 min", "175 min"],
        "genre": ["Crime, Drama", "Animation", "Mystery", "Crime, Drama"],
        "votes": ["1,798,749", "1,220", "121,063", "1,798,749"],
        "gross_income": ["134,966,411", "5,000,000", "22,000,000", "134,966,411"],
        "directors_id": ["nm0000399", "nm1", "nm2", "nm0000399"],
        "directors_name": ["Francis Ford Coppola", "Dir B", "Dir C", "Francis Ford Coppola"],
        "stars_id": ["nm0000008", "nm2", "nm3", "nm0000008"],
        "stars_name": ["Marlon Brando", "Star B", "Star C", "Marlon Brando"],
        "description": ["Crime drama...", "Animation...", None, "Crime drama..."],
    })

class TestCSVExtractor:
    def test_extract_real_movies_csv(self, extract_config):
        if not os.path.exists(MOVIES_CSV):
            pytest.skip("movies.csv not found")
        df = CSVExtractor(extract_config).extract(MOVIES_CSV)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 1000

    def test_missing_file_raises(self, extract_config):
        with pytest.raises(FileNotFoundError):
            CSVExtractor(extract_config).extract("ghost.csv")

    def test_missing_required_col_raises(self, tmp_path):
        p = tmp_path / "bad.csv"
        p.write_text("title,year\nThe Godfather,1972\n")
        config = {"encoding": "utf-8", "delimiter": ",", "required_cols": ["id", "rating"]}
        with pytest.raises(ValueError):
            CSVExtractor(config).extract(str(p))

class TestDataTransformer:
    def test_votes_cleaned_to_int(self, sample_df, transform_config):
        df = DataTransformer(transform_config).transform(sample_df)
        assert df.loc[df["id"] == "tt0068646", "votes"].iloc[0] == 1798749

    def test_gross_income_cleaned(self, sample_df, transform_config):
        df = DataTransformer(transform_config).transform(sample_df)
        assert pd.api.types.is_integer_dtype(df["gross_income"])

    def test_duration_cleaned(self, sample_df, transform_config):
        df = DataTransformer(transform_config).transform(sample_df)
        assert df.loc[df["id"] == "tt0068646", "duration"].iloc[0] == 175

    def test_nulls_dropped(self, sample_df, transform_config):
        df = DataTransformer(transform_config).transform(sample_df)
        assert df["name"].isnull().sum() == 0

    def test_certificate_filled(self, sample_df, transform_config):
        df = DataTransformer(transform_config).transform(sample_df)
        assert "Not Rated" in df["certificate"].values

    def test_deduplication(self, sample_df, transform_config):
        df = DataTransformer(transform_config).transform(sample_df)
        assert df["id"].duplicated().sum() == 0

    def test_audit_columns(self, sample_df, transform_config):
        df = DataTransformer(transform_config).transform(sample_df)
        assert "etl_load_timestamp" in df.columns
        assert (df["etl_source"] == "movies_csv_pipeline").all()

    def test_real_csv_full_pipeline(self, extract_config, transform_config):
        if not os.path.exists(MOVIES_CSV):
            pytest.skip("movies.csv not found")
        raw = CSVExtractor(extract_config).extract(MOVIES_CSV)
        clean = DataTransformer(transform_config).transform(raw)
        assert len(clean) > 1000
        assert clean["id"].duplicated().sum() == 0
        assert "etl_load_timestamp" in clean.columns
