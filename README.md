# Plugin TikTok Live Monitor pour TouchPortal

Ce plugin vous permet de surveiller les streams TikTok Live en temps réel et d'utiliser les événements dans TouchPortal pour créer des interactions automatisées.

## Fonctionnalités

### Actions disponibles
- **Start TikTok Live Monitoring** : Démarre le monitoring d'un utilisateur TikTok
- **Stop TikTok Live Monitoring** : Arrête le monitoring en cours

### États disponibles
- **Monitoring Status** : Statut actuel (Stopped, Connecting, Connected, etc.)
- **Current Username** : Nom d'utilisateur actuellement surveillé
- **Current Viewers** : Nombre de viewers actuels
- **Total Likes** : Nombre total de likes reçus
- **Current Followers** : Nombre de followers actuel
- **Last Comment** : Dernier commentaire reçu
- **Last Commenter** : Nom de la personne qui a fait le dernier commentaire
- **Room ID** : ID de la salle de live

### Événements disponibles
- **TikTok Live Connected** : Quand la connexion au live est établie
- **New Comment Received** : Quand un nouveau commentaire est reçu
- **New Follower** : Quand quelqu'un suit le stream
- **Gift Received** : Quand un cadeau est reçu
- **Stream Ended** : Quand le live se termine

## Installation

### Prérequis
- Python 3.7 ou supérieur
- TouchPortal installé
- Accès internet

### Étapes d'installation

1. **Téléchargement des fichiers**
   - Téléchargez tous les fichiers du plugin
   - Placez-les dans un dossier de travail

2. **Installation des dépendances**
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

3. **Construction du plugin**
   - Exécutez le script `build.bat`
   - Cela créera un dossier `build\TikTokLivePlugin` avec tous les fichiers nécessaires

4. **Installation dans TouchPortal**
   - Copiez le dossier `build\TikTokLivePlugin` vers :
     ```
     %APPDATA%\TouchPortal\plugins\
     ```
   - Redémarrez TouchPortal

## Utilisation

### Configuration de base
1. Ouvrez TouchPortal
2. Le plugin "TikTok Live Monitor" devrait apparaître dans la liste des plugins
3. Créez une nouvelle page ou modifiez une page existante

### Surveiller un live TikTok
1. Ajoutez l'action "Start TikTok Live Monitoring"
2. Configurez le nom d'utilisateur TikTok (sans le @)
3. Le plugin commencera à surveiller le live

### Utiliser les états
Vous pouvez utiliser les états dans vos boutons TouchPortal :
- Afficher le nombre de viewers : `${tiktok.live.viewers}`
- Afficher le dernier commentaire : `${tiktok.live.last_comment}`
- Afficher le statut : `${tiktok.live.status}`

### Créer des automations
Utilisez les événements pour déclencher des actions :
- **Nouveau commentaire** → Jouer un son
- **Nouveau follower** → Afficher une alerte
- **Cadeau reçu** → Changer l'éclairage

## Exemples d'utilisation

### Affichage des statistiques en temps réel
Créez des boutons avec du texte dynamique :
```
Viewers: ${tiktok.live.viewers}
Likes: ${tiktok.live.total_likes}
Followers: ${tiktok.live.followers}
```

### Alerte sur nouveau commentaire
1. Créez un événement basé sur "New Comment Received"
2. Ajoutez une action pour :
   - Jouer un son de notification
   - Afficher le commentaire sur l'écran
   - Changer la couleur d'un bouton

### Compteur de followers
1. Utilisez l'état "Current Followers"
2. Créez un bouton qui affiche le nombre
3. Le nombre se met à jour automatiquement

## Dépannage

### Le plugin ne se connecte pas
- Vérifiez que le nom d'utilisateur est correct
- Vérifiez votre connexion internet
- Assurez-vous que l'utilisateur fait effectivement un live

### Les événements ne se déclenchent pas
- Vérifiez que le monitoring est bien actif
- Regardez les logs de TouchPortal
- Redémarrez le plugin si nécessaire

### Erreurs de permissions
- Exécutez TouchPortal en tant qu'administrateur
- Vérifiez que Python est correctement installé

## Structure des fichiers

```
TikTokLivePlugin/
├── entry.tp              # Configuration TouchPortal
├── tiktok_plugin.exe     # Exécutable principal
└── tiktok.png           # Icône du plugin
```

## Développement

Pour modifier le plugin :
1. Modifiez `tiktok_plugin.py`
2. Relancez `build.bat`
3. Remplacez les fichiers dans TouchPortal
4. Redémarrez TouchPortal

## Limitations

- Le plugin nécessite une connexion internet active
- Les limites de l'API TikTok peuvent affecter la fiabilité
- Certains comptes privés ou protégés peuvent ne pas fonctionner

## Support

Pour des problèmes ou des suggestions :
- Vérifiez les logs de TouchPortal
- Testez avec différents utilisateurs TikTok
- Assurez-vous que TikTokLive est à jour