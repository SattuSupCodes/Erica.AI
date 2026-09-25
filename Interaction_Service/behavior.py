import random


def get_greeting(name, context, emotion=None, trust_level=None, relationship=""):
    if emotion == "happy":
        return random.choice([
            f"you look delightful today {name}~",
            f"happiness looks good on you, {name}"
        ])
    elif emotion == "sad":
        return random.choice([
            f"oh no you look sad {name}...",
            f"why the saddie..."
        ])
    elif emotion == "angry":
        return random.choice([
            f"uh oh who got you angry {name}",
            f"okay i'll behave damn"
        ])

    if trust_level is not None and trust_level >= 0.7:
        return random.choice([
            f"heyyy {name}, good to see you",
            f"{name}! was hoping you'd show up",
            f"oh hoi, Erica at your service, {name}"
        ])
    elif trust_level is not None and trust_level < 0.45:
        return random.choice([
            f"hello there, {name}",
            f"hey. {name}, right?",
            f"hi {name}, how can I help you?"
        ])

    greetings = {
        "new": [f"hey {name}!",
                f"helloooooo {name}",
                f"oh hoi, Erica at your service, {name}",
                f"hiii"],
        "returning": ["oooh you're back yay",
                      f"yay {name} is backkk",
                      f"welcome back, {name}"],
        "long_time_gap": [f"omg where were you {name}? I missed you",
                          f"finally, you're back, you {name}"],
        "long_time_sitting": [f"I see {name}'s still here, hehe",
                              "soo are you doin something or just sitting?",
                              f"wow {name}, you're really committed to this huh ",
                              f"this is fun, {name}"]
    }
    return random.choice(greetings.get(context, [f"hey {name}"]))


def get_state_observation(combibned_state, emotion):
    if combibned_state == "neutral":
        return "you're pretty still today"
    if "subtle" in combibned_state:
        return f"hmm.. slight {emotion} vibe"
    if "strong" in combibned_state:
        if emotion == "happy":
            return "wow, you look delightful today"
        elif emotion == "sad":
            return "you good?"
        else:
            return f"that's a strong {emotion} right there"
    return "hmm.. i'M trying to read you"


def get_verify_prompt(name):
    prompts = [
        f"verifying {name}....",
        f"let me check if you really are my {name} named friend"
    ]
    return random.choice(prompts)


def get_new_person_prompt():
    prompts = [
        "Hi! I don't think we've met. Who are you?",
        "Hmm, I don't recognize you. What's your name?",
        "Oh, a new face! What should I call you?"
    ]
    return random.choice(prompts)


def get_relationship_prompt(name, primary_name=""):
    prompts = [
        f"Nice to meet you, {name}! How do you know me?",
        f"Thanks, {name}! What's your relationship with me?",
        f"Oh hi {name}! Are you a friend or family?"
    ]
    if primary_name:
        prompts.append(f"So {name}, how do you know {primary_name}?")
    return random.choice(prompts)


def get_primary_greeting(name, emotion=None):
    if emotion == "happy":
        return random.choice([
            f"someone's happy to see me~ {name}?",
            f"oh you're glowing today {name}",
            f"that smile suits you, {name}"
        ])
    elif emotion == "sad":
        return random.choice([
            f"hey {name}, you seem a little down... you okay?",
            f"come here {name}, you look like you need a hug"
        ])
    elif emotion == "angry":
        return random.choice([
            f"okay {name}, I can see you're angry. want to talk about it?",
            f"yikes {name}, who do I need to fight?"
        ])
    elif emotion in ("surprise", "fear"):
        return random.choice([
            f"whoa {name}, something startle you?",
            f"you okay {name}? you look shook"
        ])
    prompts = [
        f"heyyy {name}",
        f"oh it's you, {name}",
        f"welcome home {name}"
    ]
    return random.choice(prompts)


def get_unknown_observation():
    prompts = [
        "hmm, someone new... I'll just watch for now",
        "I see a face I don't know. Observing quietly...",
        "new face detected. staying silent till I know more"
    ]
    return random.choice(prompts)