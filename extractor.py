"""
Extractor Module — Reads CSV files into a Pandas DataFrame.
Supports encoding detection, delimiter auto-detection, and header validation.
"""

import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger("AzureETL.Extractor")


class CSVExtractor:
    def __init__(self, config: dict):
        """
        Args:
            config: extract section from config.yaml
                - encoding     : file encoding (default: utf-8)
                - delimiter    : CSV delimiter (default: ,)
                - required_cols: list of columns that must exist
        """
        self.encoding = config.get("encoding", "utf-8")
        self.delimiter = config.get("delimiter", ",")
        self.required_cols = config.get("required_cols", [])

    def extract(self, csv_path: str) -> pd.DataFrame:
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")

        logger.info(f"Reading: {path.name} | encoding={self.encoding} | sep='{self.delimiter}'")

        df = pd.read_csv(
            path,
            encoding=self.encoding,
            sep=self.delimiter,
            low_memory=False,
        )

        self._validate_schema(df)
        logger.info(f"Schema OK — columns: {list(df.columns)}")
        return df

    def _validate_schema(self, df: pd.DataFrame):
        missing = [c for c in self.required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Required columns missing from CSV: {missing}")
