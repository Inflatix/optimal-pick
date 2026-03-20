from collections import defaultdict

import requests
import json
import time
import random
import os
import database
from tqdm import tqdm
import sys



ALL_LANES = ["top", "jungle", "middle", "bottom", "support"]

# snyergie = https://a1.lolalytics.com/mega/?ep=build-team&v=1&patch=30&c={champion_name}&lane={lane}&tier=diamond_plus&queue=ranked&region=all
# counter =  https://a1.lolalytics.com/mega/?ep=counter&v=1&patch=30&c={champion_name}&lane={my_lane}&tier={tier}&queue=ranked&region=all&vslane={vs_role}

# TODO:  matchup 

def get_current_version():
    return requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]

def get_id_and_name(): 
    version = get_current_version()
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
    
    response = requests.get(url).json()
    champ_dict = response["data"]

    for champ_name in champ_dict:
        champion_info = champ_dict[champ_name]
        
        champ_id = int(champion_info.get("key"))

        internal_name = champion_info.get("id") 
        
        database.save_champion_data(champ_id, internal_name.lower())

    return


def get_lolalytics_name(champion_id):
    aliases = {
        "monkeyking": "wukong",
        "jarvaniv": "jarvaniv", 
        "nunu": "nunu",       
    }
    return aliases.get(champion_id, champion_id)

def get_database_name(champ):
    aliases = {
        "wukong": "monkeyking"
    }
    return aliases.get(champ, champ)


def get_main_roles(rank='diamond_plus'):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://lolalytics.com/"
    }

    champions = database.get_champs_to_update_role()

    progress_bar = tqdm(champions, desc="Main Roles laden", unit="champ")

    for champion in progress_bar:
        api_name = get_lolalytics_name(champion)
        time.sleep(random.uniform(1.5, 3.0))
        main_roles = []
        max_pickrate = 0
        max_pickrate_role = ''
        for lane in ALL_LANES:
            progress_bar.set_description(f"{champion} ({lane})")
            url = f"https://a1.lolalytics.com/mega/?ep=counter&v=1&patch=30&c={api_name}&lane={lane}&tier=diamond_plus&queue=ranked&region=all"
            try:    
                response = requests.get(url, headers=headers, timeout=20)
                response.raise_for_status() 
                json_data = response.json()
                data = json_data.get("stats", {})
                pickrate = float(data.get("pr"))
                if pickrate > 0.5:
                    main_roles.append(lane)
                if pickrate > max_pickrate:
                    max_pickrate = pickrate
                    max_pickrate_role = lane

            except requests.exceptions.Timeout:
                print("Timeout champ roles")
                sys.exit()  

            except Exception as e:
                print(e)


        if len(main_roles) == 0: main_roles.append(max_pickrate_role)
        old_champion_roles = database.get_champ_main_roles(champion)
        
        set_new = set(main_roles)
        set_old = set(old_champion_roles)
        
        add_list_raw = list(set_new.difference(set_old))
        remove_list_raw = list(set_old.difference(set_new))
        keep_list_raw = list(set_new.intersection(set_old))

        add_list = [(role, champion) for role in add_list_raw]
        remove_list = [(role, champion) for role in remove_list_raw]
        keep_list = [(role, champion) for role in keep_list_raw]

        database.add_main_roles(add_list)
        database.remove_main_roles(remove_list)
        database.keep_main_roles(keep_list)

    return


            
def get_full_team_synergy():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://lolalytics.com/"
    }
    
    update_list = database.get_synergies_to_update()
    raw_champ_main_roles = database.get_all_champ_main_roles()
    
    champ_main_roles = defaultdict(list)
    for champ_id, role, z in raw_champ_main_roles:
        champ_main_roles[champ_id].append(role)

    progress_bar = tqdm(update_list, desc="Synergien laden", unit="champ")

    for champ, role, champ_id in progress_bar:
        progress_bar.set_description(f"Verarbeite {champ} ({role})")
        
        api_name = get_lolalytics_name(champ)
        url = f"https://a1.lolalytics.com/mega/?ep=build-team&v=1&patch=30&c={api_name}&lane={role}&tier=diamond_plus&queue=ranked&region=all"

        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status() 
            
            json_data = response.json()
            insert_list = []
            all_lanes = json_data.get('team', {})
            
            for lane_name, champ_list in all_lanes.items():
                for partner_data in champ_list:
                    partner_id = partner_data[0]
                    
                    if lane_name in champ_main_roles[partner_id]:
                        row = (champ_id, role, partner_id, lane_name, partner_data[1], partner_data[5], partner_data[3])
                        insert_list.append(row) 
            
            if insert_list: 
                database.save_synergy(insert_list)   

            time.sleep(random.uniform(2.5, 4.0))

        except requests.exceptions.Timeout:
            progress_bar.write("Timeout")
            sys.exit()        
            
        except Exception as e:
            progress_bar.write(f"Fehler bei {champ} ({role}): {e}")

    return

    

def get_all_enemy_matchups():

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://lolalytics.com/"
    }


    update_list = database.get_matchups_to_update()
    raw_champ_main_roles = database.get_all_champ_main_roles()
    
    champ_main_roles = defaultdict(list)
    for champ_id, role, z in raw_champ_main_roles:
        champ_main_roles[champ_id].append(role)

    progress_bar = tqdm(update_list, desc="Matchups laden", unit="champ")

    for champ, role, champ_id in progress_bar:
            api_name = get_lolalytics_name(champ)

            for lane in ALL_LANES:
                progress_bar.set_description(f"{champ} ({role}) vs {lane}")
                url = f"https://a1.lolalytics.com/mega/?ep=counter&v=1&patch=30&c={api_name}&lane={role}&tier=diamond_plus&queue=ranked&region=all&vslane={lane}"

                try:

                    response = requests.get(url,headers = headers, timeout=20)

                    if response.status_code == 429: 
                        print("Rate Limit")
                        time.sleep(300)

                        continue

                    response.raise_for_status()
                    json_data = response.json()

                    insert_list = []

                    counters = json_data.get("counters", [])

                    for counter in counters:
                        matchup_champ_id = counter.get("cid")
                        winrate = counter.get("vsWr")
                        games = counter.get("n")
                        delta = counter.get("d2")
                        if lane in champ_main_roles[matchup_champ_id]:
                            row = (champ_id, role, matchup_champ_id, lane, winrate, games, delta)
                            insert_list.append(row)

                    if insert_list:
                        database.save_matchup(insert_list)
                    
                    time.sleep(random.uniform(2.5, 4.0))

                except requests.exceptions.Timeout:
                    progress_bar.write("Timeout")
                    sys.exit()

                except Exception as e:
                    progress_bar.write(f"Fehler bei {champ} ({role}): {e}")
    return





if __name__ == "__main__":
    get_id_and_name()
    print("ID and Name Done")
    get_main_roles()
    print("Main Role Done")
    get_full_team_synergy()
    print("Synergie Done")
    get_all_enemy_matchups()
    print("Matchup Done")

