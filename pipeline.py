"""
Azure ETL Pipeline - Main Orchestrator
Extract → Transform → Load (CSV → Azure SQL Database)
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

from extractor import CSVExtractor
from transformer import DataTransformer
from loader import AzureSQLLoader
from config_loader import load_config

# ── Logging setup ──────────────────────────────────────────────────
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / f"etl_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("AzureETL")


def run_pipeline(csv_path: str, config_path: str = "config/config.yaml") -> dict:
    """
    Run full ETL pipeline.

    Args:
        csv_path: Path to input CSV file.
        config_path: Path to YAML config file.

    Returns:
        Summary dict with row counts and status.
    """
    summary = {"status": "failed", "rows_extracted": 0, "rows_loaded": 0, "errors": []}
    config = load_config(config_path)

    # ── EXTRACT ────────────────────────────────────────────────────
    logger.info("▶ EXTRACT phase started")
    extractor = CSVExtractor(config["extract"])
    try:
        raw_df = extractor.extract(csv_path)
        summary["rows_extracted"] = len(raw_df)
        logger.info(f"  Extracted {len(raw_df)} rows from {csv_path}")
    except Exception as e:
        logger.error(f"  Extraction failed: {e}")
        summary["errors"].append(f"Extract: {e}")
        return summary

    # ── TRANSFORM ──────────────────────────────────────────────────
    logger.info("▶ TRANSFORM phase started")
    transformer = DataTransformer(config["transform"])
    try:
        clean_df = transformer.transform(raw_df)
        logger.info(f"  Transformed → {len(clean_df)} rows after cleaning")
    except Exception as e:
        logger.error(f"  Transformation failed: {e}")
        summary["errors"].append(f"Transform: {e}")
        return summary

    # ── LOAD ───────────────────────────────────────────────────────
    logger.info("▶ LOAD phase started")
    loader = AzureSQLLoader(config["load"])
    try:
        rows_loaded = loader.load(clean_df)
        summary["rows_loaded"] = rows_loaded
        summary["status"] = "success"
        logger.info(f"  Loaded {rows_loaded} rows into Azure SQL → {config['load']['table_name']}")
    except Exception as e:
        logger.error(f"  Load failed: {e}")
        summary["errors"].append(f"Load: {e}")
        return summary

    logger.info(f"✅ Pipeline complete: {summary}")
    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Azure ETL Pipeline")
    parser.add_argument("--csv", required=True, help="Path to input CSV file")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    args = parser.parse_args()

    result = run_pipeline(args.csv, args.config)
    print(f"\nPipeline Result: {result}")
    sys.exit(0 if result["status"] == "success" else 1)
