import random

last_used_quote = None

def get_all_quotes():
    """
    A series of funny quotes from the amazing Monty Python, the inspiration behind the Python name. :)
    """

    quotes = [
        "No one expects the Spanish Inquisition!",
        "And now for something completely different.",
        "No one expects the spammish repitition!",
        "Our experts describe you as an appallingly dull fellow, unimaginative, timid, lacking in initiative, spineless, easily dominated, no sense of humour, tedious company and irrepressibly drab and awful. And whereas in most professions these would be considerable drawbacks, in chartered accountancy they are a positive boon.",
        "It's not pining. It's passed on. This parrot is no more. It has ceased to be. It's expired and gone to meet its maker. This is a late parrot. It's a stiff. Bereft of life, it rests in peace. If you hadn't nailed it to the perch, it would be pushing up the daisies. It's rung down the curtain and joined the choir invisible. THIS IS AN EX-PARROT.",
        "It's just a flesh wound.",
        "I'm sorry to have kept you waiting, but I'm afraid my walk has become rather sillier recently."
        "Well you can't expect to wield supreme executive power just because some watery tart threw a sword at you.",
        "All right... all right... but apart from better sanitation, the medicine, education, wine, public order, irrigation, roads, a fresh water system, and public health ... what have the Romans ever done for us?",
        "Nudge, nudge, wink, wink. Know what I mean?",
        "Oh! Come and see the violence inherent in the system! Help, help! I'm being repressed!",
        "-She turned me into a newt! -A newt? -I got better..."
    ]
    
    return quotes

def get_random_quote():
    quote = random.choice(get_all_quotes())
    global last_used_quote
    # make sure we don't use the same quote twice in a row
    while last_used_quote is not None and last_used_quote == quote:
        quote = random.choice(get_all_quotes())
    last_used_quote = quote
    return quote
    
