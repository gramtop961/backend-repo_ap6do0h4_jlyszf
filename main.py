import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import User, DietRequest, RecipeSearch

import requests

app = FastAPI(title="Dietician & Recipe Builder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Dietician & Recipe Builder API running"}

# Auth (simple demo; not secure for production)
class AuthPayload(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    password: str

@app.post("/auth/signup")
def signup(payload: AuthPayload):
    # check if exists
    existing = list(db["user"].find({"email": payload.email})) if db else []
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(name=payload.name or payload.email.split("@")[0], email=payload.email, password=payload.password)
    user_id = create_document("user", user)
    return {"ok": True, "user_id": user_id}

@app.post("/auth/login")
def login(payload: AuthPayload):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    user = db["user"].find_one({"email": payload.email, "password": payload.password})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"ok": True, "email": user.get("email"), "name": user.get("name")}

# Dietician assistant endpoint (rule + simple AI via heuristic)
@app.post("/diet/plan")
def generate_diet_plan(info: DietRequest):
    # Simple heuristic-based responses; in real app replace with LLM
    bmi = info.weight_kg / ((info.height_cm/100) ** 2)
    category = (
        "underweight" if bmi < 18.5 else
        "normal" if bmi < 25 else
        "overweight" if bmi < 30 else
        "obese"
    )

    guidelines = []
    if info.food_type in ["veg", "vegan"]:
        guidelines.append("Prioritize legumes, tofu, nuts, seeds for protein.")
    if info.food_type == "non-veg":
        guidelines.append("Lean proteins like chicken, fish, eggs; minimize fried foods.")
    if info.food_type == "lactose-intolerant":
        guidelines.append("Use lactose-free dairy or fortified plant milks.")
    if info.goal == "lose-weight":
        guidelines.extend([
            "Aim for a 300-500 kcal deficit.",
            "High-volume, low-calorie foods (salads, soups).",
            "30-40 minutes of brisk walking or cardio, 5x/week."
        ])
    elif info.goal == "gain-weight":
        guidelines.extend([
            "300-400 kcal surplus with 1.6-2.2 g/kg protein.",
            "Strength training 3-4x/week.",
            "Add calorie-dense snacks (nut butters, trail mix)."
        ])
    elif info.goal == "post-surgery-guidance":
        guidelines.extend([
            "Focus on soft, easily digestible foods as advised.",
            "Ensure adequate protein and vitamin C for healing.",
            "Hydrate well and follow medical guidance."
        ])
    else:
        guidelines.append("Balanced plate: half veggies, quarter protein, quarter whole grains.")

    day_plan = [
        {
            "meal": "Breakfast",
            "ideas": [
                "Oatmeal with chia and berries",
                "Veggie omelette" if info.food_type != "vegan" else "Tofu scramble",
                "Smoothie with spinach, banana, and plant milk"
            ]
        },
        {
            "meal": "Lunch",
            "ideas": [
                "Quinoa bowl with beans and veggies",
                "Grilled chicken salad" if info.food_type == "non-veg" else "Chickpea salad",
                "Lentil soup with whole-grain toast"
            ]
        },
        {
            "meal": "Dinner",
            "ideas": [
                "Stir-fry veggies with tofu/tempeh",
                "Baked fish with steamed veggies" if info.food_type == "non-veg" else "Rajma with brown rice",
                "Vegetable khichdi or millet upma"
            ]
        }
    ]

    return {
        "bmi": round(bmi, 1),
        "bmi_category": category,
        "guidelines": guidelines,
        "sample_day": day_plan
    }

# Recipe finder using free API (TheMealDB/Edamam optional). We'll implement a simple mock using themealdb.
@app.post("/recipes/search")
def recipe_search(payload: RecipeSearch):
    results = []
    try:
        if payload.query:
            r = requests.get("https://www.themealdb.com/api/json/v1/1/search.php", params={"s": payload.query}, timeout=10)
            data = r.json()
            meals = data.get("meals") or []
        elif payload.ingredients:
            r = requests.get("https://www.themealdb.com/api/json/v1/1/filter.php", params={"i": ",".join(payload.ingredients)}, timeout=10)
            data = r.json()
            meals = data.get("meals") or []
        else:
            meals = []

        for m in meals[:12]:
            results.append({
                "id": m.get("idMeal"),
                "title": m.get("strMeal"),
                "thumbnail": m.get("strMealThumb"),
                "category": m.get("strCategory"),
                "area": m.get("strArea"),
            })
    except Exception:
        results = []

    # persist the query optionally
    if payload.user_email:
        create_document("recipesearch", payload)

    return {"results": results}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available" if db is None else "✅ Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["collections"] = db.list_collection_names()
    except Exception as e:
        response["database"] = f"⚠️ {str(e)[:60]}"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
