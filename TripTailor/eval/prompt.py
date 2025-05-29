EXTRACT_PROMPT = """Extract structured JSON data from the following itinerary text, following these rules:  

---

### **Output Format (JSON Schema):**  
```json
{{
  "hotel": [
    {{
      "day": 1,
      "name": "Hotel Name",
      "price_per_night": number
    }}
  ],
  "transportation": [
    {{
      "day": 1,
      "mode": "Transport Mode",
      "route": "Travel Route",
      "number": "Flight/Train Number",
      "time": "Time Range",
      "price": number
    }}
  ],
  "itinerary": {{
    "day_1": [
      {{
        "time": "Time Range",
        "location": "Location Name",
        "price": number,
        "action": "Action Type"
      }}
    ]
  }}
}}
```

---

### **Extraction Guidelines:**  

1. **Ensure each day is separately recorded, with no missing or merged days.**  
   - The itinerary text may contain “Day X” headers or date indicators. These must be used to correctly segment the data into distinct days.  
   - If a day does not contain any relevant activities, set its value to an empty list (`[]`).  

2. **Extract and structure hotel (`hotel`) and transportation (`transportation`) separately:**  
   - **`hotel`**: Extract only lodging-related details.  
   - **`transportation`**: Extract only **long-distance** travel (flights, high-speed trains, intercity buses). Ignore **local** transportation (subways, taxis, short-distance buses).  

3. **Extract itinerary activities (`itinerary`) with specific filtering rules:**  
   - Keep only activities with `"sightseeing"` or `"dining"` as the action type:  
     - `"sightseeing"` – Visiting landmarks, scenic spots, cultural sites, and attending performances.  
       - Any itinerary item that includes a **Recommended Duration:** is considered a sightseeing spot.   
     - `"dining"` – Meals at restaurants, cafes, or eateries (**excluding breakfast**).  

   - **Ignore the following:**  
     - Check-in and check-out events (e.g., "Hotel Check-in", "Depart from Hotel").  
     - Generic exploratory activities **without a specific location** (e.g., "Brief stroll near hotel", "Casual walk near airport", "Exploring nearby streets after arrival").  

   - **Price Extraction:**  
     - Extract numerical values for prices.  
     - If an activity is free or price is not mentioned, set `"price": 0`. 

---  

### **Example Input:**  
```
**Day 1 Itinerary: Beijing to Zhuhai **

### 07:15–10:55 | Travel to Zhuhai  
Start your journey with a **flight** on **CA1479** from **Beijing** to **Zhuhai Jinwan Airport**.  
- **Ticket Price**: ¥1000  

### 11:30–12:00 | Check-in at Zhuhai New Junjing Marriott Hotel  
- **Average Price Per Night**: ¥1224  

### 14:00–16:30 | Yuanming New Garden 
Explore **Yuanming New Garden**, a stunning recreation of the Old Summer Palace in Beijing. 
- **Entrance Fee**: Free  

### 18:00–19:30 | Dinner at Xiongyu Old Local Cuisine  
- **Average Price**: ¥393  

**Itinerary for the Last Day of the Trip**

### 10:00–11:00 | Check-Out and Departure 

### 09:30–11:00 | Visit Lover’s Road (Qinglv Road)  
Take a leisurely walk along **Lover’s Road**, a scenic coastal path in Zhuhai.
- **Entrance Fee**: Free  

### 13:00–14:30 | Flight to Beijing  
Conclude your trip with a **flight** on **CZ3731** from **Zhuhai** to **Beijing**. 
- **Ticket Price**: ¥920  
```

### **Expected JSON Output:**  
```json
{{
  "hotel": [
    {{
      "day": 1,
      "name": "Zhuhai New Junjing Marriott Hotel",
      "price_per_night": 1224
    }}
  ],
  "transportation": [
    {{
      "day": 1,
      "mode": "Flight",
      "route": "Beijing to Zhuhai",
      "number": "CA1479",
      "time": "07:15–10:55",
      "price": 1000
    }},
    {{
      "day": 2,
      "mode": "Flight",
      "route": "Zhuhai to Beijing",
      "number": "CZ3731",
      "time": "13:00–14:30",
      "price": 920
    }}
  ],
  "itinerary": {{
    "day_1": [
      {{
        "time": "14:00–16:30",
        "location": "Yuanming New Garden",
        "price": 0,
        "action": "sightseeing"
      }},
      {{
        "time": "18:00–19:30",
        "location": "Xiongyu Old Local Cuisine",
        "price": 393,
        "action": "dining"
      }}
    ],
    "day_2": [
      {{
        "time": "09:30–11:00",
        "location": "Lover’s Road",
        "price": 0,
        "action": "sightseeing"
      }}
    ]
  }}
}}
```

### **Input:**  
{itinerary} 

### **Output:** 
"""

EVALUATION_PROMPT = """
You are an AI assistant evaluating two travel plans based on following criteria:

### **Evaluation Criteria and Key Factors to Consider:**:
- **Experiences:** Consider both variety and depth. While a diverse range of activities is beneficial, immersive and well-planned experiences that align closely with traveler interests should also be recognized.
- **Itinerary Intensity:** Evaluate how well the plan matches the traveler’s desired itinerary intensity (e.g., relaxed, moderate, packed). Consider the balance between activities and free time, as well as the pacing of the trip.
- **Cuisine:** Assess the suitability of dining choices to the traveler’s stated preferences, including cuisine category and alignment with budget and meal price range.
- **Accommodations:** Evaluate the quality, comfort, and overall fit with the traveler’s stated preferences, including accommodation category and budget range.
- **Transportation:** Assess the practicality of transportation options with a focus on departure and return times, convenience, cost, and suitability for the traveler’s preferences.
- **Total Budget Consideration:** Staying within the budget is essential, but an itinerary that justifies slightly higher costs through premium experiences is viewed positively, whereas strict cost-cutting at the expense of premium experiences is seen as unfavorable.

### **Scoring Scale (Out of 5)**
1. **5 (Excellent):** The itinerary **exceeds expectations**, perfectly aligning with all user preferences. It offers unique, tailored experiences and exceptional value, ensuring a memorable and personalized journey.
2. **4 (Good):** The itinerary **largely meets** the user’s needs, showing a strong level of personalization and value. However, there may be minor gaps in specific preferences or opportunities for deeper engagement that could enhance the overall experience.
3. **3 (Average):** The itinerary **partially satisfies** the user’s query, incorporating some preferences but missing key elements in important areas. It fulfills basic requirements but lacks depth, creativity, or engagement in activities, cultural insights, or personalization, resulting in a feeling of generality and mediocrity.
4. **2 (Poor):** The itinerary **barely meets** expectations, with significant gaps in personalization and relevance. Most elements do not align well with the user’s stated preferences, leading to a less enjoyable and uninspired experience.
5. **1 (Very Poor):** The itinerary **fails to address** the user's query entirely, displaying no relevance to stated preferences. It is completely generic, offering little to no value or consideration for the user's unique needs and interests.

### Output format:
#### Comparative Analysis:
[Please analyze each plan first and then provide a rating in JSON format. Based on the Evaluation Criteria and Key Factors to Consider, provide a detailed comparative analysis of how well each plan meets the traveler’s preferences and the overall quality of each plan, explaining their strengths and weaknesses.]

#### Scoring Results:
```json
{{
  "Personalization Evaluation": {{
    "Scores": {{
      "Plan A": X,
      "Plan B": Y
    }}
  }}
}}
```

### **Input**
- **Query:** {query}
- **Plan A:** {plan_a}
- **Plan B:** {plan_b}
"""
