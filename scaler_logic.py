# scaler_logic.py

def decide(rt, current_workers, max_workers, min_workers):
    # Scale out if slow, BUT only if we haven't hit the max limit
    if rt > 800 and current_workers < max_workers:
        return "scale_out"
        
    # Scale in if fast, BUT only if we have more than the minimum
    elif rt < 300 and current_workers > min_workers:
        return "scale_in"
        
    else:
        return "stable"