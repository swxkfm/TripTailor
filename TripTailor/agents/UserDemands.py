class DemandsInfo:
    def __init__(self, departure_day=None, return_day=None, departure_time=None, return_time=None, duration=None,
                 departure_city=None, destination_city=None, other_requirements=None,
                 hotel_cost=None, meal_cost_range=None, budget=None):
        self.departure_day = departure_day
        self.return_day = return_day
        self.departure_time = departure_time
        self.return_time = return_time
        self.duration = duration
        self.departure_city = departure_city
        self.destination_city = destination_city
        self.other_requirements = other_requirements
        self.hotel_cost = hotel_cost
        self.meal_cost_range = meal_cost_range
        self.budget = budget

    def __repr__(self):
        return (f"TravelInfo(departure_day={self.departure_day}, return_day={self.return_day}, "
                f"departure_time={self.departure_time}, return_time={self.return_time}, "
                f"duration={self.duration}, departure_city={self.departure_city}, "
                f"destination_city={self.destination_city}, other_requirements={self.other_requirements}, "
                f"hotel_cost={self.hotel_cost}, meal_cost_range={self.meal_cost_range}, budget={self.budget})")
