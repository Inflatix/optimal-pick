import database
from collections import defaultdict

def get_best_pick(team_picks, enemy_picks, role, delta = False):
    print(team_picks, enemy_picks)

    if delta:
        synergie_wr = database.get_synergie_delta(role, team_picks)
        matchup_wr = database.get_matchup_delta(role, enemy_picks)
    else:
        synergie_wr = database.get_synergie_wr(role, team_picks)
        matchup_wr = database.get_matchup_wr(role, enemy_picks)

    print(len(synergie_wr))
    print(len(matchup_wr))

    winrates = defaultdict(list)

    for champ, champ_id, wr, team_role in synergie_wr: 
        winrates[champ].append((wr, f"team_{team_role}"))

    for champ, champ_id, wr, enemy_role in matchup_wr:  
        winrates[champ].append((wr, f"enemy_{enemy_role}"))


    champ_weighted_average = calculate_weighted_average(winrates, role, delta)


    sorted_champs = sorted(champ_weighted_average.items(), key=lambda item: item[1], reverse=True)
    return sorted_champs


def calculate_weighted_average(winrates, my_role, delta):
    weights = get_weights(my_role)
    champ_weighted_average_wr = {}
    for champ_name, wr_list in winrates.items(): 
        total_wr = 0
        total_weights = 0
        for wr, role_label in wr_list: 

            weight = weights.get(role_label, 1.0)

            total_wr += weight * wr
            total_weights += weight
        
        if delta: 
            champ_weighted_average_wr[champ_name] = total_wr

        elif total_weights > 0:
            champ_weighted_average_wr[champ_name] = round((total_wr / total_weights),2)
    
    return champ_weighted_average_wr

        
def get_weights(role):
    roles = ["team_top", "team_jungle", "team_middle", "team_bottom", "team_support",
             "enemy_top", "enemy_jungle", "enemy_middle", "enemy_bottom", "enemy_support"]
    
    values = []
    
    match role:
        case "top":
            values = [1.0, 1.5, 1.2, 0.7, 1.0, 2.5, 1.5, 1.2, 0.7, 1.0]
        case "jungle":
            values = [1.2, 1.0, 1.5, 1.0, 1.5, 0.8, 1.5, 1.3, 0.7, 1.3]
        case "middle":
            values = [1.2, 1.5, 1.0, 1.0, 1.3, 0.8, 1.5, 1.8, 1.0, 1.3]
        case "bottom":
            values = [0.5, 1.4, 1.3, 1.0, 2.0, 0.5, 1.4, 1.2, 1.3, 1.6]
        case "support":
            values = [0.7, 1.5, 1.2, 1.7, 1.0, 0.5, 1.2, 1.0, 1.7, 2.0]
    
    return dict(zip(roles, values))





my_role = "top"
my_team = [("sejuani", "jungle"), ("ahri", "middle")]
enemy_team = [("darius", "top"), ("leesin", "jungle")]

get_best_pick(team_picks=my_team, enemy_picks=enemy_team, role=my_role, delta=True)