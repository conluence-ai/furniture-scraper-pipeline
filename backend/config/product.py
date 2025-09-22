# Import necessary libraries
from typing import List
from dataclasses import dataclass

@dataclass
class Product:
    """Data class to represent a furniture product"""
    productName: str
    description: str
    productUrl: str
    designerName: str
    imageUrls: List[str]
    furnitureType: str
