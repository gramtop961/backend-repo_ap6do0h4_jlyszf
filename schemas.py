"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- DietRequest -> "dietrequest" collection
- RecipeSearch -> "recipesearch" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=4, description="Plain demo password (do not use in production)")

class DietRequest(BaseModel):
    name: str
    age: int = Field(..., ge=1, le=120)
    height_cm: float = Field(..., gt=0)
    weight_kg: float = Field(..., gt=0)
    health_issues: Optional[str] = None
    medical_history: Optional[str] = None
    food_type: Literal['veg','non-veg','vegan','lactose-intolerant','gluten-free','keto','paleo','other']
    goal: Literal['lose-weight','gain-weight','maintain','post-surgery-guidance','improve-performance','other']
    extra_notes: Optional[str] = None

class RecipeSearch(BaseModel):
    query: Optional[str] = None
    ingredients: Optional[List[str]] = None
    food_type: Optional[Literal['veg','non-veg','vegan','lactose-intolerant','gluten-free','keto','paleo','any']] = 'any'
    user_email: Optional[EmailStr] = None
