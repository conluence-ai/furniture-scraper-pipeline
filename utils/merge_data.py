import pandas as pd
from rapidfuzz import fuzz
from utils.helpers import toCamelCase
from validation.validators import validateData
from logs.logs import validation_logger_setup, logger

validation_logger_setup()

def typesMatch(scraped_type: str, price_type: str) -> bool:
    """
        Check if the scraped type and price type match based on keywords.
        
        Args:
            scraped_type (str): The type of furniture scraped from the website.
            price_type (str): The type of furniture from the price listing.
        
        Returns:
            bool: True if the types match, False otherwise.
    """

    if not scraped_type and not price_type:
        return False

    scraped = scraped_type.lower()
    price_data = price_type.lower().split()

    return any(word.rstrip("s") in scraped for word in price_data)

# TODO: Add keyword in initialization file
def fuzzyMergeOnKeys(df1: pd.DataFrame, df2: pd.DataFrame, key1: str="productName", key2: str="furnitureType", threshold: int=95) -> pd.DataFrame:
    """
        Perform a fuzzy merge on two DataFrames based on specified keys and a threshold.

        Args:
            df1 (pd.DataFrame): The first DataFrame containing scraped data.
            df2 (pd.DataFrame): The second DataFrame containing price listings.
            key1 (str): The column name in df1 to match against df2.
            key2 (str): The column name in df2 to match against df1.
            threshold (int): The minimum similarity score for a match to be considered valid.

        Returns:
            pd.DataFrame: A DataFrame containing the merged rows where the keys match based on the threshold.
    """

    logger.info(f"Performing fuzzy merge on keys '{key1}' and '{key2}' with threshold {threshold}...")

    matched_rows = []

    for _, row_scraped in df1.iterrows():
        for _, row_price in df2.iterrows():
            name_ratio = fuzz.token_set_ratio(str(row_scraped.get(key1, "")), str(row_price.get(key1, "")))

            if name_ratio >= threshold and typesMatch(str(row_scraped.get(key2, "")), str(row_price.get(key2, ""))):
                merged_row = row_price.to_dict()
                merged_row.update(row_scraped.to_dict())
                matched_rows.append(merged_row)
    
    return pd.DataFrame(matched_rows)

def renameColumns(df: list, column_mapping: list) -> list:
    """
        Rename columns in a DataFrame based on a mapping.

        Args:
            df (list): The DataFrame to rename columns in.
            column_mapping (list): A list of tuples where each tuple contains the old column name and the new column name.

        Returns:
            list: The DataFrame with renamed columns.
    """

    final_columns = []
    
    for c1 in df:
        for c2 in column_mapping:
            if c1 == toCamelCase(c2):
                final_columns.append(c2)
                break

    final_columns.extend(df[len(column_mapping):])

    return final_columns

def mergeDataFrames(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """
        Merge two DataFrames and rename columns based on a mapping.

        Args:
            df1 (pd.DataFrame): The first DataFrame to merge.
            df2 (pd.DataFrame): The second DataFrame to merge.

        Returns:
            pd.DataFrame: The merged DataFrame with renamed columns.
    """

    logger.info("Merging DataFrames...")

    columns = df2.columns

    # Clean and standardize column names
    df1.columns = [toCamelCase(col) for col in df1.columns]
    df2.columns = [toCamelCase(col) for col in df2.columns]

    # Validate and process the data
    processed_df = pd.DataFrame(validateData(df1))

    if processed_df.empty:
        raise ValueError("No valid data found after validation. Please check the input DataFrame.")
    
    # Perform fuzzy merge on the two DataFrames
    merged_df = fuzzyMergeOnKeys(processed_df, df2)
    merged_df.columns = renameColumns(merged_df.columns, columns)

    logger.info("DataFrames merged successfully.")

    return merged_df