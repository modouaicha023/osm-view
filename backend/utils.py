"""
Module de fonctions utilitaires pour le projet d'optimisation des tournées
"""
import math
import random
import json
import os


def haversine(lon1, lat1, lon2, lat2):
    """
    Calcule la distance en km entre deux points géographiques
    en utilisant la formule de Haversine

    Args:
        lon1, lat1: Coordonnées du premier point (degrés)
        lon2, lat2: Coordonnées du deuxième point (degrés)

    Returns:
        float: Distance en kilomètres
    """
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371 

    return c * r


def format_time(minutes):
    """
    Convertit des minutes en format HH:MM

    Args:
        minutes: Nombre de minutes depuis minuit

    Returns:
        str: Heure au format HH:MM
    """
    hours, mins = divmod(minutes, 60)
    return f"{int(hours):02d}:{int(mins):02d}"


def parse_time(time_str):
    """
    Convertit une heure au format HH:MM en minutes depuis minuit

    Args:
        time_str: Heure au format HH:MM

    Returns:
        int: Minutes depuis minuit
    """
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes


def generate_random_time(start_time, end_time):
    """
    Génère une heure aléatoire entre deux heures

    Args:
        start_time: Heure de début au format HH:MM
        end_time: Heure de fin au format HH:MM

    Returns:
        str: Heure aléatoire au format HH:MM
    """
    start_minutes = parse_time(start_time)
    end_minutes = parse_time(end_time)

    random_minutes = random.randint(start_minutes, end_minutes)
    return format_time(random_minutes)


def save_json(data, filename):
    """
    Sauvegarde des données au format JSON

    Args:
        data: Données à sauvegarder
        filename: Nom du fichier
    """
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_json(filename):
    """
    Charge des données depuis un fichier JSON

    Args:
        filename: Nom du fichier

    Returns:
        dict: Données chargées
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement du fichier JSON: {e}")
        return {}
