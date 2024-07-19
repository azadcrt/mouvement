# Installation

L'utilisation de Xbee studio ou xctu pour l'initialisation de nouvelle XBee 
Il faut avoir le droit de lire le port USB (sur linux notament). 
Les fichiers mpy sont compiler grace à mpy-cross.
Pour un emetteur il faut un fichier main.py et un fichier em.mpy pour le faire fonctioner.
Le puits n'a besoin que d'un fichier main.py. 
Le boutton user des board groove permette d'enregistrer les logs dans un fichier à récuperer sur l'xbee ( attention un fichier à la fois).


positionnement des capteurs pour que les axes blender et des capteur se supperpose.
![image](https://github.com/user-attachments/assets/14cea68e-f260-4589-b85d-9a66b9c3fc7f)


## Bug connu 
Sur batterie les messages ne se retransmette pas (Sûrement dû à un paramètre qui change quand sur batterie)
PC peu puissant si on quitte blender la fenetre peut bloquer car un thread se ferme mal.
Au lancement des emetteurs des messages non transmit apparraisse entre 0-4 ce qui peut sur les courte durée influencer les logs.





# mouvement
## étalonnage
Scripts de récuperation des données du puits et de transmition à blender 
- IMPORTANT: lancer le script blender avant et choisir le bon port_name

## Internet et madgwick 
Script madgwick soit adapter du net soit fait par moi.
- Sert surtout de fichier "de base" 

## Modif
Code des XBEE TRX avec lecture des données d'interet
- Sert surtout de fichier "Stable" 

## Récepteur 
Code de la XBEE puit.
-parse et retransmet les données au pc

## Final.blend
Projet blender contenant un modele humain lie a un squelette (rigging) ainsi que deux script (api pour lire les quaternions et reset pour reset la scene blender)
- IMPORTANT: il faut avoir le squelette de séléctioné pour lancer les script (plus facilement visible en wireframe)

## En cours
Nouvelle fonctionnalité pas encore complètement sûre

## node.xpro
Fichier de configuration de base des XBEE pour xbee studio ou xtcu 
- Bien penser à renommer les modules
