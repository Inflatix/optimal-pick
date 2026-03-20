import sqlite3

DB_NAME = 'league_optimizer.db'

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON") # for CASCADE
    return conn

def init_db():
    """Initialisiert die Datenbank und erstellt alle Tabellen und Trigger."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript('''
        -- Stammdaten der Champions
        CREATE TABLE IF NOT EXISTS Champions (
            champ_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );

        -- Rollen pro Champion (aus deinen JSON-Daten)
        CREATE TABLE IF NOT EXISTS Champion_roles (
            champ_id INTEGER,
            role TEXT,
            last_update DATETIME DEFAULT CURRENT_TIMESTAMP, 
            PRIMARY KEY (champ_id, role),
            FOREIGN KEY (champ_id) REFERENCES Champions(champ_id)
        );

        -- Matchup-Daten (Counter)
        CREATE TABLE IF NOT EXISTS Matchups (
            champ1_id INTEGER,
            role1 TEXT,
            champ2_id INTEGER,
            role2 TEXT,
            winrate REAL,
            games INTEGER,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            delta REAL,
            PRIMARY KEY (champion1_id, role1, champion2_id, role2),
            FOREIGN KEY (champion1_id, role1) REFERENCES Champion_roles(champ_id, role) ON DELETE CASCADE,
            FOREIGN KEY (champion2_id, role2) REFERENCES Champion_roles(champ_id, role) ON DELETE CASCADE
        );

        -- Synergie-Daten (Team-Kombinationen)
        CREATE TABLE IF NOT EXISTS Synergies (
            champ1_id INTEGER,
            role1 TEXT,
            champ2_id INTEGER,
            role2 TEXT,
            winrate REAL,
            games INTEGER,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            delta REAL,
            PRIMARY KEY (champ1_id, role1, champ2_id, role2),
            FOREIGN KEY (champ1_id, role1) REFERENCES Champion_roles(champ_id, role) ON DELETE CASCADE ,
            FOREIGN KEY (champ2_id, role2) REFERENCES Champion_roles(champ_id, role) ON DELETE CASCADE
        );
    ''')

    cursor.executescript('''
        -- Trigger für Matchups
        CREATE TRIGGER IF NOT EXISTS tr_update_matchups_timestamp 
        AFTER UPDATE ON Matchups
        BEGIN
            UPDATE Matchups SET last_updated = CURRENT_TIMESTAMP 
            WHERE champ1_id = OLD.champ1_id AND role1 = OLD.role1 
              AND champ2_id = OLD.champ2_id AND role2 = OLD.role2;
        END;

        -- Trigger für Synergies
        CREATE TRIGGER IF NOT EXISTS tr_update_synergies_timestamp 
        AFTER UPDATE ON Synergies
        BEGIN
            UPDATE Synergies SET last_updated = CURRENT_TIMESTAMP 
            WHERE champ1_id = OLD.champ1_id AND role1 = OLD.role1 
              AND champ2_id = OLD.champ2_id AND role2 = OLD.role2;
        END;
    ''')

    conn.commit()
    conn.close()
    print("Datenbank erfolgreich initialisiert.")

def save_champion_data(champ_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT OR REPLACE INTO Champions (champ_id, name) VALUES (?, ?)", (champ_id, name))
    
    conn.commit()
    conn.close()

def save_matchup(input_list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT OR REPLACE INTO Matchups (champ1_id, role1, champ2_id, role2, winrate, games, delta)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (input_list))
    conn.commit()
    conn.close()


def save_synergy(input_list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT OR REPLACE INTO Synergies (champ1_id, role1, champ2_id, role2, winrate, games, delta)
        VALUES (?, ?, ?, ?, ?, ?. ?)
    ''', (input_list))
    conn.commit()
    conn.close()

def get_champs_to_update_role():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
            SELECT c.name
            FROM Champions c LEFT JOIN Champion_roles r ON c.champ_id = r.champ_id 
            AND r.last_update > datetime('now', '-14 days')
            WHERE r.champ_id IS NULL 
            """)
    res = cursor.fetchall()
    conn.close()
    return [row[0] for row in res]

def get_champ_main_roles(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT r.role 
                   FROM Champions c JOIN Champion_roles r ON c.champ_id = r.champ_id
                   WHERE c.name = ?
                   """ , (name,) )
    res = cursor.fetchall()
    conn.close()
    return [row[0] for row in res]


def keep_main_roles(role_and_name_list):
    if not role_and_name_list: return 
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("""
                   UPDATE Champion_roles
                   SET last_update = datetime("now")
                   WHERE role = ? AND champ_id = (SELECT champ_id FROM Champions WHERE name = ?)
                   """, role_and_name_list)
    conn.commit()
    conn.close()

def add_main_roles(role_and_name_list):
    if not role_and_name_list: return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("""
                   INSERT INTO Champion_roles (champ_id, role, last_update)
                   SELECT champ_id, ?, datetime("now")
                   FROM Champions
                   WHERE name = ?
                   """, role_and_name_list)
    conn.commit()
    conn.close()
    
def remove_main_roles(role_and_name_list):
    if not role_and_name_list: return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(""" 
                   DELETE FROM Champion_roles
                   WHERE role = ? AND champ_id = (SELECT champ_id FROM Champions WHERE name = ?)
                   """, role_and_name_list)
    conn.commit()
    conn.close()

def get_synergies_to_update():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT c.name,r.role, c.champ_id
                   FROM Champion_roles r LEFT JOIN Champions c ON r.champ_id = c.champ_id LEFT JOIN Synergies s ON c.champ_id = s.champ1_id
                   AND r.role = s.role1 AND s.last_updated > datetime('now', '-14 days')
                   WHERE s.champ1_id IS NULL 
                   """)
    res = cursor.fetchall()
    conn.close()
    return res

def get_all_champ_main_roles():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT c.champ_id, r.role, c.name
                   FROM Champion_roles r JOIN Champions c ON c.champ_id = r.champ_id
                   """)
    res = cursor.fetchall()
    conn.close()
    return res

def get_matchups_to_update():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT c.name,r.role, c.champ_id
                   FROM Champion_roles r LEFT JOIN Champions c ON r.champ_id = c.champ_id LEFT JOIN Matchups m ON c.champ_id = m.champ1_id
                   AND r.role = m.role1 AND m.last_updated > datetime('now', '-14 days')
                   WHERE m.champ1_id IS NULL 
                   """)
    res = cursor.fetchall()
    conn.close()
    return res


def get_all_champ_names():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(""" 
                   SELECT name 
                   FROM Champions 
                   """)
    res = cursor.fetchall()
    conn.close()
    return [row[0] for row in res]


def get_synergie_wr(myrole, team_champs_and_role):
    if not team_champs_and_role:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    pair_placeholders = ", ".join(["(?, ?)"] * len(team_champs_and_role))

    flattened_team = []
    for name, role in team_champs_and_role:
        flattened_team.extend([name, role])

    cursor.execute(f"""
                    SELECT c1.name,c1.champ_id,s.winrate,s.role2
                    FROM Champions c1 
                    JOIN Synergies s ON c1.champ_id = s.champ1_id 
                    JOIN Champions c2 ON c2.champ_id = s.champ2_id
                    WHERE s.role1 = ? AND (c2.name, s.role2) IN ({pair_placeholders}) 
                       """, [myrole] + flattened_team)
    res = cursor.fetchall()
    conn.close()
    return res

def get_matchup_wr(myrole, enemy_champs_and_role):
    if not enemy_champs_and_role:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    pair_placeholders = ", ".join(["(?, ?)"] * len(enemy_champs_and_role))

    flattened_team = []
    for name, role in enemy_champs_and_role:
        flattened_team.extend([name, role])

    cursor.execute(f"""
                    SELECT c1.name,c1.champ_id,m.winrate,m.role2
                    FROM Champions c1 
                    JOIN Matchups m ON c1.champ_id = m.champ1_id 
                    JOIN Champions c2 ON c2.champ_id = m.champ2_id
                    WHERE m.role1 = ? AND (c2.name, m.role2) IN ({pair_placeholders}) 
                       """, [myrole] + flattened_team)
    res = cursor.fetchall()
    conn.close()
    return res