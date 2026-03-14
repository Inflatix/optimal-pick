from collections import defaultdict
import json

from flask import Flask, request, jsonify
from flask_cors import CORS
import calculations 
import get_data
import database


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/get-recommendation', methods=['POST', 'OPTIONS'])
def get_recommendation():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    try: 
        data = request.json

        raw_team = data.get("team_picks", {})
        raw_enemy = data.get("enemy_picks", {})

        my_role = data.get("role")
        print(my_role)
        team_list = [(get_data.get_database_name(champ), role) for role, champ in raw_team.items() if champ]
        enemy_list = [(get_data.get_database_name(champ), role) for role, champ in raw_enemy.items() if champ]
    
        best_picks = calculations.get_best_pick(team_list, enemy_list, my_role)

    
        return jsonify({
            "status": "success",
            "recommendations": {champ: wr for champ, wr in best_picks}
        })
    
    except Exception as e: 
        print(f"ERROR: {e}") # Damit du im Terminal siehst, was schiefläuft!
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/get-champ-roles', methods=['GET'])
def get_champ_roles():
    try: 
        raw_champ_main_roles = database.get_all_champ_main_roles()
        champ_main_roles = defaultdict(list)
        for champ_id, role, champ_name in raw_champ_main_roles:
            champ_main_roles[champ_name].append(role)

        return json.dumps(champ_main_roles)

    except Exception as e: 
        print(f"Error {e}")

if __name__ == '__main__':
    print("Starte League Draft Backend auf http://localhost:5000 ...")
    app.run(debug=True, port=5000)