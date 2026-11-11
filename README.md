# Cul de Chouette, Maître du Jeu

Assistant de Maître du Jeu pour le Cul de Chouette, le jeu de dés popularisé par la série Kaamelott. Le programme tient le tableau des scores, annonce les combinaisons, indique aux joueurs ce qu'ils doivent faire (sirotage, cris, civet, grelottine) et applique les points selon les règles choisies avant la partie.

Il existe en deux versions qui partagent le même moteur de règles : une interface graphique Tkinter et un mode console.

## Table des matières

- [Présentation](#présentation)
- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Lancement](#lancement)
- [Utilisation](#utilisation)
- [Options de partie](#options-de-partie)
- [Règles implémentées](#règles-implémentées)
- [Règles non gérées](#règles-non-gérées)
- [Choix d'interprétation](#choix-dinterprétation)
- [Configuration](#configuration)
- [Architecture du code](#architecture-du-code)
- [Dépannage](#dépannage)
- [Crédits et licence](#crédits-et-licence)

## Présentation

Les dés se lancent à la main, sur la table. Une personne joue le rôle de Maître du Jeu. Elle saisit les valeurs des dés dans le programme, puis indique qui a crié en premier, qui est arrivé dernier sur une Suite ou qui a parié quoi au sirotage. Le programme calcule les points, tient le journal de la partie et affiche le classement après chaque tour.

Le jeu se joue de 2 à 16 joueurs. Dans le mode standard, le premier joueur qui atteint ou dépasse 343 points remporte la partie.

## Fonctionnalités

- Interface graphique avec tableau des scores, journal coloré et fenêtres de saisie adaptées à chaque situation.
- Mode console complet, qui utilise le même moteur.
- Trois niveaux de règles, du jeu historique à la version complète.
- Option pour autoriser ou interdire les scores négatifs.
- Mode Règles à l'Aquitaine, où le score est converti en gorgées.
- Saisie des dés en deux temps (chouettes puis cul), ce qui permet de gérer l'Achat et le Verdier.
- Annulation du dernier tour ou de la dernière bévue.
- Bouton Règles avec sommaire cliquable.
- Inscription d'un joueur en cours de partie avec le Chante-Sloubi.
- Export du tableau des scores en image PNG.
- Contrôle automatique de Pillow, avec proposition d'installation si le module manque.

## Prérequis

| Élément | Détail |
| --- | --- |
| Python | Version 3.8 ou supérieure |
| Tkinter | Pour l'interface graphique. Inclus avec Python sur Windows et macOS. Sous Debian et Ubuntu, installer le paquet `python3-tk` |
| Pillow | Facultatif, nécessaire uniquement pour l'export PNG |

## Installation

```bash
git clone https://github.com/Vodoxiss/Cul-de-Chouette
cd <depot>
python -m pip install pillow
```

Les fichiers du projet :

| Fichier | Rôle |
| --- | --- |
| `cul_de_chouette.py` | Moteur de règles et mode console |
| `cul_de_chouette_gui.py` | Interface graphique, importe `cul_de_chouette.py` |

Les deux fichiers doivent rester dans le même dossier.

## Lancement

Interface graphique :

```bash
python cul_de_chouette_gui.py
```

Mode console :

```bash
python cul_de_chouette.py
```

Sous Linux et macOS, utiliser `python3` à la place de `python` si la commande `python` n'existe pas.

## Utilisation

### Interface graphique

1. Cliquer sur **Nouvelle partie**, ajouter au moins deux joueurs et choisir les options (voir [Options de partie](#options-de-partie)).
2. Cliquer sur le gros bouton **Saisir les chouettes de ...** pour jouer le tour du joueur indiqué.
3. Saisir les deux chouettes avec les boutons de 1 à 6, ou au clavier (deux chiffres puis Entrée). Le nom de la combinaison s'affiche dès que les trois dés sont connus.
4. Saisir le cul. Un seul clic valide ce dé. Sur cette fenêtre, le bouton **J'achète !** apparaît quand l'Achat est possible.
5. Répondre aux fenêtres suivantes. Chaque fenêtre rappelle ce que les joueurs doivent faire, puis demande qui l'a fait.
6. Le tableau et le journal se mettent à jour. Le programme signale la victoire quand un joueur atteint l'objectif.

Barre d'outils :

| Bouton | Action |
| --- | --- |
| Nouvelle partie | Choix des joueurs et des options |
| Règles | Ouvre la fenêtre des règles avec sommaire |
| Inscrire un joueur | Ajoute un joueur, avec Chante-Sloubi si la partie a commencé |
| Actions | Menu avec Bévue, Défi Grelottine et Lance-Civet |
| Annuler le dernier tour | Restaure l'état précédent |
| Exporter en PNG | Enregistre le tableau actuel sans terminer la partie |
| Terminer la partie + PNG | Affiche le classement final et enregistre l'image |

Le défi Grelottine se lance entre deux tours. Le programme le propose automatiquement après un Néant quand au moins deux joueurs possèdent une Grelottine. Le menu Actions permet de le lancer à tout autre moment.

### Mode console

Menu principal :

| Choix | Action |
| --- | --- |
| 1 | Nouvelle partie |
| 2 | Inscrire un joueur |
| 3 | Jouer ou continuer |
| 4 | Tableau des scores |
| 5 | Terminer et enregistrer le PNG |
| 6 | Bévue |
| 7 | Défi Grelottine |
| 8 | Règles du jeu |
| 9 | Exporter le tableau en PNG |
| 0 | Quitter |

À la saisie des chouettes, entrer deux chiffres (par exemple `4 4` ou `44`) ou une commande : `scores`, `annuler`, `journal`, `regles`, `menu`. À la saisie du cul, entrer un chiffre, ou `achat` quand l'Achat est possible.

## Options de partie

Les trois options se règlent au début de la partie.

| Option | Activée | Désactivée |
| --- | --- | --- |
| Scores négatifs (activée par défaut) | Un joueur qui atteint -343 est éliminé. Un défi Grelottine exige que les deux scores soient supérieurs à 0 | Le score ne descend jamais sous 0. Un joueur à zéro ne perd rien et la perte non payée est gagnée par chacun des autres joueurs. Un minimum de 30 points est demandé pour garder une Grelottine, lancer ou subir un défi ou une Soufflette. Le civet est limité au score du joueur, et les paris du Sirop et du Verdier demandent 5 points |
| Règles à l'Aquitaine | Le score est converti en gorgées et la partie s'arrête quand les joueurs le décident | Mode standard avec objectif de 343 points |
| Niveau de règles | Niveau 1, 2 ou 3 (voir ci-dessous) | Niveau 3 par défaut |

Mode Règles à l'Aquitaine :

- Pour chaque gain de points, on arrondit à la dizaine supérieure puis on divise par 10. Le joueur donne ce nombre de gorgées à qui il veut.
- Pour chaque perte, il boit ce nombre de gorgées.
- Les minimums de points disparaissent.
- Un Néant donne une Grelottine supplémentaire, avec un maximum de 6.
- Un défi Grelottine mise autant de gorgées que de Grelottines, sans Sirop-Grelot.
- La combinaison Excalibur (5-3-1) est ajoutée.
- Cette option force les scores négatifs et supprime l'objectif de 343 points.

## Règles implémentées

### Points des combinaisons

| Combinaison | Dés | Points |
| --- | --- | --- |
| Chouette | Deux dés identiques | Carré du dé (1, 4, 9, 16, 25, 36) |
| Velute | La somme de deux dés égale le troisième | 2 x carré du plus grand dé |
| Chouette-Velute | 1-1-2, 2-2-4 ou 3-3-6 | Points de la Velute, pour le premier qui crie « Pas mou, le caillou ! » |
| Cul de Chouette | Trois dés identiques | 40 + 10 x valeur du dé |
| Suite | Trois dés consécutifs | Le dernier à réagir perd 10 points |
| Néant | Aucune autre combinaison | Le lanceur gagne une Grelottine |
| Artichette (niveau 2) | 4-4-3 | 16 points pour le lanceur ou perte de 16 points |
| Soufflette (niveau 2) | 4-2-1 | Défi à trois lancers |
| Suite-Velutée (niveau 2) | 1-2-3 | Suite plus Velute de 3 (18 points) |
| Bleu-Rouge (niveau 3) | 3-3-4 | 9 points puis relance annoncée par chaque joueur |
| Néant Soufflé (niveau 3) | 1-4-6 | Le premier qui crie « Mécréant ! » prend la Grelottine |
| Excalibur (Aquitaine) | 5-3-1 | Le Roi boit autant de gorgées que d'annonceurs |

### Règles par niveau

| Niveau | Règles |
| --- | --- |
| 1 | Chouette, Velute, Chouette-Velute, Cul de Chouette, Suite, Néant, Grelottine et défi Grelottine, Sirop (sirotage et paris), Civet, Lance-Civet, Bévue, Chante-Sloubi |
| 2 | Niveau 1 plus Artichette, Soufflette, Suite-Velutée, Poulette, Passe-Grelot, Rigodon, Attrape-Oiseau, Contre-Sirop, Civet doublé, Cul de Chouette doublé, Achat et Double Achat |
| 3 | Niveau 2 plus Bleu-Rouge, Pélican, Verdier, Jarret (Mi-Jarret, Bi-Jarret, Lance-Jarret) et Néant Soufflé |

### Défi Grelottine

Un joueur qui possède une Grelottine peut défier un autre porteur de Grelottine. Le grelottin choisit la combinaison à réaliser et fixe la mise dans la limite d'une fraction du plus petit des deux scores, arrondie au supérieur.

| Combinaison défiée | Fraction maximale |
| --- | --- |
| Chouette | 1/3 |
| Velute | 1/4 |
| Cul de Chouette | 1/8 |
| Chouette-Velute | 1/16 |
| Sirop-Grelot | 1/32 |

Le défié dispose de deux lancers et s'arrête dès qu'il réussit. Il marque dans tous les cas les points de sa combinaison finale.

## Règles non gérées

- Règles de niveau 4 : Flan (avec Double-Flan, Contre-Flan et Lance-Flan), Tichette (avec Michette, Bichette et quiche), Civet-Filoché (et sa version doublée), Cul de Chouette doublé diminué.
- Jarret-Souple, Jarret-Sifflet et Charret.
- L'achat d'un sirotage.
- Les départages par cris successifs. Le Maître du Jeu arbitre et saisit le résultat final.

## Choix d'interprétation

Certains points des règles sont ambigus. Voici les choix retenus.

- Les fractions de mise de la Grelottine sont 1/3, 1/4, 1/8, 1/16 et 1/32. L'exemple de la source (42 points pour 33 % de 124) ne se vérifie qu'avec 1/3.
- Le Chante-Sloubi utilise le nombre total de tours joués dans la partie.
- À l'Aquitaine, la mise d'une Grelottine est égale au nombre de Grelottines du joueur, qui sont toutes dépensées.
- Un Néant obtenu pendant un défi Grelottine ne donne pas de Grelottine.
- Après un Achat, le sirotage n'est pas possible. Le lanceur d'origine garde les points de sa éventuelle Chouette.
- Quand un joueur à zéro devrait perdre des points, la part non payée est gagnée par chacun des autres joueurs.
- Le civet est non cumulable. Un seul civet par joueur.

## Configuration

Les constantes situées en haut de `cul_de_chouette.py` règlent les valeurs du jeu.

| Constante | Rôle | Valeur par défaut |
| --- | --- | --- |
| `OBJECTIF` | Score à atteindre | 343 |
| `CIVET_MAX` | Mise maximale d'un civet | 102 |
| `PENALITE_BEVUE` | Points perdus sur une bévue | 5 |
| `PENALITE_SUITE` | Points perdus par le dernier sur une Suite | 10 |
| `MISE_PARI` | Mise d'un pari au sirotage | 5 |
| `GAIN_PARI` | Gain d'un pari gagné | 25 |
| `PRIX_ACHAT` | Prix d'un Achat | 30 |
| `MIN_GRELOTTINE` | Score minimal sans scores négatifs | 30 |
| `ELIMINATION_NEGATIVE` | Seuil d'élimination | -343 |
| `LIMITE_SLOUBI` | Valeur maximale du Chante-Sloubi | 228 |
| `GRELOTTINES_MAX_AQUITAINE` | Grelottines maximales à l'Aquitaine | 6 |
| `DENOM_DEFI` | Dénominateurs des mises de défi | 3, 4, 8, 16, 32 |

## Architecture du code

```text
cul_de_chouette.py        Moteur de règles et mode console
cul_de_chouette_gui.py    Interface graphique Tkinter
```

Moteur (`cul_de_chouette.py`) :

- `analyser(des, niveau, aquitaine)` détermine la combinaison formée par trois dés.
- La classe `Jeu` contient l'état de la partie et toutes les règles. La méthode `tour_suivant()` déroule un tour complet.
- Les saisies passent par quatre fonctions de module : `ask_yes_no`, `ask_int`, `choisir_option` et `saisir_lancer`. La méthode `choisir_joueurs` de la classe `Jeu` joue le même rôle pour les choix de joueurs.
- `exporter_png(jeu, chemin, termine)` dessine le tableau des scores avec Pillow.
- La liste `REGLES` contient le texte affiché par le bouton Règles et la commande `regles`.

Interface (`cul_de_chouette_gui.py`) :

- Les quatre fonctions de saisie du moteur sont remplacées par des fenêtres Tkinter.
- La classe `JeuGUI` hérite de `Jeu` et redéfinit `choisir_joueurs`, `lire_chouettes`, `exporter` et `afficher_scores`.
- Les appels à `print` du moteur sont redirigés vers le journal de la fenêtre. Les derniers messages s'affichent aussi en tête de chaque fenêtre de dialogue.
- Chaque tour sauvegarde l'état de la partie, ce qui permet l'annulation.

Pour ajouter une règle, il suffit de compléter la méthode `resoudre` du moteur. L'interface graphique en bénéficie sans modification.

## Dépannage

**Le message « Pillow introuvable » s'affiche à l'export PNG**

Pillow est installé pour un autre Python que celui qui lance le programme. La fenêtre indique le chemin du Python utilisé et propose l'installation. Pour le faire à la main, utiliser le même Python que celui du lancement :

```bash
python -m pip install pillow
```

**`ModuleNotFoundError: No module named 'tkinter'`**

Installer Tkinter. Sous Debian et Ubuntu :

```bash
sudo apt install python3-tk
```

**`ModuleNotFoundError: No module named 'cul_de_chouette'`**

Les deux fichiers `.py` ne sont pas dans le même dossier. Les placer ensemble puis relancer depuis ce dossier.

**Les accents s'affichent mal dans la console Windows**

Lancer `chcp 65001` avant le programme, ou utiliser l'interface graphique.

## Crédits et licence

- Les règles sont adaptées de la page Wikilivres « Boîte à jeux/Le cul de chouette ». Le texte intégré au programme est un résumé reformulé. Les textes de Wikilivres sont publiés sous licence libre, qui demande en général de citer la source. Vérifier les conditions sur la page d'origine avant toute republication.
- Les noms des règles et les cris viennent de la série Kaamelott, créée par Alexandre Astier. Ce projet est un projet de fan, sans lien avec les auteurs ou les ayants droit de la série.
