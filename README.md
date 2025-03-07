# Installation

- **Outils nécessaires** :  
  - [XBee Studio](https://www.digi.com/resources/documentation/digidocs/90002385/) ou [XCTU](https://www.digi.com/resources/documentation/digidocs/90001526/) pour l'initialisation des nouveaux modules XBee.  
  - Sur Linux, assurez-vous d'avoir les droits de lecture sur le port USB.  

- **Compilation des fichiers** :  
  - Les fichiers `.mpy` sont compilés à l'aide de `mpy-cross`.  

- **Configuration des fichiers** :  
  - Un **émetteur** nécessite un `main.py` et un `em.mpy` pour fonctionner.  
  - Le **puits** n'a besoin que d'un `main.py`.  

- **Enregistrement des logs** :  
  - Le bouton **USER** des cartes Grove permet d'enregistrer les logs dans un fichier.  
  - ⚠️ **Attention** : un seul fichier de log peut être enregistré à la fois sur l'XBee.  

![Diagramme](https://github.com/user-attachments/assets/14cea68e-f260-4589-b85d-9a66b9c3fc7f)  

---

# 802.15.4  
Contient une version basique du projet, mettant en œuvre la communication entre les modules XBee via le protocole **802.15.4**.  

# Maryline  
Ce dossier intègre des adaptations et améliorations basées sur les retours des premiers utilisateurs.  

# reconnaitre.zip  
Archive contenant le projet **Android Studio** lié au projet.
