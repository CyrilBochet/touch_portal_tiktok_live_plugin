import json
import sys

def validate_touchportal_config(config_file):
    """Valide un fichier de configuration TouchPortal"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✓ JSON valide: {config_file}")
        
        # Vérifications de base
        required_fields = ["sdk", "version", "name", "id", "plugin_start_cmd", "categories"]
        for field in required_fields:
            if field not in config:
                print(f"✗ Champ manquant: {field}")
                return False
            else:
                print(f"✓ Champ présent: {field}")
        
        # Vérifier les événements
        print("\nVérification des événements:")
        for category in config.get("categories", []):
            for event in category.get("events", []):
                event_id = event.get("id", "unknown")
                if "valueStateId" not in event:
                    print(f"✗ Événement {event_id}: manque valueStateId")
                    return False
                else:
                    print(f"✓ Événement {event_id}: valueStateId présent")
        
        # Vérifier les états
        print("\nVérification des états:")
        for category in config.get("categories", []):
            for state in category.get("states", []):
                state_id = state.get("id", "unknown")
                required_state_fields = ["id", "type", "desc", "default"]
                for field in required_state_fields:
                    if field not in state:
                        print(f"✗ État {state_id}: manque {field}")
                        return False
                print(f"✓ État {state_id}: tous les champs présents")
        
        # Vérifier les actions
        print("\nVérification des actions:")
        for category in config.get("categories", []):
            for action in category.get("actions", []):
                action_id = action.get("id", "unknown")
                required_action_fields = ["id", "name", "type", "description"]
                for field in required_action_fields:
                    if field not in action:
                        print(f"✗ Action {action_id}: manque {field}")
                        return False
                print(f"✓ Action {action_id}: tous les champs présents")
        
        print(f"\n✓ Configuration valide!")
        return True
        
    except json.JSONDecodeError as e:
        print(f"✗ Erreur JSON: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ Fichier non trouvé: {config_file}")
        return False
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False

def main():
    config_files = ["entry.tp", "build/TikTokLivePlugin/entry.tp", "build/TikTokLivePlugin/plugin.json"]
    
    print("Validation des fichiers de configuration TouchPortal")
    print("=" * 50)
    
    for config_file in config_files:
        print(f"\nValidation de: {config_file}")
        print("-" * 30)
        if validate_touchportal_config(config_file):
            print("✓ VALIDÉ")
        else:
            print("✗ ERREURS DÉTECTÉES")
    
    print("\nTerminé!")

if __name__ == "__main__":
    main()