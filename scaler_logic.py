def decide(rt):
    if rt > 800:
        return "scale_out"
    elif rt < 300:
        return "scale_in"
    else:
        return "stable"

