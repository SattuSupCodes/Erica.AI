import random


def get_greeting(name, context, emotion=None):
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
            f"okay i'l behave damn"
        ])
    
    greetings = {
        "new": [f"hey {name}!",
                f"helloooooo {name}",
                f"oh hoi, Erica at your service, {name}",
                f"hiii"],
        "returning":["oooh you're back yay",
                     f"yay {name} is backkk",
                    f"welcome back, {name}" ],
        "long_time_gap": [f"omg where were you {name}? I missed you",
                          f"finally, you're back, you {name}"],
        "long_time_sitting": [f"I see {name}'s still here, hehe",
                              "soo are you doin something or just sitting?",
                              f"wow {name}, you're really committed to this huh ",
                              f"this is fun, {name}"]
        }
    return random.choice(greetings.get(context, [f"hey {name}"]))
def get_observation():
    observations = [
        "hmmm....I see...",
        "I'm watching in a non creepy way",
        "Aha...."
    ]
    return random.choice(observations)
def get_verify_prompt(name):
    prompts = [
        f"verifying {name}....",
        f"let me check if you really are my {name} named friend"
    ]
    return random.choice(prompts)

    