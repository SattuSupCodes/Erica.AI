class Verify:
    def __init__(self):
        self.is_active = False
        self.target_id = None
        self.has_asked = False
    def verify_start(self, person_id):
        self.is_active = True
        self.target_id = person_id
        self.has_asked = False
    def should_ask(self):
        if self.is_active and not self.has_asked:
            return True
        else:
            return False
    def mark_asked(self):
        self.has_asked = True
            
        
            
    def process_response(self, response):
        yes_words = ["yes", "y","yeah"]
        no_words = ["no", "n", "nah"]
        if response.strip().lower() in yes_words:
            return "confirmed"
        elif response.strip().lower() in no_words:
            return "rejected"
        else:
            return "invalid"
            
    def reset(self):
        self.is_active = False
        self.target_id = None
        self.has_asked = False