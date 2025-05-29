class Activity:
    def __init__(self, name, activity_type, start_time, end_time, location, cost=0, notes=""):
        self.name = name
        self.activity_type = activity_type
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.cost = cost
        self.notes = notes

class DailySchedule:
    def __init__(self, day):

        self.day = day
        self.activities = []  
        self.total_cost = 0 

    def add_activity(self, activity):
        self.activities.append(activity)

    def get_schedule_summary(self):
      pass

    def display_schedule(self):
        pass
