"""
Transformer Module — Cleans and normalizes Movies DataFrame before loading.
Movies-specific steps:
  - votes       : "1,220"   → 1220   (int)
  - gross_income: "134,966,411" → 134966411 (int)
  - duration    : "175 min" → 175  (int, minutes)
  - genre       : keep as-is (comma-separated string)
General steps: null handling, type casting, deduplication, audit columns.
"""

import logging
import pandas as pd

logger = logging.getLogger("AzureETL.Transformer")


class DataTransformer:
    def __init__(self, config: dict):
        self.drop_nulls_in = config.get("drop_nulls_in", [])
        self.fill_nulls = config.get("fill_nulls", {})
        self.rename_cols = config.get("rename_cols", {})
        self.date_cols = config.get("date_cols", [])
        self.deduplicate_on = config.get("deduplicate_on", [])
        self.numeric_cols = config.get("numeric_cols", [])

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info(f"Starting transform — input rows: {len(df)}")
        df = df.copy()

        df = self._rename(df)
        df = self._clean_votes(df)
        df = self._clean_gross_income(df)
        df = self._clean_duration(df)
        df = self._cast_numerics(df)
        df = self._parse_dates(df)
        df = self._handle_nulls(df)
        df = self._deduplicate(df)
        df = self._add_audit_columns(df)

        logger.info(f"Transform complete — output rows: {len(df)}")
        return df

    # ── Movies-specific cleaners ───────────────────────────────────

    def _clean_votes(self, df: pd.DataFrame) -> pd.DataFrame:
        """'1,220,500' → 1220500 (int)"""
        if "votes" in df.columns:
            df["votes"] = (
                df["votes"].astype(str)
                .str.replace(",", "", regex=False).str.strip()
            )
            df["votes"] = pd.to_numeric(df["votes"], errors="coerce").astype("Int64")
            logger.debug("Cleaned votes column")
        return df

    def _clean_gross_income(self, df: pd.DataFrame) -> pd.DataFrame:
        """'134,966,411' → 134966411 (int)"""
        if "gross_income" in df.columns:
            df["gross_income"] = (
                df["gross_income"].astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False).str.strip()
            )
            df["gross_income"] = pd.to_numeric(df["gross_income"], errors="coerce").astype("Int64")
            logger.debug("Cleaned gross_income column")
        return df

    def _clean_duration(self, df: pd.DataFrame) -> pd.DataFrame:
        """'175 min' → 175 (int minutes)"""
        if "duration" in df.columns:
            df["duration"] = (
                df["duration"].astype(str)
                .str.replace("min", "", regex=False).str.strip()
            )
            df["duration"] = pd.to_numeric(df["duration"], errors="coerce").astype("Int64")
            logger.debug("Cleaned duration → integer minutes")
        return df

    # ── General steps ──────────────────────────────────────────────

    def _rename(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.rename_cols:
            df = df.rename(columns=self.rename_cols)
        return df

    def _cast_numerics(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in self.numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in self.date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    def _handle_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        if self.drop_nulls_in:
            valid_cols = [c for c in self.drop_nulls_in if c in df.columns]
            df = df.dropna(subset=valid_cols)
            logger.info(f"Dropped {before - len(df)} rows with nulls in {valid_cols}")
        for col, val in self.fill_nulls.items():
            if col in df.columns:
                df[col] = df[col].fillna(val)
        return df

    def _deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.deduplicate_on:
            before = len(df)
            valid_cols = [c for c in self.deduplicate_on if c in df.columns]
            df = df.drop_duplicates(subset=valid_cols, keep="first")
            logger.info(f"Removed {before - len(df)} duplicate rows on {valid_cols}")
        return df

    def _add_audit_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df["etl_load_timestamp"] = pd.Timestamp.utcnow()
        df["etl_source"] = "movies_csv_pipeline"
        return df
