class FlightDataHandler:
    """Handles storing flight planning data temporarily"""
    
    def __init__(self):
        self.active_sessions = {}
    
    def start_session(self, user_id, data):
        self.active_sessions[user_id] = data
    
    def get_session(self, user_id):
        return self.active_sessions.get(user_id)
    
    def update_session(self, user_id, key, value):
        if user_id in self.active_sessions:
            self.active_sessions[user_id][key] = value
    
    def end_session(self, user_id):
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
