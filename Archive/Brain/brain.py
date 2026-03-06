class EricaBrain:
    def __init__(self):
        self.last_label = None
    def process(self, detection):
        if not detection:
            current_label = None
        else:
            current_label = detection[0]['label']
        if current_label != self.last_label:
            self.last_label = current_label
            if current_label is not None:
                
                return f"I see a {current_label}."
            
        return None