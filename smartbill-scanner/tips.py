def generate_tips(spending_dict):
    tips = []
    total = sum(spending_dict.values())
    if total == 0:
        return tips
    if spending_dict.get('Food', 0) / total > 0.5:
        tips.append("Reduce food delivery, cook more at home.")
    if spending_dict.get('Utility', 0) / total > 0.3:
        tips.append("Review your power usage and consider cost-effective appliances.")
    if spending_dict.get('Shopping', 0) / total > 0.4:
        tips.append("Track impulsive buys. Make a monthly limit.")
    return tips 