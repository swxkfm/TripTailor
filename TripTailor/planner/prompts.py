from langchain.prompts import PromptTemplate


ZEROSHOT_REACT_INSTRUCTION = """Collect information for a query plan using interleaving 'Thought', 'Action', and 'Observation' steps. Ensure you gather valid information related to transportation, dining, attractions, and accommodation. All information should be written in Notebook, which will then be input into the Planner tool. Note that the nested use of tools is prohibited. 'Thought' can reason about the current situation, and 'Action' can have 8 different types:
(1) FlightSearch[Departure City, Destination City, Date]:
Description: A flight information retrieval tool.
Parameters:
Departure City: The city you'll be flying out from.
Destination City: The city you aim to reach.
Date: The date of your travel in YYYY-MM-DD format.
Example: FlightSearch[New York, London, 2022-10-01] would fetch flights from New York to London on October 1, 2022.

(2) GoogleDistanceMatrix[Origin, Destination, Mode]:
Description: Estimate the distance, time and cost between two cities.
Parameters:
Origin: The departure city of your journey.
Destination: The destination city of your journey.
Mode: The method of transportation. Choices include 'self-driving' and 'taxi'.
Example: GoogleDistanceMatrix[Paris, Lyon, self-driving] would provide driving distance, time and cost between Paris and Lyon.

(3) AccommodationSearch[City]:
Description: Discover accommodations in your desired city.
Parameter: City - The name of the city where you're seeking accommodation.
Example: AccommodationSearch[Rome] would present a list of hotel rooms in Rome.

(4) RestaurantSearch[City]:
Description: Explore dining options in a city of your choice.
Parameter: City – The name of the city where you're seeking restaurants.
Example: RestaurantSearch[Tokyo] would show a curated list of restaurants in Tokyo.

(5) AttractionSearch[City]:
Description: Find attractions in a city of your choice.
Parameter: City – The name of the city where you're seeking attractions.
Example: AttractionSearch[London] would return attractions in London.

(6) CitySearch[State]
Description: Find cities in a state of your choice.
Parameter: State – The name of the state where you're seeking cities.
Example: CitySearch[California] would return cities in California.

(7) NotebookWrite[Short Description]
Description: Writes a new data entry into the Notebook tool with a short description. This tool should be used immediately after FlightSearch, AccommodationSearch, AttractionSearch, RestaurantSearch or GoogleDistanceMatrix. Only the data stored in Notebook can be seen by Planner. So you should write all the information you need into Notebook.
Parameters: Short Description - A brief description or label for the stored data. You don't need to write all the information in the description. The data you've searched for will be automatically stored in the Notebook.
Example: NotebookWrite[Flights from Rome to Paris in 2022-02-01] would store the informatrion of flights from Rome to Paris in 2022-02-01 in the Notebook.

(8) Planner[Query]
Description: A smart planning tool that crafts detailed plans based on user input and the information stroed in Notebook.
Parameters: 
Query: The query from user.
Example: Planner[Give me a 3-day trip plan from Seattle to New York] would return a detailed 3-day trip plan.
You should use as many as possible steps to collect engough information to input to the Planner tool. 

Each action only calls one function once. Do not add any description in the action.

Query: {query}{scratchpad}"""



zeroshot_react_agent_prompt = PromptTemplate(
                        input_variables=["query", "scratchpad"],
                        template=ZEROSHOT_REACT_INSTRUCTION,
                        )

PLANNER_INSTRUCTION = """You are a travel planner tasked with creating a concise and detailed travel plan based on the query and the provided information. The output should include the following sections and adhere to these specifications:  

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

### 6. **Budget Breakdown**  
   - Align with the specified budget and provide a cost breakdown for transportation, accommodations, meals, and attractions.  
   - Offer alternatives if the total cost exceeds the budget.  

### 7. **Additional Notes**  
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

COT_PLANNER_INSTRUCTION = """You are a travel planner tasked with creating a concise and detailed travel plan based on the query and the provided information. The output should include the following sections and adhere to these specifications:  

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

### 6. **Budget Breakdown**  
   - Align with the specified budget and provide a cost breakdown for transportation, accommodations, meals, and attractions.  
   - Offer alternatives if the total cost exceeds the budget.  

### 7. **Additional Notes**  
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
Let's think step by step. First, """

REACT_PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight/train numbers (e.g., F0123456) and cost, restaurant names and cost, hotel names and cost, and attractions names and cost. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with common sense. Attraction visits and meals are expected to be diverse. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B). Do not use any Markdown formatting (e.g., do not use `**` for bold text). Solve this task by alternating between Thought, Action, and Observation steps. The 'Thought' phase involves reasoning about the current situation. The 'Action' phase can be of two types:
(1) CostEnquiry[Sub Plan]: This function calculates the cost of a detailed sub plan(except transportation cost), which you need to input the people number and plan in JSON format. The sub plan should encompass a complete one-day plan. An example will be provided for reference.
(2) Finish[Final Plan]: Use this function to indicate the completion of the task. You must submit a final, complete plan as an argument.
***** Example *****
Query: Could you create a travel plan from Ithaca to Charlotte spanning 3 days, from Wednesday to Friday, with a daily budget under ¥500 and meal cost range of ¥50 to ¥100?
You can call CostEnquiry like CostEnquiry[{{"day": 1,"current_city": "from Ithaca to Charlotte","transportation": "Flight Number: F3633413, from Ithaca to Charlotte, Cost: ¥450","attraction": "The Charlotte Museum of History, Cost: ¥10","lunch": "Cafe Maple Street, Cost: ¥10","dinner": "Bombay Vada Pav, Cost: ¥15","accommodation": "Affordable Spacious Refurbished Room in Bushwick!, Cost: ¥250"}}]
You can call Finish like Finish[Day: 1
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Cost: ¥450
Attraction: The Charlotte Museum of History, Cost: ¥10
Lunch: Cafe Maple Street, Cost: ¥60
Dinner: Bombay Vada Pav, Cost: ¥55
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Cost: ¥250

Day 2:
Current City: Charlotte
Transportation: -
Attraction: The Mint Museum, Cost: ¥10;Romare Bearden Park, Cost: ¥0
Lunch: Birbal Ji Dhaba, Cost: ¥66
Dinner: Pind Balluchi, Cost: ¥67
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Cost: ¥250

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Cost: ¥500
Attraction: Books Monument, Cost: ¥0
Lunch: Olive Tree Cafe, Cost: ¥80
Dinner: Kylin Skybar, Cost: ¥90
Accommodation: -]
***** Example Ends *****

You must use Finish to indict you have finished the task. Do not add any additional explanations in action. And each action only calls one function once. 
Given information: {text}
Query: {query}{scratchpad} """

REFLECTION_HEADER = 'You have attempted to give a sub plan before and failed. The following reflection(s) give a suggestion to avoid failing to answer the query in the same way you did previously. Use them to improve your strategy of correctly planning.\n'

REFLECT_INSTRUCTION = """You are an advanced reasoning agent that can improve based on self refection. You will be given a previous reasoning trial in which you were given access to an automatic cost calculation environment, a travel query to give plan and relevant information. Only the selection whose name and city match the given information will be calculated correctly. You were unsuccessful in creating a plan because you used up your set number of reasoning steps. In a few sentences, Diagnose a possible reason for failure and devise a new, concise, high level plan that aims to mitigate the same failure. Use complete sentences.  

Given information: {text}

Previous trial:
Query: {query}{scratchpad}

Reflection:"""

REACT_REFLECT_PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight/train numbers (e.g., F0123456) and cost, restaurant names and cost, hotel names and cost, and attractions names and cost. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with common sense. Attraction visits and meals are expected to be diverse. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B). Do not use any Markdown formatting (e.g., do not use `**` for bold text). Solve this task by alternating between Thought, Action, and Observation steps. The 'Thought' phase involves reasoning about the current situation. The 'Action' phase can be of two types:
(1) CostEnquiry[Sub Plan]: This function calculates the cost of a detailed sub plan(except transportation cost), which you need to input the people number and plan in JSON format. The sub plan should encompass a complete one-day plan. An example will be provided for reference.
(2) Finish[Final Plan]: Use this function to indicate the completion of the task. You must submit a final, complete plan as an argument.
***** Example *****
Query: Could you create a travel plan from Ithaca to Charlotte spanning 3 days, from Wednesday to Friday, with a daily budget under ¥500 and meal cost range of ¥50 to ¥100?
You can call CostEnquiry like CostEnquiry[{{"day": 1,"current_city": "from Ithaca to Charlotte","transportation": "Flight Number: F3633413, from Ithaca to Charlotte, Cost: ¥450","attraction": "The Charlotte Museum of History, Cost: ¥10","lunch": "Cafe Maple Street, Cost: ¥10","dinner": "Bombay Vada Pav, Cost: ¥15","accommodation": "Affordable Spacious Refurbished Room in Bushwick!, Cost: ¥250"}}]
You can call Finish like Finish[Day: 1
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Cost: ¥450
Attraction: The Charlotte Museum of History, Cost: ¥10
Lunch: Cafe Maple Street, Cost: ¥60
Dinner: Bombay Vada Pav, Cost: ¥55
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Cost: ¥250

Day 2:
Current City: Charlotte
Transportation: -
Attraction: The Mint Museum, Cost: ¥10;Romare Bearden Park, Cost: ¥0
Lunch: Birbal Ji Dhaba, Cost: ¥66
Dinner: Pind Balluchi, Cost: ¥67
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Cost: ¥250

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Cost: ¥500
Attraction: Books Monument, Cost: ¥0
Lunch: Olive Tree Cafe, Cost: ¥80
Dinner: Kylin Skybar, Cost: ¥90
Accommodation: -]
***** Example Ends *****

{reflections}

You must use Finish to indict you have finished the task. And each action only calls one function once.
Given information: {text}
Query: {query}{scratchpad} """

expand_prompt = """**Objective:**  
Expand the provided brief travel itinerary into a detailed and engaging plan, ensuring consistency with the original choices of attractions, restaurants, hotels, and transportation. The expanded itinerary should include specific timings, descriptions, and additional relevant details to enhance the travel experience.

---

**Instructions:**

1. **Maintain Consistency:**  
   - Ensure all attractions, restaurants, hotels, and transportation methods mentioned in the original plan are included in the expanded itinerary.  
   - Do not introduce new attractions, restaurants, hotels, or transportation options unless explicitly requested.  

2. **Add Details:**  
   - Include specific timings for each activity (e.g., 09:00–10:00).  
   - Provide descriptions of the attractions, restaurants, and hotels to make the itinerary more engaging.  
   - Highlight key features, historical significance, or unique aspects of each location.  
   - Mention practical details such as opening hours, entrance fees, and recommended duration for each activity.  

3. **Enhance Flow:**  
   - Organize the itinerary in a logical sequence, ensuring smooth transitions between activities.  
   - Include travel times between locations where applicable.  

4. **Personalize the Experience:**  
   - Suggest optional activities or additional tips (e.g., best times to visit, local customs, or nearby attractions) to enrich the traveler’s experience. 

5. **Direct Output**: 
   - Provide content directly without introductory or concluding statements.  

---

**Original Itinerary:**  
{original_itinerary} 

**Reference Information:**  
{reference_information}  

---

**Output Example:**

**Day 1 Itinerary: Shanghai to Fuzhou**

### 09:00–10:50 | Travel to Fuzhou  
Start your journey with a **flight** on **MF3086** from **Shanghai** to **Fuzhou Changle International Airport**. Depart at 09:00 and arrive at 10:50, ensuring a punctual and comfortable trip.  
- **Ticket Price**: ¥490  

---

### 11:30–12:00 | Check-in at Youjia Inn  
After arriving in Fuzhou, check in at **Youjia Inn**, a budget-friendly accommodation offering a comfortable stay at an average price of ¥232 per night. The inn is conveniently located, making it easy to explore the city’s attractions.  
- **Average Price Per Night**: ¥232  

---

### 12:30–13:30 | Lunch at InterContinental Fuzhou · Fudi  
Head to **InterContinental Fuzhou · Fudi** for a delightful lunch. This restaurant offers a variety of dishes in a sophisticated setting, perfect for a relaxing midday meal.  
- **Average Price Per Person**: ¥122  

---

### 14:00–16:00 | Explore Southern Shaolin Temple  
Visit the **Southern Shaolin Temple**, a historic site known for its cultural significance and serene atmosphere. The temple offers a glimpse into the region’s rich history and martial arts heritage.  
- **Opening Hours**: 08:00–17:00  
- **Entrance Fee**: Free  
- **Recommended Duration**: 1-2 hours  

---

### 16:30–18:00 | Stroll Through Nanjun Guild Hall  
Take a leisurely walk through **Nanjun Guild Hall**, a historic building with a solemn and imposing gate. The hall showcases traditional architecture and offers a peaceful retreat from the bustling city.  
- **Opening Hours**: 08:00–17:00  
- **Entrance Fee**: Free  
- **Recommended Duration**: 1-2 hours  

---

### 18:30–19:30 | Dinner at Fulihua Seafood Restaurant  
End your day with a delightful dinner at **Fulihua Seafood Restaurant**. Enjoy a variety of fresh seafood dishes in a cozy and welcoming atmosphere.  
- **Average Price Per Person**: ¥154  

---

### 20:00–21:30 | Relax at Youjia Inn  
Return to **Youjia Inn** for a restful evening. Take some time to relax and prepare for the next day’s adventures.  

---

**Day 2 Itinerary: Fuzhou**
...

---

**Output:**

"""

planner_agent_prompt = PromptTemplate(
                        input_variables=["text","query"],
                        template = PLANNER_INSTRUCTION,
                        )

cot_planner_agent_prompt = PromptTemplate(
                        input_variables=["text","query"],
                        template = COT_PLANNER_INSTRUCTION,
                        )

react_planner_agent_prompt = PromptTemplate(
                        input_variables=["text","query", "scratchpad"],
                        template = REACT_PLANNER_INSTRUCTION,
                        )

reflect_prompt = PromptTemplate(
                        input_variables=["text", "query", "scratchpad"],
                        template = REFLECT_INSTRUCTION,
                        )

react_reflect_planner_agent_prompt = PromptTemplate(
                        input_variables=["text", "query", "reflections", "scratchpad"],
                        template = REACT_REFLECT_PLANNER_INSTRUCTION,
                        )
