from langchain.prompts import PromptTemplate

demand_extraction_template = """You are a travel assistant. When a user provides a travel query, extract and organize the information in the following structured format. If certain details (except `Other Requirements`) are not explicitly mentioned, infer them based on the user's query and general travel knowledge. Ensure each field is enclosed in square brackets `[]` for easy parsing. If no `Other Requirements` are mentioned, leave it blank. If `Meal Cost Range` is missing, assign the default value `[100, 200]`. If the departure or return time is specified as "morning" assume it means "early morning"

**Structured Output Format:**
1. Departure Day: [Day of the Week]
2. Return Day: [Day of the Week]
3. Departure Time: [early morning/late morning/afternoon/evening]
4. Return Time: [early morning/late morning/afternoon/evening]
5. Duration: [Number of Days]
6. Departure City: [City Name]
7. Destination City: [City Name]
8. Other Requirements: [List of Requirements]
9. Hotel Cost: [Luxury/Upscale/Midscale/Economy]
10. Meal Cost Range: [Minimum Cost, Maximum Cost]
11. Budget: [Budget]

**Example Query:**
"I am looking for a 4-day trip from Nanjing to Shenzhen, departing on Saturday early morning and returning on Tuesday afternoon, with a budget of ¥4000. I prefer staying in upscale hotels and dining at restaurants with meal costs ranging from ¥100 to ¥200. I’m interested in exploring historical sites, cultural landmarks, scenic coastal parks, and relaxing natural retreats, along with enjoying diverse cuisines like seafood, Chaoshan, Hakka, and Guangdong dishes. The itinerary should be moderate in intensity, balancing guided exploration with some downtime."

**Expected Response:**
Departure Day: [Saturday]
Return Day: [Tuesday]
Departure Time: [early morning]
Return Time: [afternoon]
Duration: [4]
Departure City: [Nanjing]
Destination City: [Shenzhen]
Other Requirements: [exploring historical sites, cultural landmarks, scenic coastal parks, relaxing natural retreats, seafood, Guangdong dishes]
Hotel Cost: [Upscale]
Meal Cost Range: [100, 200]
Budget: [4000]

**Now respond to the user query based on the examples provided above:**
{user_query}
"""

demand_extraction_prompt = PromptTemplate(
    input_variables=["user_profile","user_query"],  
    template= demand_extraction_template     
)

major_otd_transport_template = """
You are a travel assistant. When a user provides a travel query and specifies available transportation options, select the most suitable mode of transportation from the departure point to the tourist destination. Base your decision on factors such as cost, time, convenience, destination stay duration, user demands, and **departure time preferences** (e.g., early morning, late morning, afternoon, evening). Under similar conditions, prioritize earlier flights or trains to maximize travel time at the destination. Please provide your final answer in the format: Flight Number[] or Train Number[]. You just have to give the best one.

**Important Notes:**
1. You must always provide a valid answer in the format: Flight Number[] or Train Number[]. Do not leave the brackets empty.
2. If no clear best option exists, choose the most cost-effective or convenient option by default.
3. **Departure Time Preference**: If the user explicitly mentions a preferred departure time (e.g., early morning), prioritize options that align with this preference.

**Example Query:**
I plan to travel from Beijing to Shanghai for a four-day trip starting on Saturday early morning. I need budget-friendly accommodation and prefer meals priced between 100 to 200 yuan. I’d like to try Jiangsu and Zhejiang cuisine and visit historical and cultural landmarks. Additionally, I hope the itinerary won't be too rushed, and I prefer to depart in the morning.
Available Transportation Options:
1. Flight Number: 9C8835, Airline: Spring Airlines, Departure Time: 7:25, Arrival Time: 10:00, Price: ¥640, On-Time Performance: 0.99, Average Delay: 0 minutes.
2. Flight Number: CZ3596, Airline: China Southern Airlines, Departure Time: 8:50, Arrival Time: 11:25, Price: ¥570, On-Time Performance: 0.9, Average Delay: 13 minutes.
3. Train Number: G85, Departure Time: 8:00, Arrival Time: 14:51, Second Class Price: ¥793, First Class Price: ¥1302.

**Expected Response:**
Cost Efficiency: CZ3596 offers the lowest ticket price at ¥570, making it the most budget-friendly option compared to ¥640 for 9C8835 and ¥793 for G85 (Second Class).
Time Efficiency: The flight CZ3596 takes approximately 2 hours and 35 minutes, which is significantly faster than the train G85 (nearly 7 hours). This saves valuable time for the user's short four-day trip.
Convenience: The departure time of 8:50 for CZ3596 is more reasonable than the early 7:25 departure for 9C8835, allowing the user some additional preparation time in the morning.
Reliability: While CZ3596's on-time performance is slightly lower (0.9) than 9C8835 (0.99), its average delay of 13 minutes is minor and unlikely to disrupt the itinerary.
Departure Time Preference: CZ3596 departs at 8:50, which aligns with the user's preference for a early morning departure.
Answer: Flight Number[CZ3596]

Please now respond to the question based on the examples provided above. Ensure your final answer in the format: Flight Number[] or Train Number[]. You just have to give the best one.

{user_query}
Available Transportation Options:
{transport_options}
"""

major_dto_transport_template = """
You are a travel assistant. When a user provides a travel query and specifies available transportation options, select the most suitable mode of transportation from the tourist destination back to the departure point. Base your decision on factors such as cost, time, convenience, user demands, and **departure time preferences** (e.g., early morning, late morning, afternoon, evening). Under similar conditions, prioritize later flights or trains to extend the user's travel experience. Please provide your final answer in the format: Flight Number[] or Train Number[]. You just have to give the best one.

**Important Notes:**
1. You must always provide a valid answer in the format: Flight Number[] or Train Number[]. Do not leave the brackets empty.
2. If no clear best option exists, choose the most cost-effective or convenient option by default.
3. **Departure Time Preference**: If the user explicitly mentions a preferred departure time (e.g., evening), prioritize options that align with this preference.

**Example Query:**
I plan to travel from Beijing to Shanghai for a four-day trip starting on Saturday evening. I need budget-friendly accommodation and prefer meals priced between 100 to 200 yuan. I’d like to try Jiangsu and Zhejiang cuisine and visit historical and cultural landmarks. Additionally, I hope the itinerary won't be too rushed, and I prefer to return in the evening.
Available Transportation Options:
1. Flight Number: 9C8835, Airline: Spring Airlines, Departure Time: 19:00, Arrival Time: 21:35, Price: ¥640, On-Time Performance: 0.99, Average Delay: 0 minutes.
2. Flight Number: CZ3596, Airline: China Southern Airlines, Departure Time: 21:50, Arrival Time: 0:25 (next day), Price: ¥570, On-Time Performance: 0.9, Average Delay: 13 minutes.
3. Train Number: G85, Departure Time: 18:00, Arrival Time: 1:00 (next day), Second Class Price: ¥793, First Class Price: ¥1302.

**Expected Response:**
Cost Efficiency: CZ3596 offers the lowest ticket price at ¥570, making it the most budget-friendly option compared to ¥640 for 9C8835 and ¥793 for G85 (Second Class).
Time Efficiency: The flight CZ3596 takes approximately 2 hours and 35 minutes, which is faster than the train G85 (nearly 7 hours). The later departure time of 21:50 allows the user to enjoy more time in Shanghai before leaving.
Convenience: CZ3596's departure time of 21:50 is ideal for a user looking to maximize their time in the destination city while still providing a convenient evening return flight.
Reliability: While CZ3596's on-time performance is slightly lower (0.9) than 9C8835 (0.99), its average delay of 13 minutes is minor and unlikely to disrupt the itinerary.
Departure Time Preference: CZ3596 departs at 21:50, which aligns with the user's preference for an evening return.
Answer: Flight Number[CZ3596]

Please now respond to the question based on the examples provided above. Ensure your final answer in the format: Flight Number[] or Train Number[]. You just have to give the best one.

{user_query}
Available Transportation Options:
{transport_options}
"""

major_otd_transport_prompt = PromptTemplate(
    input_variables=["user_query", "transport_options"],  
    template= major_otd_transport_template
)

major_dto_transport_prompt = PromptTemplate(
    input_variables=["user_query", "transport_options"],  
    template= major_dto_transport_template
)

attraction_rank_template = """
You are a travel assistant. When a user provides a travel query and specifies a list of points of interest, sort the POIs based on user demands and specific criteria. Provide the result as a list of POI IDs in the sorted order.

**Example Query:**
I plan to travel from Beijing to Shanghai for a four-day trip starting on Saturday. I need budget-friendly accommodation and prefer meals priced between 100 to 200 yuan. I’d like to try Jiangsu and Zhejiang cuisine and visit historical and cultural landmarks. Additionally, I hope the itinerary won't be too rushed.
List of POIs:
POI ID: 10521129, Name: Shanghai Railway Museum, Rating: 4.5, Heat Score: 3.6, Sight Level: 3A, Price: ¥10.0, Tags: Museum; venue exhibition hall, Features: Visit real old locomotives
POI ID: 87854, Name: Shanghai Postal Museum, Rating: 4.7, Heat Score: 4.1, Sight Level: 3A, Price: ¥0.0, Tags: Museums; Venue exhibition hall, Features: Historic Post Building
POI ID: 10533456, Name: World Expo Museum, Rating: 4.7, Heat Score: 6.0, Sight Level: 3A, Price: ¥0.0, Tags: Museums; Venue exhibition hall, Features: A museum that comprehensively displays the special topics of the Expo
POI ID: 90595, Name: China National Maritime Museum, Rating: 4.7, Heat Score: 6.4, Sight Level: 4A, Price: ¥27.0, Tags: Explore the Exhibition Hall; Hidden Gems for Kids, Features: Understanding China's Maritime History Simulation Model; The First Domestic Maritime-themed Museum
POI ID: 91002, Name: People's Square, Rating: 4.7, Heat Score: 5.9, Sight Level: 3A, Price: ¥0.0, Tags: Walking baby treasure land; City coordinates, Features: Shanghai Landmark and Transportation Hub

**Example Response:**
Given your preferences for budget-friendly attractions, historical and cultural landmarks, and a relaxed itinerary, here's the sorted list of POIs based on relevance:
Shanghai Postal Museum (POI ID: 87854) - Offers free entry, historic significance, and a focus on cultural history.
China National Maritime Museum (POI ID: 90595) - A maritime-themed museum providing rich historical insights at a modest cost.
People's Square (POI ID: 91002) - A central landmark with no entry fee, perfect for a leisurely visit and cultural exploration.
Shanghai Railway Museum (POI ID: 10521129) - Affordable and showcases historical locomotives, fitting well into a historical itinerary.
World Expo Museum (POI ID: 10533456) - Comprehensive and free, but higher heat score suggests it may be more crowded, so better reserved for a less busy day.
Final Answer: Attractions[87854,90595,91002,10521129,10533456]

**Important Notes:**
- The output must be a **unique and ordered list of POI IDs**.
- Do not include any duplicates or irrelevant IDs.
- **Do not use any POI IDs from the example unless they are explicitly provided in the user's POI list.**
- Ensure the final answer strictly follows the format: `Attractions[ID1,ID2,ID3,...]`.

Please now respond to the question based on the examples and rules provided above. Focus only on the POIs provided in the user's list and ignore any IDs from the example unless they are explicitly included in the user's list.

{user_query}
List of POIs:
{attractions}
"""

attraction_rank_prompt = PromptTemplate(
    input_variables=["user_query", "attractions"],
    template= attraction_rank_template
)

daily_schedule_template = """You are a travel assistant responsible for creating a sightseeing-focused itinerary. Your task is to generate a **well-structured and realistic travel plan** based on the user's preferences while considering **arrival and departure times**.  

### **Key Guidelines:**  

1. **Arrival and Departure Considerations:**  
   - Plan activities around the user's **arrival and departure times** to maximize sightseeing opportunities.  
   - Ensure that the schedule **does not include sightseeing activities that conflict with travel times**.  
   - On the **first and last day**, prioritize activities that are close to the arrival/departure location to minimize transit time.  

2. **Balanced and Realistic Schedule:**  
   - Allocate sufficient time for each attraction based on its **recommended duration**.   
   - Ensure **each day has an even distribution** of activities without being too packed or too empty.  

3. **User Preferences:**  
   - Select **the most relevant POIs** based on the user's stated interests.  
   - Prioritize diverse and engaging experiences rather than simply listing all available POIs.  

4. **No Duplicate Attractions:**  
   - **Each POI should only appear once** in the entire itinerary.  
   - If the user has a multi-day trip, distribute POIs evenly across different days to maintain variety.  

5. **POI ID Consistency:**  
   - Each attraction must include its **correct POI ID**, ensuring alignment with the provided POI list.  
   - **Do not assign POI IDs to meal times (lunch and dinner).**  

6. **Meal Integration Rules:**  
   - Include **lunch and dinner** at appropriate times, but **do not specify exact restaurants**.  
   - Meals should only be included **if they are adjacent to sightseeing activities**.  
   - **Do not include standalone meal times** (e.g., a day cannot consist of just "lunch" without sightseeing).  
   - **Breakfast should not be included**, as it is assumed to be handled independently.  

7. **Flexibility & Realism:**  
   - **Do not include hotels or accommodations** in the itinerary.  
   - **Do not add restaurants as POIs**—meals should be noted as "Lunch" or "Dinner" without specific locations.  
   - If needed, allow for **some free time**, but only when it makes sense (e.g., before departure).  

---

### **Example Format (for reference, do not include in final output):**  
✅ **Correct Example:**  
Day 2:  
8:30–10:00: Morning exploration at Binjiang Park (POI ID: 1)  
10:30–13:30: Explore Xintiandi (POI ID: 2)  
13:30–14:30: Lunch  
15:00–17:30: Shanghai Glass Museum (POI ID: 11)  
17:30–18:30: Early dinner  

❌ **Incorrect Example (What to Avoid):**  
- 🚫 Including hotels: **"Check into the Luojiahu Hotel (POI ID: 12)"**  
- 🚫 Adding restaurant POIs: **"Dinner at Qingdao Haiweiyuan (POI ID: 14)"**  
- 🚫 Standalone meals: **"Day 5: Lunch" (without sightseeing before/after)**  

---

{user_query}  
**Arrival time in the destination city on the first day:** {arrival_time}  
**Departure time on the final day:** {departure_time}  
**List of POIs:**  
{attractions}  
"""

daily_schedule_prompt = PromptTemplate(
    input_variables=["user_query","arrival_time","departure_time", "attractions"],
    template= daily_schedule_template
)

daily_schedule_extract_template = """Convert the sightseeing itinerary into the format [POI ID, 1000, POI ID] for each day. Replace "POI ID" with the respective POI ID from the list. Use "1000" to represent lunch or dinner, depending on its placement in the schedule. Do not include breakfast since it is assumed to be handled independently. Ensure that the sequence of visits is accurate.

- **Use `1000` only to represent lunch or dinner**

**Example Input:**
Daily Schedule:
Day 2:
8:30–10:00: Morning exploration at Binjiang Park (POI ID: 1)
10:30–13:30: Explore Xintiandi (POI ID: 2)
13:30–14:30: Lunch near Xintiandi
15:00–17:30: Shanghai Glass Museum (POI ID: 11)
17:30–18:30: Early dinner

**Example Output:**
Day2: [1, 2, 1000, 11, 1000]

Please respond **only with the formatted output** based on the example provided above.

Daily Schedule:
{schedule}

"""

daily_schedule_extract_prompt = PromptTemplate(
    input_variables=["attractions", "schedule"],
    template= daily_schedule_extract_template
)

restaurant_select_template = """You are a travel assistant specializing in personalized restaurant recommendations. When provided with a user’s travel query and a list of restaurants, your task is to analyze the query and select the most suitable restaurant. Use the restaurant details provided to make an informed decision. Respond only in the format Restaurant[restaurant_id], where restaurant_id corresponds to the identifier of the selected restaurant.

**Example Input:**
I plan to travel from Beijing to Shanghai for a four-day trip starting on Saturday. I need budget-friendly accommodation and prefer meals priced between 100 to 200 yuan. I’d like to try Jiangsu and Zhejiang cuisine and visit historical and cultural landmarks. Additionally, I hope the itinerary won't be too rushed.
Restaurant ID: 1, Name: Crowne Plaza Shanghai Saint Noah Hotel Noah Xuan, Avg Price: ¥164, Category: Jiangsu and Zhejiang Cuisine, Stars: 4.0, Good Remarks: 357.0, Bad Remarks: 13.0, Product Rating: 7.9, Environment Rating: 8.7, Service Rating: 8.0
Restaurant ID: 2, Name: Tang Palace, Avg Price: ¥172, Category: Guangdong cuisine, Stars: 3.0, Good Remarks: 4134.0, Bad Remarks: 312.0, Product Rating: 6.9, Environment Rating: 6.9, Service Rating: 6.9
Restaurant ID: 3, Name: Crowne Plaza Shanghai Saint Noah's Kitchen, Avg Price: ¥149, Category: Buffet, Stars: 3.0, Good Remarks: 1367.0, Bad Remarks: 84.0, Product Rating: 6.9, Environment Rating: 6.9, Service Rating: 6.9

**Example Output:**
Restaurant[1]

Please now respond to the question based on the examples provided above. Respond only in the format Restaurant[restaurant_id], where restaurant_id corresponds to the identifier of the selected restaurant. **When selecting a restaurant, prioritize lower prices.**
{user_query}
List of Restaurants:
{restaurants}
"""

restaurant_select_prompt = PromptTemplate(
    input_variables=["user_query", "restaurants"],
    template= restaurant_select_template
)

hotel_select_template = """You are a travel assistant specializing in personalized hotel recommendations. When provided with a user’s travel query and a list of hotels, your task is to analyze the query and select the most suitable hotel. Use the hotel details provided to make an informed decision. Respond only in the format Hotel[hotel_id], where hotel_id corresponds to the identifier of the selected hotel.

**Example Input:**
I plan to travel from Beijing to Shanghai for a four-day trip starting on Saturday. I need budget-friendly accommodation and prefer hotels priced between 500 to 1000 yuan. I’d like to stay in a comfortable and well-rated hotel with good service and environment. Additionally, I hope the hotel is conveniently located near tourist attractions.
Hotel ID: 1, Name: Zhuhai Chimelong Hengqin Bay Hotel, Avg Price: ¥1371, Category: Luxury, Rating: 5.0/5, Product Rating: 9.3/10, Environment Rating: 9.3/10, Service Rating: 9.3/10
Hotel ID: 2, Name: Guilin Shenlong Health Resort Hotel, Avg Price: ¥277, Category: Upscale, Rating: 3.5/5, Product Rating: 7.3/10, Environment Rating: 7.3/10, Service Rating: 7.4/10
Hotel ID: 3, Name: Guorui Xinju Hotel Apartments, Avg Price: ¥163, Category: Economy, Rating: 4.5/5, Product Rating: 8.4/10, Environment Rating: 8.8/10, Service Rating: 8.5/10

**Example Output:**
Hotel[3]

Please now respond to the question based on the examples provided above. Respond only in the format Hotel[hotel_id], where hotel_id corresponds to the identifier of the selected hotel. **When selecting a hotel, prioritize lower prices while still meeting the user's requirements.**

{user_query}
List of Hotels:
{hotels}
"""

hotel_select_prompt = PromptTemplate(
    input_variables=["user_query", "hotels"],
    template=hotel_select_template
)

day_template = """You are a professional travel planning assistant, skilled in creating concise and flexible one-day itineraries based on the opening hours of attractions and dining times at restaurants. Please generate a brief daily itinerary based on the following data, following these requirements:  

---

### **Formatting Requirements**  
1. **Time Slots**: Clearly mark the time for each activity using a time range.  
   - For attractions, ensure the time slots match the recommended visit duration provided in the data.  
   - **Example:**  
     ✅ **14:00–17:00 | Tianding Mountain Tourism Town** (Recommended Duration: 3–4 hours)  
     ❌ **14:00–15:30 | Tianding Mountain Tourism Town** (Allocated time is too short)  
2. **Activity Details**: Provide a concise but vivid description of each activity or location, focusing on its key features, main attractions, and why it’s recommended.  
3. **Additional Information**: Include essential details such as recommended duration, opening hours, and ticket prices. All these information must strictly match the provided data. Do not modify or invent any information.
4. **Meal Suggestions**: Incorporate lunch and dinner plans, recommending local specialties and describing the restaurant’s ambiance and average cost per person.  
5. **Language Style**: Use fluent, natural language suitable for quick reference by travelers. Avoid academic or overly complex expressions.  
6. **Content Scope**: Focus on the travel experience without delving into historical or background details. 
7. **Direct Output**: Provide content directly without introductory or concluding statements.  
8. **Name Consistency**: Always use the exact `Name` field from the data for attractions and restaurants. Do not translate, modify, or replace it with other names.

---

### **Additional Rules**  
1. **One Activity per Time Slot**: Ensure only one attraction or activity is scheduled in each time slot.   
2. **Time Management**: Ensure the itinerary is realistic and accounts for travel time between locations.
3. **Adherence to Recommended Duration**: Ensure that all activities align with the recommended duration provided, avoiding any time conflicts. **Do not modify the "recommended duration" information for any activity.** If time conflicts arise, adjust the start and end times of activities while respecting their recommended durations.

---

### **Input Format**  
Here is the data for the daily list of attractions and restaurants:  

```
{activities}
```

---

### **Example Output (for reference only)** 

### 09:00–10:00 | Northeast Tiger Forest Park  
Start your day at **Northeast Tiger Forest Park**, the world’s largest wild park for Northeast Tigers. Observe these majestic animals in their natural habitat, including white tigers, lions, and other exotic wildlife.  
- **Opening Hours**: 08:30–16:00 (seasonal variations)  
- **Entrance Fee**: ¥105  
- **Recommended Duration**: 1-3 hours  

---

### 12:00–13:00 | Lunch at Guandong Fumanyuan Iron Pot Stewed  
For lunch, savor hearty **Farmhouse Cuisine** at **Guandong Fumanyuan Iron Pot Stewed**. Enjoy the rustic flavors of traditional dishes in a cozy setting.  
- **Cuisine Type**: Farmhouse  
- **Average Cost**: ¥35  

---

Please generate the daily itinerary in **English only**, adhering strictly to the above format!
"""

day_prompt = PromptTemplate(
    input_variables=["activities"],
    template= day_template
)

frist_day_template = """You are a professional travel planning assistant, skilled in creating concise and flexible itineraries for the **first day** of a trip. Focus on travel arrangements and hotel check-in. Please generate a brief daily itinerary based on the following data, following these requirements:    

---

### **Formatting Requirements**  
1. **Time Slots**: Clearly mark the time for each activity using a time range.  
   - For attractions, ensure the time slots match the recommended visit duration provided in the data.  
   - **Example:**  
     ✅ **14:00–17:00 | Tianding Mountain Tourism Town** (Recommended Duration: 3–4 hours)  
     ❌ **14:00–15:30 | Tianding Mountain Tourism Town** (Allocated time is too short) 
2. **Descriptions**: Use concise, vivid descriptions to highlight each activity, including key features, attractions, or reasons for the recommendation.  
3. **Essential Details**: Include specific information such as opening hours, ticket prices, recommended duration, and other relevant highlights (e.g., ambiance for restaurants or rating for hotels).  
   - **Important:** All names, prices, and details must strictly match the provided data. Do not modify or invent any information.
4. **Travel Details**:  
   - The first day must begin with a transportation segment.  
   - **Departure and arrival times of transportation must match the given transportation data exactly. Do not modify these times.**  
5. **Time Adjustment Rules**:  
   - Prioritize key activities such as hotel check-in and the most highly rated attractions.  
   - Discard or shorten less critical activities to accommodate travel time or delays.
6. **Hotel Stay**: After arriving in the city, include a visit to the hotel for check-in. Mention hotel check-in details, including name, category, average price, and key highlights from reviews.   
7. **Name Consistency**: Always use the exact `Name` field from the data for attractions, hotel and restaurants. Do not translate, modify, or replace it with other names.
8. **Language Style**: Use fluent, natural language suitable for quick reference. Avoid academic or overly formal expressions.  
9. **Direct Output**: Provide content directly without introductory or concluding statements.  

---

### **Additional Rules**  
1. **One Activity per Time Slot**: Ensure only one attraction or activity is scheduled in each time slot. If the JSON data includes multiple attractions for the same time, split them into separate slots or discard less critical ones if time is insufficient.  
2. **Time Management**: Ensure the itinerary is realistic and accounts for travel time between locations.
3. **Adherence to Recommended Duration**: Ensure that all activities align with the recommended duration provided, avoiding any time conflicts. **Do not modify the "recommended duration" information for any activity.** If time conflicts arise, adjust the start and end times of activities while respecting their recommended durations.
4. **Resolve Time Conflicts:** If there are overlapping or conflicting activities, reorganize the schedule to ensure a logical flow between activities.

---

### **Input Format**  
Here is the data format for the daily list of attractions, restaurants, travel details, and hotel information:  

```
{activities}
```  

---

### **Example Output (for reference only)**  

### 06:45–09:35 | Travel to Changchun  
Start your journey with a **flight** on **CA1985** from your departure city to **Changchun Longjia International Airport**. Depart at 06:45 and arrive at 09:35, ensuring a punctual and comfortable trip.  
- **Ticket Price**: ¥750  

---

### 10:30–11:00 | Check-in at Yuefu Grand Hotel  
After arriving in Changchun, check in at **Yuefu Grand Hotel**, an **Upscale hotel** with a 4/5 rating. Enjoy a comfortable stay at an average price of ¥179 per night. Guests have praised the hotel for its **pleasant environment** and **good service**.  
- **Average Price Per Night**: ¥179  

---

### 14:00–17:00 | Tianding Mountain Tourism Town  
Explore **Tianding Mountain Tourism Town**, a comprehensive parent-child entertainment destination. Enjoy attractions like Cute Pet Paradise, Deer Garden, Rainbow Slide, and more, all set in a beautiful natural environment. Perfect for families and nature enthusiasts.  
- **Opening Hours**: To be confirmed  
- **Entrance Fee**: Free  
- **Recommended Duration**: 3-4 hours  

---

Please generate the daily itinerary in **English only**, adhering strictly to the above format!
"""

frist_day_prompt = PromptTemplate(
    input_variables=["activities"],
    template= frist_day_template
)

last_day_template = """You are a professional travel planning assistant, skilled in creating concise and flexible itineraries for the **final day** of a trip. **Today is the last day of the trip, and the traveler is returning to their final destination.** The final city of the trip is **{city1}**, and the trip ends upon arrival there. Focus on activities before departure, travel arrangements (e.g., flights or trains), and hotel check-out if applicable. Please generate a brief daily itinerary based on the following data, following these requirements:   

---

### **Formatting Requirements**  
1. **Time Slots**: Clearly mark the time for each activity using a time range.  
   - For attractions, ensure the time slots match the recommended visit duration provided in the data.  
   - **Example:**  
     ✅ **14:00–17:00 | Tianding Mountain Tourism Town** (Recommended Duration: 3–4 hours)  
     ❌ **14:00–15:30 | Tianding Mountain Tourism Town** (Allocated time is too short) 
2. **Descriptions**: Use concise, vivid descriptions to highlight each activity, including key features, attractions, or reasons for the recommendation.  
3. **Essential Details**: Include specific information such as opening hours, ticket prices, recommended duration, and other relevant highlights (e.g., ambiance for restaurants or rating for hotels).  
   - **Important:** All names, prices, and details must strictly match the provided JSON data. Do not modify or invent any information.
4. **Travel Details**: Select the **last transportation segment of the trip** (either flight or train).  
   - The itinerary **ends** after this segment. **Do not schedule any activities or additional transportation after this.** 
   - **Once the selected transportation to {city2} is scheduled, no further activities or transportation should be added.**    
   - **Do not create additional transportation segments beyond what is explicitly listed.**    
   - **Departure and arrival times of transportation must match the given transportation data exactly. Do not modify these times.**
   - If delays or schedule conflicts arise, **adjust the itinerary** to ensure a timely return by removing lower-priority activities. 
5. **Hotel Check-Out**: If applicable, include hotel check-out time and luggage storage options. Highlight any late check-out policies if relevant. 
6. **Language Style**: Use fluent, natural language suitable for quick reference. Avoid academic or overly formal expressions.  
7. **Direct Output**: Provide content directly without introductory or concluding statements.  
8. **Name Consistency**: Always use the exact `Name` field from the data for attractions and restaurants. Do not translate, modify, or replace it with other names. 

---

### **Additional Rules**  
1. **One Activity per Time Slot**: Ensure only one attraction or activity is scheduled in each time slot. 
2. **Time Management**: Ensure the itinerary is realistic and accounts for travel time between locations.
3. **Adherence to Recommended Duration**: Ensure that all activities align with the recommended duration provided, avoiding any time conflicts. **Do not modify the "recommended duration" information for any activity.** If time conflicts arise, adjust the start and end times of activities while respecting their recommended durations.
4. **No Activities After Returning Home:** On the last day, do not schedule any activities after the transportation (e.g., flight or train) that brings the traveler back home.
5. **Buffer Time for Departure**:  
   - For **flights**, always allocate **at least 2 hours** before the scheduled departure time to account for travel to the airport, security checks, and potential delays.  
   - For **trains**, allocate **at least 1 hour** before the scheduled departure time to account for travel to the station and boarding.  
   Adjust the itinerary accordingly to ensure a stress-free departure.  
---

### **Input Format**  
Here is the data format for the daily list of attractions, restaurants, travel details:  

```
{activities}
```  

---

### **Example Output (for reference only)**  

### 09:00–10:30 | Visit Badaxia Square  
Start your last day with a relaxing stroll at **Badaxia Square**, a picturesque square featuring a stunning 3000-meter coastline and a natural, open layout. Enjoy the variety of tree species and the serene atmosphere, making it an ideal spot for sightseeing and unwinding.  
- **Entrance Fee**: Free  
- **Recommended Duration**: 1.5 hours  

### 12:00 | Hotel Check-Out  
Check out from your hotel and store your luggage if needed. Ensure you have all your belongings before heading to the airport.  

### 16:15–19:35 | Flight to Shenzhen  
Conclude your trip with a **flight** on **ZH3019** from **Qingdao** to **Shenzhen**. Depart at 16:15 and arrive at 19:35, ensuring a smooth and timely journey back home.  
- **Ticket Price**: ¥1260  
- **On-Time Performance**: 80%  
- **Average Delay**: 12 minutes  

---

Please generate the daily itinerary in **English only**, adhering strictly to the above format!
"""

last_day_prompt = PromptTemplate(
    input_variables=["city1", "city2", "activities"],
    template= last_day_template
)

planner_instruction = """You are a travel planner tasked with creating a concise and detailed travel plan based on the query and the provided information. The output should include the following sections and adhere to these specifications:  

### 1. **Daily Itinerary**  
   - Divide the trip by days.  
   - Specify the current city (e.g., "from A to B" if traveling between cities).  
   - Include exact timings for each activity (e.g., 10:00–12:00).  
   - Ensure sufficient time for travel, meals, rest, and prioritize key activities logically.  
   - **Important:** All names, prices, and details must strictly match the given information. Do not modify or invent any information.

### 2. **Transportation**  
   - Provide flight or train numbers, departure/arrival times, ticket prices, and durations for intercity travel.  
   - **First Day Transportation:** Specify only the transportation options available on the first day for travel from the departure city to the destination city.
   - **Last Day Transportation:** Specify only the transportation options available on the last day for travel from the destination city back to the departure city.

### 3. **Accommodation**  
   - Specify the hotel name, rating, check-in/check-out times, and average price per night.  

### 4. **Attractions**  
   - Detail attraction names, opening hours, entrance fees, recommended duration, and cultural or historical significance.  

### 5. **Dining**  
   - List restaurant names, cuisine types, must-try dishes, average cost per person, and operating hours.  

### 6. **Additional Notes**  
   - **One Activity per Time Slot**: Ensure only one attraction or activity is scheduled in each time slot.  
   - **Time Management**: Ensure the itinerary is realistic and accounts for travel time between locations. 
   - **Distance Consideration**: Prioritize activities that are geographically close to each other to minimize unnecessary travel time.

### Output Formatting  
- Use clear headings (e.g., **Day 1 Itinerary**).  
- Present information in bullet points or short paragraphs for readability.  
- Ensure alignment with the user’s preferences and query context.  

Ensure that the plan is logical, concise, and detailed, while maintaining alignment with the user’s budget, interests, and time constraints. The output should avoid unnecessary elaboration or unrelated details.  

***** Example *****
**Example Query:** 
Planning a 3-day trip from Chongqing to Shenyang, departing on Wednesday and returning on Friday, with a focus on exploring historical landmarks, local cuisine, and leisurely shopping in vibrant commercial areas. The trip includes Economy accommodations with breakfast, averaging ¥74 per night, and a daily budget under ¥500, with meal costs around ¥50–¥70 per person. The itinerary aims to blend cultural experiences, such as visiting museums and ancient architecture, with free time to relax and enjoy the city.

**Example Travel Plan:**
**Day 1 Itinerary: Chongqing to Shenyang **

### 06:10–11:00 | Travel to Shenyang
Start your journey with a **flight** on **CA4163** from Chongqing to Shenyang. Depart at 06:10 and arrive at 11:00, ensuring a punctual and comfortable trip.
- **Ticket Price**: ¥900

---

### 12:00–12:30 | Check-in at Jijin E-Family Theme Hotel
After arriving in Shenyang, check in at **Jijin E-Family Theme Hotel**, an **Economy hotel** with a 3.5 rating. Enjoy a comfortable stay at an average price of ¥74 per night. Guests have praised the hotel for its **pleasant environment** and **good service**.
- **Average Price Per Night**: ¥74

---

### 14:00–16:00 | Explore Taiyuan Street
Spend some time exploring **Taiyuan Street**, one of Shenyang's most bustling commercial districts. Modeled after Tokyo's Ginza shopping area, it is known as "Northeast China's First Golden Street." The street features a mix of historic Chinese buildings from the 1920s and modern skyscrapers, offering a unique blend of the old and new.
- **Opening Hours**: All day (Monday-Sunday, January 1-December 31)
- **Entrance Fee**: Free
- **Recommended Duration**: 1-3 hours

---

### 18:00–19:30 | Dinner at Laotieling Shengchuan (Taiyuan South Street Store)
Enjoy a delicious dinner at **Laotieling Shengchuan (Taiyuan South Street Store)**. This popular local chain is known for its tasty skewers, chicken wings, and grilled dishes. A great place to experience local flavors.
- **Location**: Between Nanba Road and Nanqi Road (next to Xiaotudou)
- **Operating Hours**: Monday to Sunday, 16:00-02:00
- **Average Cost**: ¥70 per person

**Day 2 Itinerary**

...

**Itinerary for the Last Day of the Trip**

...

***** Example Ends *****


**Given information:**
{text}

**Query:** 
{query}

**Travel Plan:**
"""

planner_agent_prompt = PromptTemplate(
                        input_variables=["text","query"],
                        template = planner_instruction,
                        )

if __name__ == "__main__":
    formatted_prompt = demand_extraction_prompt.format(user_profile="Hello, how are you?",user_query="e")
    print(formatted_prompt)
