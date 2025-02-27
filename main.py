import os
import argparse
from api import app

def main():
    parser = argparse.ArgumentParser(description='Service d\'optimisation de trajets')
    parser.add_argument('--port', type=int, default=5000, help='Port du serveur')
    parser.add_argument('--debug', action='store_true', help='Mode debug')
    args = parser.parse_args()
    
    # Créer les dossiers nécessaires 
    os.makedirs('static', exist_ok=True)
    
    # Démarrer le serveur
    app.run(debug=args.debug, host='0.0.0.0', port=args.port)

if __name__ == "__main__":
    main() 