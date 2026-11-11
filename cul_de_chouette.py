import copy
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

OBJECTIF = 343
CIVET_MAX = 102
PENALITE_BEVUE = 5
PENALITE_SUITE = 10
MISE_PARI = 5
GAIN_PARI = 25
PRIX_ACHAT = 30
MIN_GRELOTTINE = 30            
ELIMINATION_NEGATIVE = -343
LIMITE_SLOUBI = 228
GRELOTTINES_MAX_AQUITAINE = 6

DENOM_DEFI = {"chouette": 3, "velute": 4, "cul": 8, "chouette_velute": 16, "sirop": 32}

OISEAUX = {1: "Linotte", 2: "Alouette", 3: "Fauvette",
           4: "Mouette", 5: "Bergeronnette", 6: "Chouette"}
LABELS3 = ["Chouette 1", "Chouette 2", "Cul"]
LABELS2 = ["Chouette 1", "Chouette 2"]
LABELS_CUL = ["Cul"]

def ceil_div(a, b):
    return -(-a // b)

def gorgees(n):
    return f"{n} gorgée" + ("s" if n > 1 else "")

@dataclass
class Joueur:
    nom: str
    score: int = 0
    civets: int = 0            
    grelottine: int = 0        
    immunite: bool = False     
    jarret: bool = False
    elimine: bool = False
    gorgees_donnees: int = 0
    gorgees_bues: int = 0

@dataclass
class Combo:
    kind: str
    valeur: int
    points: int
    suite: bool = False

    def matches(self, k):
        if self.kind == k:
            return True
        if k == "suite" and self.suite:
            return True
        if self.kind == "suite_velutee" and k in ("velute", "suite"):
            return True
        return False

    def libelle(self):
        k, v = self.kind, self.valeur
        if k == "cul":
            return f"Cul de Chouette de {v}"
        if k == "chouette":
            return f"Chouette de {v}"
        if k == "velute":
            return f"Velute de {v}" + (" (et Suite)" if self.suite else "")
        if k == "chouette_velute":
            return f"Chouette-Velute (Chouette de {v // 2}, Velute de {v})"
        return {"suite": "Suite", "suite_velutee": "Suite-Velutée", "artichette": "Artichette",
                "soufflette": "Soufflette", "bleu_rouge": "Bleu-Rouge",
                "neant_souffle": "Néant Soufflé", "excalibur": "Excalibur",
                "neant": "Néant"}[k]

def analyser(des, niveau=3, aquitaine=False):
    s = tuple(sorted(des))
    a, b, c = s
    if niveau >= 3 and s == (3, 3, 4):
        return Combo("bleu_rouge", 3, 9)
    if niveau >= 2 and s == (3, 4, 4):
        return Combo("artichette", 4, 0)
    if niveau >= 2 and s == (1, 2, 4):
        return Combo("soufflette", 4, 0)
    if niveau >= 2 and s == (1, 2, 3):
        return Combo("suite_velutee", 3, 18, suite=True)
    if niveau >= 3 and s == (1, 4, 6):
        return Combo("neant_souffle", 0, 0)
    if aquitaine and s == (1, 3, 5):
        return Combo("excalibur", 0, 0)
    distincts = len(set(s))
    if distincts == 1:
        return Combo("cul", a, 40 + 10 * a)
    velute = (a + b == c)
    if distincts == 2:
        if velute:
            return Combo("chouette_velute", c, 2 * c * c)
        p = a if a == b else b
        return Combo("chouette", p, p * p)
    suite = (b == a + 1 and c == b + 1)
    if velute:
        return Combo("velute", c, 2 * c * c, suite=suite)
    if suite:
        return Combo("suite", c, 0, suite=True)
    return Combo("neant", 0, 0)

class RetourMenu(Exception):
    pass


class Recommencer(Exception):
    pass


def saisir(invite):
    try:
        return input(invite).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nÀ bientôt !")
        sys.exit(0)


def ask_yes_no(question):
    while True:
        r = saisir(f"{question} (o/n) ").lower()
        if r in ("o", "oui", "y", "yes"):
            return True
        if r in ("n", "non"):
            return False
        print("   Réponds par o ou n.")


def ask_int(question, lo, hi, vide_ok=False):
    while True:
        r = saisir(f"{question} ")
        if r == "" and vide_ok:
            return None
        if r.lstrip("-").isdigit() and lo <= int(r) <= hi:
            return int(r)
        print(f"   Entre un nombre entre {lo} et {hi}.")


def parse_des(s, n=3):
    s = re.sub(r"[\s,;\-/.]+", "", s)
    if len(s) == n and all(ch in "123456" for ch in s):
        return [int(ch) for ch in s]
    return None


def saisir_lancer(invite, labels, extras=()):
    n = len(labels)
    while True:
        r = saisir(f"{invite} " + (f"[ou : {', '.join(c for c, _ in extras)}] " if extras else "")
                   ).lower()
        for code, _ in extras:
            if r == code:
                return code
        d = parse_des(r, n)
        if d:
            return d
        print(f"   Saisie invalide : {n} dé(s) de 1 à 6 (ex : {'3 4 6'[:2 * n - 1]}).")


def choisir_option(titre, options):
    print(titre)
    for i, (_, label) in enumerate(options, 1):
        print(f"     {i}) {label}")
    n = ask_int("   Choix :", 1, len(options))
    return options[n - 1][0]

def _police(taille, gras=False):
    from PIL import ImageFont
    candidats = (["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "Helvetica.ttc"]
                 if gras else ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "Helvetica.ttc"])
    for nom in candidats:
        try:
            return ImageFont.truetype(nom, taille)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=taille)
    except TypeError:
        return ImageFont.load_default()


def _ecrire(d, xy, texte, police, couleur, ancrage="lm"):
    try:
        d.text(xy, texte, font=police, fill=couleur, anchor=ancrage)
    except ValueError:
        d.text(xy, texte, font=police, fill=couleur)


def classer(joueurs):
    tri = sorted(joueurs, key=lambda j: (j.elimine, -j.score))
    res, prec, rang = [], None, 0
    for i, j in enumerate(tri):
        if (j.score, j.elimine) != prec:
            rang, prec = i + 1, (j.score, j.elimine)
        res.append((rang, j))
    return res


def objets(j):
    o = []
    if j.elimine:
        o.append("ÉLIMINÉ")
    if j.civets:
        o.append("Civet")
    if j.grelottine:
        o.append("Grelottine" + (f" x{j.grelottine}" if j.grelottine > 1 else ""))
    if j.immunite:
        o.append("Immunité")
    if j.jarret:
        o.append("Jarret")
    return " · ".join(o) if o else "-"


def exporter_png(jeu, chemin, termine=True):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("   Pillow n'est pas installé : lance  pip install pillow  puis recommence.")
        return None

    classement = classer(jeu.joueurs)
    n = len(classement)
    aq = jeu.aquitaine
    W, h_titre, h_ent, h_ligne, h_pied = 960, 150, 56, 62, 60
    H = h_titre + h_ent + h_ligne * n + h_pied
    img = Image.new("RGB", (W, H), "#FBF5E6")
    d = ImageDraw.Draw(img)
    f_titre, f_sous = _police(42, True), _police(19)
    f_ent, f_txt, f_score = _police(22, True), _police(26), _police(32, True)
    f_petit = _police(20)

    d.rectangle([0, 0, W, h_titre], fill="#5B3A1E")
    _ecrire(d, (W // 2, 46), "CUL DE CHOUETTE", f_titre, "#FBF5E6", "mm")
    sous = ("Tableau des scores final" if termine else "Tableau des scores provisoire")
    _ecrire(d, (W // 2, 92), f"{sous}  -  {datetime.now():%d/%m/%Y %H:%M}", f_sous, "#E8D5B0", "mm")
    opts = ("Règles à l'Aquitaine" if aq else f"Objectif {OBJECTIF} pts")
    opts += f"  -  règles {'★' * jeu.niveau}"
    opts += "  -  scores négatifs " + ("autorisés" if jeu.negatifs else "interdits") if not aq else ""
    _ecrire(d, (W // 2, 124), opts, f_sous, "#E8D5B0", "mm")

    if aq:
        cols = [("rang", "#", 55, "mm"), ("nom", "Joueur", 100, "lm"), ("score", "Score", 450, "mm"),
                ("don", "Données", 575, "mm"), ("bue", "Bues", 690, "mm"), ("obj", "Objets", 830, "mm")]
    else:
        cols = [("rang", "#", 55, "mm"), ("nom", "Joueur", 100, "lm"), ("score", "Score", 500, "mm"),
                ("obj", "Objets", 740, "mm")]
    y = h_titre
    d.rectangle([0, y, W, y + h_ent], fill="#8B5E34")
    for cle, titre, x, anc in cols:
        _ecrire(d, (x, y + h_ent // 2), titre, f_ent, "white", anc)
    y += h_ent
    for i, (rang, j) in enumerate(classement):
        gagnant = termine and not aq and jeu.gagnant is j
        fond = "#F4D03F" if gagnant else ("#F3E8CF" if i % 2 == 0 else "#FBF5E6")
        d.rectangle([0, y, W, y + h_ligne], fill=fond)
        cy = y + h_ligne // 2
        nom = j.nom + ("  (vainqueur)" if gagnant else "")
        while len(nom) > 3 and d.textlength(nom, font=f_txt) > 330:
            nom = nom[:-2] + "."
        valeurs = {"rang": str(rang), "nom": nom, "score": str(j.score),
                   "don": str(j.gorgees_donnees), "bue": str(j.gorgees_bues), "obj": objets(j)}
        for cle, _, x, anc in cols:
            police = f_score if cle in ("rang", "score") else (f_petit if cle == "obj" else f_txt)
            couleur = "#9B1C1C" if (cle == "score" and j.score < 0) else "#2B1B0E"
            txt = valeurs[cle]
            while cle == "obj" and len(txt) > 3 and d.textlength(txt, font=police) > 260:
                txt = txt[:-2] + "."
            _ecrire(d, (x, cy), txt, police, couleur, anc)
        y += h_ligne
    _ecrire(d, (W // 2, y + h_pied // 2), "Pas mou, le caillou !", f_sous, "#8B5E34", "mm")
    img.save(chemin)
    return chemin

class Jeu:
    def __init__(self):
        self.reset()

    def reset(self, negatifs=True, aquitaine=False, niveau=3):
        self.joueurs = []
        self.idx = 0
        self.tour = 0
        self.en_cours = False
        self.journal = []
        self.etats = []
        self.victoire_annoncee = False
        self.vainqueur_special = None
        self.gagnant = None
        self.aquitaine = aquitaine
        self.negatifs = True if aquitaine else negatifs
        self.niveau = niveau
        self.mult = 1
        self.defi_en_attente = False

    def nouvelle(self, noms, negatifs, aquitaine, niveau):
        self.reset(negatifs, aquitaine, niveau)
        self.en_cours = True
        for n in noms:
            self.ajouter(n)
        opts = ["règles à l'Aquitaine" if aquitaine else f"premier à {OBJECTIF} points",
                f"règles {'★' * niveau}"]
        if not aquitaine:
            opts.append("scores négatifs " + ("autorisés" if self.negatifs else "interdits"))
        self.dire("Nouvelle partie : " + ", ".join(opts) + ". Pas mou, le caillou !")

    @property
    def actifs(self):
        return [j for j in self.joueurs if not j.elimine]

    def autres(self, j):
        return [p for p in self.actifs if p is not j]

    def dire(self, msg):
        print(msg)
        self.journal.append(msg.strip())

    def gagner(self, j, pts, raison, ricochet=True):
        if pts == 0:
            return
        if self.aquitaine:
            j.score += pts
            n = ceil_div(abs(pts), 10)
            if pts > 0:
                j.gorgees_donnees += n
                fin = f"{j.nom} DONNE {gorgees(n)}"
            else:
                j.gorgees_bues += n
                fin = f"{j.nom} BOIT {gorgees(n)}"
            self.dire(f"   >> {j.nom} {pts:+d} pts ({raison}) - {fin} (total : {j.score})")
            return
        excedent = 0
        if pts < 0 and not self.negatifs:
            if j.score >= -pts:
                j.score += pts
            else:
                excedent = -pts - j.score
                pts = -j.score
                j.score = 0
        else:
            j.score += pts
        if pts == 0:
            self.dire(f"   >> {j.nom} est à 0 : il ne peut pas perdre de points ({raison})")
        else:
            self.dire(f"   >> {j.nom} {pts:+d} pts ({raison}) - total : {j.score}")
        if excedent and ricochet:
            for p in self.autres(j):
                self.gagner(p, excedent, f"{j.nom} est à zéro", False)
        self.controle(j)

    def boire(self, j, n, raison):
        j.gorgees_bues += n
        self.dire(f"   >> {j.nom} BOIT {gorgees(n)} ({raison})")

    def controle(self, j):
        if self.aquitaine:
            return
        if not self.negatifs and j.score < MIN_GRELOTTINE and j.grelottine:
            j.grelottine = 0
            self.dire(f"   {j.nom} passe sous {MIN_GRELOTTINE} pts : il perd sa Grelottine.")
        if self.negatifs and j.score <= ELIMINATION_NEGATIVE and not j.elimine:
            j.elimine = True
            self.dire(f"   {j.nom} atteint {j.score} pts : il est ÉLIMINÉ de la partie.")

    def bevue_a(self, j, raison):
        self.gagner(j, -PENALITE_BEVUE, f"Bévue : {raison}")

    def capture(self):
        return (copy.deepcopy(self.joueurs), self.idx, len(self.journal), self.tour)

    def restaurer(self, snap):
        self.joueurs, self.idx, n, self.tour = copy.deepcopy(snap[0]), snap[1], snap[2], snap[3]
        del self.journal[n:]

    def sauver_etat(self):
        self.etats.append(self.capture())

    def annuler(self):
        if not self.etats:
            print("   Rien à annuler.")
            return False
        snap = self.etats.pop()
        self.restaurer(snap)
        self.vainqueur_special = None
        print("   Dernière action annulée.")
        return True

    def choisir_joueurs(self, question, parmi=None, un_seul=False):
        parmi = parmi if parmi is not None else self.actifs
        if not parmi:
            return []
        numeros = {self.joueurs.index(p) + 1: p for p in parmi}
        print("   " + "   ".join(f"{k}) {p.nom}" for k, p in numeros.items()))
        while True:
            s = saisir(f"   {question} ")
            if s == "":
                return []
            try:
                nums = [int(x) for x in re.split(r"[\s,;]+", s)]
            except ValueError:
                print("   Entre des numéros séparés par des virgules.")
                continue
            if any(k not in numeros for k in nums):
                print("   Numéro invalide.")
                continue
            nums = list(dict.fromkeys(nums))
            if un_seul and len(nums) > 1:
                print("   Un seul numéro, s'il te plaît.")
                continue
            return [numeros[k] for k in nums]

    def afficher_scores(self):
        if not self.joueurs:
            print("   Aucun joueur inscrit.")
            return
        larg = max(6, max(len(j.nom) for j in self.joueurs))
        print()
        if self.aquitaine:
            print(f"   {'#':>2}  {'Joueur':<{larg}}  {'Score':>6}  Donné  Bu  Objets")
        else:
            print(f"   {'#':>2}  {'Joueur':<{larg}}  {'Score':>6}  {'Reste':>6}  Objets")
        print("   " + "-" * (larg + 40))
        for rang, j in classer(self.joueurs):
            if self.aquitaine:
                print(f"   {rang:>2}  {j.nom:<{larg}}  {j.score:>6}  {j.gorgees_donnees:>5}  "
                      f"{j.gorgees_bues:>2}  {objets(j)}")
            else:
                print(f"   {rang:>2}  {j.nom:<{larg}}  {j.score:>6}  "
                      f"{max(0, OBJECTIF - j.score):>6}  {objets(j)}")
        print()

    def afficher_journal(self):
        if not self.journal:
            print("   Journal vide.")
        for ligne in self.journal[-25:]:
            print("   |", ligne)

    def afficher_regles(self):
        for titre, texte in REGLES:
            print(f"\n=== {titre} ===\n{texte}")

    def menu(self):
        print("\n" + "=" * 60)
        print("   CUL DE CHOUETTE - Maître du Jeu (by Vodoxiss - V2.0)")
        print("=" * 60)
        while True:
            etat = (f"partie en cours, {len(self.joueurs)} joueur(s)"
                    if self.en_cours else "aucune partie en cours")
            print(f"\n--- MENU ({etat}) ---")
            print("  1) Nouvelle partie        6) Bévue")
            print("  2) Inscrire un joueur     7) Défi Grelottine")
            print("  3) Jouer / continuer      8) Règles du jeu")
            print("  4) Tableau des scores     9) Exporter le tableau (.png)")
            print("  5) Terminer + .png        0) Quitter")
            c = saisir("> ")
            if c == "1":
                self.nouvelle_partie_console()
            elif c == "2":
                self.inscrire_console()
            elif c == "3":
                self.jouer()
            elif c == "4":
                self.afficher_scores()
            elif c == "5":
                self.terminer()
            elif c == "6":
                self.bevue()
            elif c == "7":
                self.defi_manuel()
            elif c == "8":
                self.afficher_regles()
            elif c == "9":
                self.exporter(termine=False)
            elif c == "0":
                if self.en_cours and not ask_yes_no("Une partie est en cours. Quitter quand même ?"):
                    continue
                print("Pas mou, le caillou ! À bientôt.")
                return
            else:
                print("   Choix invalide.")

    def nouvelle_partie_console(self):
        if self.en_cours and self.joueurs and not ask_yes_no(
                "Une partie est en cours : l'abandonner et en commencer une nouvelle ?"):
            return
        aq = ask_yes_no("Règles à l'Aquitaine (score converti en gorgées) ?")
        neg = True if aq else ask_yes_no("Autoriser les scores négatifs ?")
        niv = ask_int("Niveau de règles (1 = ★, 2 = ★★, 3 = ★★★) :", 1, 3)
        noms = []
        print("Inscris les joueurs (Entrée pour terminer la liste).")
        while True:
            nom = saisir(f"   Nom du joueur {len(noms) + 1} : ")
            if not nom:
                break
            if nom.lower() in (n.lower() for n in noms):
                print("   Ce nom existe déjà.")
                continue
            noms.append(nom)
        self.nouvelle(noms, neg, aq, niv)
        if len(self.joueurs) >= 2:
            self.jouer()
        else:
            print("   Il faut au moins 2 joueurs (menu 2 pour en ajouter).")

    def inscrire_console(self):
        if not self.en_cours:
            self.reset()
            self.en_cours = True
        nom = saisir("   Nom du joueur : ")
        if nom:
            self.inscrire(nom)

    def ajouter(self, nom, score=0):
        if any(j.nom.lower() == nom.lower() for j in self.joueurs):
            print("   Ce nom existe déjà.")
            return False
        self.joueurs.append(Joueur(nom, score))
        print(f"   {nom} est inscrit(e).")
        return True

    def inscrire(self, nom):
        if self.tour == 0 or len(self.actifs) < 2:
            return self.ajouter(nom)
        if any(j.nom.lower() == nom.lower() for j in self.joueurs):
            print("   Ce nom existe déjà.")
            return False
        if self.aquitaine:
            n = min(LIMITE_SLOUBI, self.tour)
            self.dire(f"   {nom} rejoint la partie : il doit chanter « Sloubi 1, sloubi 2... » jusqu'à {n}.")
            return self.ajouter(nom)
        scores = sorted((j.score for j in self.actifs), reverse=True)
        valeur = ((scores[0] - scores[1]) * self.tour) // 10
        print(f"   CHANTE-SLOUBI : {nom} doit chanter « Sloubi 1, sloubi 2... » jusqu'à {valeur} "
              f"(écart des deux meilleurs x {self.tour} tours / 10).")
        if valeur > LIMITE_SLOUBI:
            self.dire(f"   Le Sloubi dépasse {LIMITE_SLOUBI} : {nom} ne peut pas entrer maintenant.")
            return False
        reussi = ask_yes_no(f"   {nom} chante-t-il jusqu'au bout, sans bévue ni interruption ?")
        score = int(valeur * (1.5 if reussi else 1))
        self.dire(f"   {nom} entre dans la partie avec {score} pts" + (" (x1,5 : Sloubi réussi)." if reussi else "."))
        return self.ajouter(nom, score)

    def jouer(self):
        if not self.en_cours:
            print("   Aucune partie en cours : commence par 'Nouvelle partie'.")
            return
        if len(self.actifs) < 2:
            print("   Il faut au moins 2 joueurs.")
            return
        print("\nCommandes à la saisie des chouettes : scores | annuler | journal | regles | menu")
        while True:
            try:
                self.tour_suivant()
            except RetourMenu:
                return
            except Recommencer:
                continue
            self.afficher_scores()
            if self.verifier_victoire():
                return

    def verifier_victoire(self):
        if self.aquitaine or not self.en_cours or self.victoire_annoncee:
            return False
        gagnant, msg = None, ""
        if self.vainqueur_special:
            gagnant, msg = self.vainqueur_special, "gagne la partie avec un Cul de Chouette doublé identique"
        elif len(self.joueurs) > 1 and len(self.actifs) == 1:
            gagnant, msg = self.actifs[0], "est le dernier joueur en lice"
        else:
            cand = [j for j in self.actifs if j.score >= OBJECTIF]
            if cand:
                gagnant = max(cand, key=lambda j: j.score)
                msg = f"a atteint {gagnant.score} points (objectif : {OBJECTIF})"
        if not gagnant:
            return False
        self.victoire_annoncee = True
        print(f"*** {gagnant.nom} {msg} ! ***")
        if ask_yes_no("Terminer la partie maintenant ?"):
            self.terminer(gagnant)
            return True
        return False

    def lire_chouettes(self, j):
        while True:
            s = saisir(f"Chouettes de {j.nom} (2 dés, ex : 4 4) ou commande > ").lower()
            if s in ("menu", "m"):
                raise RetourMenu
            if s in ("scores", "s"):
                self.afficher_scores()
            elif s in ("annuler", "a"):
                if self.annuler():
                    raise Recommencer
            elif s in ("journal", "j"):
                self.afficher_journal()
            elif s in ("regles", "r"):
                self.afficher_regles()
            else:
                d = parse_des(s, 2)
                if d:
                    return d
                print("   Saisie invalide : 2 dés de 1 à 6, ou une commande.")

    def tour_suivant(self):
        self.vainqueur_special = None
        self.defi_en_attente = False
        self.mult = 1
        while self.joueurs[self.idx].elimine:
            self.idx = (self.idx + 1) % len(self.joueurs)
        j = self.joueurs[self.idx]
        snap = self.capture()
        print("\n" + "=" * 60)
        o = objets(j)
        print(f"TOUR {self.tour + 1} - C'est à {j.nom} de jouer (score {j.score}"
              + (f", {o}" if o != "-" else "") + ")")
        try:
            self._jouer_tour(j)
        except RetourMenu:
            self.restaurer(snap)
            self.mult = 1
            raise
        self.etats.append(snap)
        self.mult = 1
        self.idx = (self.idx + 1) % len(self.joueurs)
        self.tour += 1
        if self.defi_en_attente:
            self.defi_en_attente = False
            self.proposer_defi()

    def _jouer_tour(self, j):
        mode = None
        if self.niveau >= 3 and j.jarret:
            mode = self.choisir_jarret(j)
        civet = None
        if j.civets and ask_yes_no(f"   {j.nom} déclare-t-il un CIVET avant de lancer ?"):
            civet = self.demander_civet(j)
        if mode == "bi":
            self.mult = 2
            self.dire("   Bi-Jarret : la combinaison vaudra le double.")

        des, acteur, verdier = self.lancer(j, civet is not None, mode)
        combo = analyser(des, self.niveau, self.aquitaine)
        achat = acteur is not j
        self.dire(f"\n{j.nom} : chouettes {des[0]} et {des[1]}, cul {des[2]}"
                  + (f" (lancé par {acteur.nom})" if achat else "") + f"  =>  {combo.libelle().upper()}")
        if achat and des[0] == des[1]:
            self.gagner(j, des[0] ** 2 * self.mult, f"Chouette de {des[0]} (cul acheté)")
        res = self.resoudre(acteur, combo, libre=not achat, grel=True)

        if verdier:
            reussi = sorted(des) == [2, 4, 6]
            for p in verdier:
                if reussi:
                    self.gagner(p, GAIN_PARI, "Verdier réussi : Velute de 6")
                else:
                    self.gagner(p, -MISE_PARI, "Verdier raté")
        if civet:
            self.resoudre_civet(j, civet, combo, res)

    def lancer(self, j, civet, mode):
        if mode == "mi":
            des = saisir_lancer(f"1er lancer de {j.nom} (Mi-Jarret)", LABELS3)
            if ask_yes_no("   « Bjarret ! » : garde-t-il ce premier lancer ?"):
                return des, j, []
            des = saisir_lancer(f"2e lancer de {j.nom} (Mi-Jarret)", LABELS3)
            return des, j, []
        chouettes = self.lire_chouettes(j)
        verdier = []
        if self.niveau >= 3 and sorted(chouettes) in ([2, 4], [2, 6], [4, 6]):
            verdier = self.annonces_verdier(j)
        acteur = j
        peut_acheter = (self.niveau >= 2 and not civet and mode is None and chouettes != [6, 6])
        while True:
            extras = []
            if peut_acheter:
                extras = [("achat", "J'achète !" if acteur is j else "Je rachète !")]
            r = saisir_lancer(f"Cul de {acteur.nom}", LABELS_CUL, extras)
            if isinstance(r, str):
                b = self.choisir_acheteur(acteur)
                if b:
                    acteur = b
                continue
            return chouettes + r, acteur, verdier

    def choisir_acheteur(self, actuel):
        cand = [p for p in self.autres(actuel) if self.aquitaine or p.score >= PRIX_ACHAT]
        if not cand:
            self.dire(f"   Personne n'a les {PRIX_ACHAT} pts nécessaires pour acheter.")
            return None
        qui = self.choisir_joueurs("Qui crie « J'achète ! » ? (Entrée = personne)", parmi=cand,
                                   un_seul=True)
        if not qui:
            return None
        b = qui[0]
        self.gagner(b, -PRIX_ACHAT, "achat du cul")
        self.dire(f"   {b.nom} achète le cul : c'est lui qui le lance ; la Chouette reste au lanceur.")
        return b

    def annonces_verdier(self, j):
        print("   VERDIER possible : les chouettes peuvent donner une Velute de 6 (6-4-2).")
        print(f"   Les autres joueurs peuvent crier « Vert-Linette ! » (pari de {MISE_PARI} pts, gain {GAIN_PARI}).")
        cand = [p for p in self.autres(j) if self.negatifs or self.aquitaine or p.score >= MISE_PARI]
        return self.choisir_joueurs("Qui parie « Vert-Linette ! » ? (plusieurs possibles, Entrée = personne)",
                                    parmi=cand)

    def choisir_jarret(self, j):
        choix = choisir_option(f"{j.nom} possède un JARRET. Comment l'utilise-t-il ?", [
            ("non", "Il le garde pour plus tard"),
            ("mi", "Mi-Jarret : deux lancers (il garde les dés qu'il veut)"),
            ("bi", "Bi-Jarret : la combinaison vaut le double"),
            ("donne", "Lance-Jarret : le donner à un autre joueur")])
        if choix == "donne":
            cible = self.choisir_joueurs("À qui donne-t-il son Jarret ?", parmi=self.autres(j), un_seul=True)
            if cible:
                if cible[0].jarret:
                    self.bevue_a(j, "Lance-Jarret vers un joueur qui en a déjà un")
                else:
                    j.jarret, cible[0].jarret = False, True
                    self.dire(f"   {j.nom} lance son Jarret à {cible[0].nom}.")
            return None
        if choix in ("mi", "bi"):
            j.jarret = False
            return choix
        return None

    def paris_civet(self):
        p = [("chouette", "Chouette"), ("velute", "Velute"), ("chouette_velute", "Chouette-Velute"),
             ("suite", "Suite"), ("cul", "Cul de Chouette (sans sirotage)"),
             ("cul_siro", "Cul de Chouette (avec sirotage)")]
        if self.niveau >= 2:
            p += [("artichette", "Artichette"), ("soufflette", "Soufflette"),
                  ("suite_velutee", "Suite-Velutée")]
        if self.niveau >= 3:
            p += [("bleu_rouge", "Bleu-Rouge (la relance du lanceur doit être bonne)")]
        return p

    def demander_civet(self, j):
        libre = self.negatifs or self.aquitaine
        maxi = CIVET_MAX if libre else min(CIVET_MAX, j.score)
        if maxi < 1:
            self.dire(f"   {j.nom} n'a pas assez de points pour miser un Civet.")
            return None
        print(f"   CIVET : {j.nom} mise des points et parie sur son prochain coup.")
        mise = ask_int(f"   Mise (1 à {maxi}) :", 1, maxi)
        pari = choisir_option("   Pari :", self.paris_civet())
        label = dict(self.paris_civet())[pari]
        self.dire(f"   « Civet de {mise} sur {label} ! »")
        facteur = 1
        if self.niveau >= 2:
            porteurs = [p for p in self.autres(j) if p.civets]
            if porteurs:
                qui = self.choisir_joueurs("Qui crie « Civet doublé ! » ? (plusieurs possibles, Entrée = personne)",
                                           parmi=porteurs)
                for p in qui:
                    if not libre and mise * facteur * 2 > j.score:
                        self.bevue_a(p, "Civet doublé au-delà des points du joueur")
                        continue
                    p.civets = 0
                    facteur *= 2
                    self.dire(f"   {p.nom} double la mise (et sacrifie son Civet) : mise x{facteur}.")
        return {"mise": mise * facteur, "pari": pari}

    def resoudre_civet(self, j, civet, combo, res):
        mise, pari = civet["mise"] * self.mult, civet["pari"]
        j.civets = 0
        label = dict(self.paris_civet())[pari]
        if pari == "cul_siro":
            ok = res["siro"] is True
        elif pari == "bleu_rouge":
            ok = res["relance"] is j
        else:
            ok = combo.matches(pari)
        if ok:
            self.dire(f"   CIVET RÉUSSI : {j.nom} avait parié sur « {label} ».")
            self.gagner(j, mise, "civet réussi")
        else:
            self.dire(f"   CIVET RATÉ : {j.nom} avait parié sur « {label} ».")
            self.gagner(j, -mise, "civet raté")

    def donner_civet(self, p):
        if p.civets:
            self.dire(f"   {p.nom} a déjà un Civet (non cumulable).")
        else:
            p.civets = 1
            self.dire(f"   {p.nom} gagne un CIVET.")

    def lance_civet(self):
        porteurs = [p for p in self.actifs if p.civets]
        if not porteurs:
            print("   Personne n'a de Civet.")
            return
        qui = self.choisir_joueurs("Qui lance son Civet ? (« Lance-Civet ! »)", parmi=porteurs, un_seul=True)
        if not qui:
            return
        cible = self.choisir_joueurs("À qui ?", parmi=self.autres(qui[0]), un_seul=True)
        if not cible:
            return
        snap = self.capture()
        if cible[0].civets:
            self.bevue_a(qui[0], "Lance-Civet vers un joueur qui en a déjà un")
        else:
            qui[0].civets, cible[0].civets = 0, 1
            self.dire(f"   {qui[0].nom} lance son Civet à {cible[0].nom}.")
        self.etats.append(snap)

    def resoudre(self, a, combo, libre=True, grel=True):
        m = self.mult
        k = combo.kind
        res = {"siro": None, "relance": None}
        if k == "cul":
            self.cul_de_chouette(a, combo.valeur, libre)
        elif k == "chouette":
            if libre:
                res["siro"] = self.chouette(a, combo.valeur)
            else:
                self.gagner(a, combo.points * m, combo.libelle())
        elif k == "velute":
            self.gagner(a, combo.points * m, combo.libelle())
            if combo.suite:
                self.suite()
        elif k == "chouette_velute":
            self.chouette_velute(combo)
        elif k == "suite":
            self.suite()
        elif k == "suite_velutee":
            self.suite_velutee(a)
        elif k == "artichette":
            self.artichette(a)
        elif k == "soufflette":
            self.soufflette(a)
        elif k == "bleu_rouge":
            res["relance"] = self.bleu_rouge(a)
        elif k == "neant_souffle":
            self.neant_souffle()
        elif k == "excalibur":
            self.excalibur()
        else:
            self.dire("   Aucune combinaison.")
            if grel:
                self.donner_grelottine(a)
                self.defi_en_attente = True
        return res

    def cul_de_chouette(self, a, v, libre=True):
        pts = 40 + 10 * v
        m = self.mult
        if libre and self.niveau >= 2:
            print(f"   {a.nom} peut tenter de DOUBLER son Cul de Chouette (« Cul de Chouette ! ») :")
            print("   un seul lancer des 3 dés. Réussite : points des deux culs (et victoire si même valeur).")
            print("   Échec : il est éliminé de la partie et son cul ne compte pas.")
            if ask_yes_no(f"   {a.nom} tente-t-il de doubler son Cul de Chouette ?"):
                d = saisir_lancer(f"Lancer unique de {a.nom} (Cul de Chouette doublé)", LABELS3)
                if d[0] == d[1] == d[2]:
                    v2 = d[0]
                    self.gagner(a, (pts + 40 + 10 * v2) * m, f"Cul de Chouette doublé ({v} puis {v2})")
                    if v2 == v:
                        self.dire(f"   Même valeur : {a.nom} REMPORTE LA PARTIE !")
                        self.vainqueur_special = a
                else:
                    self.dire(f"   Échec : {a.nom} est éliminé de la partie ! (son cul ne compte pas)")
                    a.elimine = True
                return
        self.gagner(a, pts * m, f"Cul de Chouette de {v}")

    def chouette(self, j, n):
        pts = n * n
        options = [("non", f"Personne ne sirote : {j.nom} marque sa Chouette (+{pts * self.mult} pts)"),
                   ("sirop", f"{j.nom} sirote (« Je sirote ! »)")]
        if self.niveau >= 2:
            for p in self.autres(j):
                options.append((f"ao:{self.joueurs.index(p)}", f"Attrape-Oiseau : {p.nom}"))
        print(f"   CHOUETTE DE {n}. Sirotage possible : relancer un dé pour viser un Cul de Chouette de {n}.")
        choix = choisir_option("   Que se passe-t-il ?", options)
        if choix == "non":
            self.gagner(j, pts * self.mult, f"Chouette de {n}")
            return None
        acteur = j if choix == "sirop" else self.joueurs[int(choix.split(":")[1])]
        if acteur is not j:
            self.gagner(j, pts * self.mult, f"Chouette de {n} (l'oiseau est attrapé)")
        res = self.sirotage(acteur, n)
        if res is None and acteur is j:
            self.gagner(j, pts * self.mult, f"Chouette de {n}")
        return res

    def sirotage(self, a, n, defi=False):
        m = 1 if defi else self.mult
        cul_pts = 40 + 10 * n
        valeur_cs = cul_pts // 5
        oiseaux = ", ".join(f"{k}={v}" for k, v in OISEAUX.items())
        print(f"   {a.nom} sirote : il relance un dé pour faire un Cul de Chouette de {n} (+{cul_pts * m} pts).")
        print(f"   Échec : -{n * n * m} pts" + (" et il gagne un CIVET (sirotage de 6)." if n == 6 else "."))
        if not (self.negatifs or self.aquitaine) and a.score < n * n:
            self.dire(f"   {a.nom} n'a pas assez de points ({a.score} < {n * n}) : sirotage interdit.")
            qui = self.choisir_joueurs("Qui crie « Sirop-Jeannot ! » en premier ? (plusieurs = tous gagnent)",
                                       parmi=self.autres(a))
            for p in qui:
                self.gagner(p, valeur_cs, "Sirop-Jeannot")
            return None
        print(f"   Les autres joueurs parient {MISE_PARI} pts sur le dé (gain {GAIN_PARI}) : {oiseaux}.")
        print("   « Beau-Sirop ! » = parier sur la réussite ; « Couche-Sirop ! » = ne pas parier.")
        paris = []
        for p in self.autres(a):
            if not (self.negatifs or self.aquitaine) and p.score < MISE_PARI:
                continue
            v = ask_int(f"   Pari de {p.nom} (1-6, Entrée = pas de pari) :", 1, 6, vide_ok=True)
            if v:
                paris.append((p, v))
        de = ask_int(f"   Résultat du dé de sirotage de {a.nom} (1-6) :", 1, 6)
        self.dire(f"   Le dé tombe sur {de} ({OISEAUX[de]}).")
        reussi = (de == n)
        for p, v in paris:
            if v == de:
                self.gagner(p, GAIN_PARI, f"pari gagné ({OISEAUX[de]})")
            else:
                self.gagner(p, -MISE_PARI, "pari perdu au sirop")
        if reussi:
            self.cul_de_chouette(a, n, libre=True)
        else:
            self.gagner(a, -n * n * m, f"sirotage raté : perd la Chouette de {n}")
            if n == 6:
                self.donner_civet(a)
            if self.niveau >= 2 and not any(v == de for _, v in paris):
                cand = self.actifs if len(self.actifs) == 2 else self.autres(a)
                print(f"   CONTRE-SIROP : le premier qui crie « J'apprécie les fruits au sirop ! » gagne {valeur_cs} pts")
                print("   (égalité : les joueurs concernés perdent ces points).")
                qui = self.choisir_joueurs("Qui crie en premier ? (plusieurs = égalité, Entrée = personne)",
                                           parmi=cand)
                if len(qui) == 1:
                    self.gagner(qui[0], valeur_cs, "Contre-Sirop")
                else:
                    for p in qui:
                        self.gagner(p, -valeur_cs, "égalité sur le Contre-Sirop")
        return reussi

    def chouette_velute(self, combo):
        pts = combo.points * self.mult
        print(f"   CHOUETTE-VELUTE ! Le premier qui frappe dans ses mains en criant « Pas mou, le caillou ! »")
        print(f"   gagne {pts} points. En cas d'égalité, les joueurs concernés perdent ces points.")
        qui = self.choisir_joueurs("Qui a crié en premier ? (plusieurs = égalité, Entrée = personne)")
        if not qui:
            self.dire("   Personne n'a réagi : pas de point.")
        elif len(qui) == 1:
            self.gagner(qui[0], pts, "Pas mou, le caillou")
        else:
            for p in qui:
                self.gagner(p, -pts, "égalité sur Pas mou, le caillou")

    def suite(self):
        pen = PENALITE_SUITE * self.mult
        print("   SUITE ! Tous les joueurs frappent du poing sur la table en criant « Grelotte ça picote ! ».")
        print(f"   Le dernier perd {pen} points (égalité : « Sans fin, est la moisissure des bières bretonnes »,")
        print("   puis un dé : le plus grand perd).")
        qui = self.choisir_joueurs("Qui est le dernier ? (un seul, Entrée = personne)", un_seul=True)
        if qui:
            self.gagner(qui[0], -pen, "dernier sur la Suite")
        else:
            self.dire("   Personne ne perd de points.")

    def suite_velutee(self, a):
        self.suite()
        print("   SUITE-VELUTÉE (1-2-3) : le lanceur peut attraper une chouette en criant « Patte de canaaard ! »")
        print("   (il valide alors sa Velute). Sinon un adversaire peut les attraper en criant « Velutée ! ».")
        choix = choisir_option("   Que se passe-t-il ?", [
            ("rien", "Personne ne réagit (seule la Suite s'applique)"),
            ("patte", f"{a.nom} crie « Patte de canaaard ! » : sa Velute de 3 est validée (+18)"),
            ("velutee", "Un adversaire crie « Velutée ! » et relance les chouettes"),
            ("deux", "Deux adversaires crient « Velutée ! » en même temps")])
        if choix == "patte":
            self.gagner(a, 18 * self.mult, "Velute de 3 (Patte de canaaard)")
        elif choix == "velutee":
            r = self.choisir_joueurs("Qui crie « Velutée ! » ?", parmi=self.autres(a), un_seul=True)
            if r:
                ch = saisir_lancer(f"Nouvelles chouettes ({r[0].nom} relance les deux, le cul reste 3)", LABELS2)
                c2 = analyser(ch + [3], 1)
                self.dire(f"   Nouveau résultat : {ch[0]} {ch[1]} 3  =>  {c2.libelle()}")
                self.resoudre(r[0], c2, libre=False, grel=False)
        elif choix == "deux":
            r = self.choisir_joueurs("Qui sont les deux joueurs ?", parmi=self.autres(a))
            if len(r) >= 2:
                ch = saisir_lancer(f"Une chouette relancée par {r[0].nom}, une par {r[1].nom}", LABELS2)
                c2 = analyser(ch + [3], 1)
                self.dire(f"   Nouveau résultat : {ch[0]} {ch[1]} 3  =>  {c2.libelle()}")
                if c2.points:
                    self.gagner(a, -c2.points * self.mult, f"{c2.libelle()} retourné contre le lanceur")
            else:
                self.dire("   Il faut deux joueurs : rien ne se passe.")

    def artichette(self, a):
        pts = 16 * self.mult
        print(f"   ARTICHETTE (4-4-3) : le lanceur gagne {pts} pts en criant « Raitournelle ! », sauf si un autre")
        print(f"   joueur lui crie d'abord « Artichette ! » en le désignant : il perd alors {pts} pts.")
        choix = choisir_option("   Que se passe-t-il ? (égalité : le lanceur est prioritaire)", [
            ("lanceur", f"{a.nom} crie « Raitournelle ! » en premier (+{pts})"),
            ("autre", f"Un autre joueur crie « Artichette ! » en premier ({a.nom} perd {pts})"),
            ("rien", "Personne ne dit rien")])
        if choix == "lanceur":
            self.gagner(a, pts, "Artichette : Chouette de 4")
        elif choix == "autre":
            self.gagner(a, -pts, "Artichette dénoncée")

    def soufflette(self, a):
        print("   SOUFFLETTE (4-2-1) : le lanceur peut défier un joueur en criant « En garde ma mignonne ! ».")
        print("   Le soufflé a 3 lancers pour réussir 4-2-1 : 1er = 50 pts, 2e = 40, 3e = 30 (pour lui, contre le souffleur).")
        print("   Échec : le soufflé perd 30 pts (au profit du souffleur), puis marque sa dernière combinaison.")
        seuil = 0 if (self.negatifs or self.aquitaine) else MIN_GRELOTTINE
        cand = [p for p in self.autres(a) if p.score >= seuil and a.score >= seuil]
        if not cand:
            self.dire("   La Soufflette ne peut pas être jouée (scores insuffisants).")
            return
        qui = self.choisir_joueurs("Qui est défié ? (Entrée = personne)", parmi=cand, un_seul=True)
        if not qui:
            return
        s = qui[0]
        des = None
        for essai in (1, 2, 3):
            des = saisir_lancer(f"Lancer {essai}/3 de {s.nom} (il doit faire 4-2-1)", LABELS3)
            if sorted(des) == [1, 2, 4]:
                pts = {1: 50, 2: 40, 3: 30}[essai]
                self.dire(f"   {s.nom} réussit au lancer {essai} !")
                self.gagner(s, pts, "Soufflette relevée")
                self.gagner(a, -pts, "Soufflette perdue")
                return
        self.dire(f"   {s.nom} échoue.")
        self.gagner(s, -30, "Soufflette échouée")
        self.gagner(a, 30, "Soufflette gagnée")
        c = analyser(des, self.niveau, self.aquitaine)
        self.dire(f"   Dernière combinaison de {s.nom} : {c.libelle()}")
        self.resoudre(s, c, libre=False, grel=False)

    def bleu_rouge(self, a):
        m = self.mult
        self.gagner(a, 9 * m, "Bleu-Rouge : Chouette de 3")
        print("   BLEU-ROUGE ! Chaque joueur annonce une relance DIFFÉRENTE (somme des 3 dés, de 3 à 18),")
        print(f"   puis {a.nom} relance les trois dés. Bonne relance : 36 pts + 2 x la valeur + la combinaison.")
        paris = {}
        for p in self.actifs:
            while True:
                v = ask_int(f"   Relance de {p.nom} (3 à 18) :", 3, 18)
                if v in paris:
                    print(f"   {paris[v].nom} a déjà annoncé {v} : choisis une autre valeur.")
                    continue
                paris[v] = p
                break
        des = saisir_lancer(f"Relance de {a.nom} (les 3 dés)", LABELS3)
        total = sum(des)
        c = analyser(des, min(self.niveau, 2), False)
        self.dire(f"   Relance : {des[0]} {des[1]} {des[2]} = {total}  =>  {c.libelle()}")
        gagnant = paris.get(total)
        if gagnant:
            self.gagner(gagnant, (36 + 2 * total) * m, f"relance de {total} réussie")
            self.resoudre(gagnant, c, libre=False, grel=False)
        else:
            self.dire("   Personne n'a trouvé la relance : aucune combinaison ne s'applique.")
        if c.kind == "cul" and c.valeur == 6:
            self.dire("   PÉLICAN !")
            print("   Le premier qui crie « Pélican ! » gagne 28 pts (égalité : « Passe-Montagne ! », puis")
            print("   « Zbradaraldjan ! », puis celui qui avait annoncé 18).")
            qui = self.choisir_joueurs("Qui a crié « Pélican ! » en premier ? (Entrée = personne)", un_seul=True)
            if qui:
                self.gagner(qui[0], 28 * m, "Pélican")
        elif c.kind == "neant":
            print("   JARRET ! Le premier qui crie « Lance-Bûches ! » obtient un Jarret.")
            qui = self.choisir_joueurs("Qui crie « Lance-Bûches ! » en premier ? (plusieurs = tous, Entrée = personne)")
            for p in qui:
                if p.jarret:
                    self.dire(f"   {p.nom} a déjà un Jarret (non cumulable).")
                else:
                    p.jarret = True
                    self.dire(f"   {p.nom} obtient un JARRET.")
        return gagnant

    def neant_souffle(self):
        print("   NÉANT SOUFFLÉ (1-4-6) : le premier qui crie « Mécréant ! » en se touchant le nez récupère la Grelottine")
        print("   (le lanceur peut participer). Avec « Je suis un misérable » : personne ne la récupère.")
        qui = self.choisir_joueurs("Qui a crié « Mécréant ! » en premier ? (Entrée = personne)", un_seul=True)
        if qui:
            self.donner_grelottine(qui[0], bevue=True)
            self.defi_en_attente = True
        else:
            self.dire("   Personne ne récupère la Grelottine.")

    def excalibur(self):
        if len(self.actifs) < 3:
            self.dire("   Excalibur (5-3-1) ne se joue qu'à 3 joueurs ou plus : rien ne se passe.")
            return
        print("   EXCALIBUR (5-3-1) : les joueurs peuvent crier « Excalibur ! » en levant le doigt.")
        print("   Seul : Bévue. À deux ou plus : ils désignent un Roi qui boit autant de gorgées que d'annonceurs.")
        qui = self.choisir_joueurs("Qui a crié « Excalibur ! » ? (Entrée = personne)")
        k = len(qui)
        if k == 0:
            return
        if k == 1:
            self.bevue_a(qui[0], "Excalibur annoncé seul")
        elif k == len(self.actifs):
            self.dire(f"   GUERRE CIVILE ! Tout le monde boit {gorgees(k)}.")
            for p in self.actifs:
                self.boire(p, k, "Guerre civile")
        else:
            r = self.choisir_joueurs("Qui est désigné Roi ?", un_seul=True)
            if r:
                self.boire(r[0], k, "Roi (Excalibur)")

    def donner_grelottine(self, p, bevue=False):
        if not self.aquitaine and not self.negatifs and p.score < MIN_GRELOTTINE:
            if bevue:
                self.bevue_a(p, f"annonce avec moins de {MIN_GRELOTTINE} pts")
            self.dire(f"   {p.nom} a moins de {MIN_GRELOTTINE} pts : pas de Grelottine.")
            return
        if self.aquitaine:
            if p.grelottine >= GRELOTTINES_MAX_AQUITAINE:
                self.dire(f"   {p.nom} a déjà {GRELOTTINES_MAX_AQUITAINE} Grelottines (maximum).")
                return
            p.grelottine += 1
            self.dire(f"   {p.nom} gagne une GRELOTTINE (il en a {p.grelottine}).")
        elif p.grelottine:
            self.dire(f"   {p.nom} a déjà une Grelottine (non cumulable).")
        else:
            p.grelottine = 1
            self.dire(f"   {p.nom} gagne une GRELOTTINE.")

    def proposer_defi(self):
        porteurs = [p for p in self.actifs if p.grelottine]
        if len(porteurs) >= 2:
            print("   Plusieurs joueurs ont une Grelottine : un défi est possible entre deux tours.")
            if ask_yes_no("   Un joueur lance-t-il un défi GRELOTTINE maintenant ?"):
                self.defi_grelottine()

    def defi_manuel(self):
        if not self.en_cours:
            print("   Aucune partie en cours.")
            return
        snap = self.capture()
        if self.defi_grelottine():
            self.etats.append(snap)

    def defi_possible(self, g, d):
        if self.aquitaine:
            return True
        seuil = 1 if self.negatifs else MIN_GRELOTTINE
        return g.score >= seuil and d.score >= seuil

    def defis(self):
        l = [("chouette", "Chouette"), ("velute", "Velute"), ("chouette_velute", "Chouette-Velute"),
             ("cul", "Cul de Chouette")]
        if not self.aquitaine:
            l.append(("sirop", "Sirop-Grelot (Cul de Chouette obtenu avec un sirotage)"))
        return l

    def defi_grelottine(self):
        porteurs = [p for p in self.actifs if p.grelottine]
        if len(porteurs) < 2:
            print("   Il faut au moins deux joueurs possédant une Grelottine.")
            return False
        qui = self.choisir_joueurs("Qui crie « Grelottine ! » ? (plusieurs = le plus petit score devient grelottin)",
                                   parmi=porteurs)
        if not qui:
            return False
        if len(qui) > 1:
            mini = min(p.score for p in qui)
            qui = [p for p in qui if p.score == mini]
            if len(qui) > 1:
                print("   Égalité de score : départagez-vous par un dé (le plus petit l'emporte).")
                qui = self.choisir_joueurs("Qui devient grelottin ?", parmi=qui, un_seul=True) or qui[:1]
        g = qui[0]
        cible = self.choisir_joueurs(f"Qui {g.nom} défie-t-il ? (un joueur ayant une Grelottine)",
                                     parmi=[p for p in porteurs if p is not g], un_seul=True)
        if not cible:
            return False
        d = cible[0]
        if not self.defi_possible(g, d):
            self.bevue_a(g, "défi Grelottine impossible (score insuffisant)")
            return True

        if self.niveau >= 2 and d.immunite:
            choix = choisir_option(f"   {d.nom} est immunisé (il a gagné un défi). Que fait-il ?", [
                ("non", "Rien : il accepte le défi"),
                ("rigodon", "« Rigodon ! » : le défi est annulé, les deux Grelottines disparaissent"),
                ("passe", "« Passe-Grelot ! » : il renvoie le défi sur un autre joueur")])
            if choix == "rigodon":
                d.immunite = False
                g.grelottine = 0
                d.grelottine = 0
                self.dire(f"   Rigodon ! Le défi est annulé : {g.nom} et {d.nom} perdent leur Grelottine.")
                return True
            if choix == "passe":
                seuil = 0 if self.aquitaine else (3 if self.negatifs else MIN_GRELOTTINE)
                cand = [p for p in self.actifs if p not in (g, d) and p.score >= seuil]
                if len(self.actifs) < 3 or not cand:
                    self.dire("   Passe-Grelot impossible (pas de cible valable).")
                else:
                    nv = self.choisir_joueurs("Qui reçoit le défi ?", parmi=cand, un_seul=True)
                    if nv:
                        d.immunite = False
                        self.dire(f"   Passe-Grelot ! Le défi passe de {d.nom} à {nv[0].nom}.")
                        d = nv[0]

        type_ = choisir_option(f"   {g.nom} choisit la combinaison que {d.nom} doit réaliser :", self.defis())
        label = dict(self.defis())[type_]
        if self.aquitaine:
            mise = g.grelottine
            pts_mise = 10 * mise
            txt_mise = gorgees(mise)
        else:
            mn = min(g.score, d.score)
            maxi = ceil_div(mn, DENOM_DEFI[type_])
            print(f"   Mise maximale : {maxi} pts (1/{DENOM_DEFI[type_]} du plus petit score : {mn}, arrondi au supérieur).")
            mise = maxi if maxi <= 1 else ask_int(f"   Mise de {g.nom} (1 à {maxi}) :", 1, maxi)
            pts_mise = mise
            txt_mise = f"{mise} pts"
        g.grelottine = 0
        self.dire(f"   {g.nom} défie {d.nom} : « {label} » pour {txt_mise} (la Grelottine de {g.nom} est dépensée).")
        print(f"   {d.nom} a 2 lancers (il garde les dés qu'il veut entre les deux). Réussite au 1er lancer : il s'arrête.")

        reussi, sirote, des = False, False, None
        for essai in (1, 2):
            des = saisir_lancer(f"Lancer {essai}/2 de {d.nom} : {label}", LABELS3)
            base = analyser(des, 1)
            if type_ == "sirop":
                if base.kind == "chouette":
                    if essai == 2 or ask_yes_no(f"   {d.nom} sirote-t-il maintenant ? (obligatoire au 2e lancer)"):
                        if essai == 2:
                            print("   Chouette au 2e lancer : le sirotage est obligatoire.")
                        r = self.sirotage(d, base.valeur, defi=True)
                        sirote = r is not None
                        if r:
                            reussi = True
                            break
            elif base.matches(type_):
                reussi = True
                break
        if reussi:
            self.dire(f"   DÉFI RÉUSSI : {d.nom} a réalisé : {label}.")
            self.gagner(d, pts_mise, "défi Grelottine gagné")
            self.gagner(g, -pts_mise, "défi Grelottine perdu")
            if self.niveau >= 2:
                d.immunite = True
        else:
            self.dire(f"   DÉFI RATÉ : {g.nom} gagne la mise.")
            self.gagner(g, pts_mise, "défi Grelottine gagné")
            self.gagner(d, -pts_mise, "défi Grelottine perdu")
        c = analyser(des, self.niveau, self.aquitaine)
        if not sirote and not (reussi and type_ == "sirop"):
            self.dire(f"   Combinaison finale de {d.nom} : {c.libelle()}")
            self.resoudre(d, c, libre=False, grel=False)
        if not reussi and self.niveau >= 2 and c.kind == "neant":
            print("   POULETTE : le grelottin et/ou le défié peuvent crier « Elle est où la Poulette ? ».")
            print("   Le seul à crier gagne 10 pts ; si les deux crient, ils perdent 10 pts chacun.")
            qui = self.choisir_joueurs("Qui crie ? (Entrée = personne)", parmi=[g, d])
            if len(qui) == 1:
                self.gagner(qui[0], 10, "Poulette")
            else:
                for p in qui:
                    self.gagner(p, -10, "Poulette simultanée")
        return True

    def bevue(self):
        print(f"   BÉVUE : le(s) fautif(s) perdent {PENALITE_BEVUE} points.")
        qui = self.choisir_joueurs("Qui commet la bévue ? (numéro(s), Entrée pour annuler)")
        if not qui:
            return
        self.sauver_etat()
        for p in qui:
            self.bevue_a(p, "erreur de jeu")

    def chemin_png(self):
        return Path.cwd() / f"cul_de_chouette_{datetime.now():%Y-%m-%d_%Hh%M}.png"

    def exporter(self, termine):
        if not self.joueurs:
            print("   Aucun joueur : rien à enregistrer.")
            return
        chemin = exporter_png(self, self.chemin_png(), termine=termine)
        if chemin:
            print(f"   Tableau enregistré : {chemin}")

    def terminer(self, gagnant=None):
        if not self.joueurs:
            print("   Aucune partie à terminer.")
            return
        if not self.en_cours:
            print("   La partie est déjà terminée.")
            return
        print("\n" + "=" * 60)
        print("   FIN DE LA PARTIE - SCORES FINAUX")
        self.afficher_scores()
        self.gagnant = None
        if self.aquitaine:
            tot = sum(j.gorgees_bues for j in self.joueurs)
            print(f"   Gorgées bues au total : {tot}. Santé !")
        else:
            if gagnant is None:
                cand = self.actifs or self.joueurs
                gagnant = max(cand, key=lambda j: j.score)
            self.gagnant = gagnant
            print(f"   Vainqueur : {gagnant.nom} avec {gagnant.score} points. Bravo !")
        self.exporter(termine=True)
        self.en_cours = False

REGLES = [
    ("But et déroulement", """\
De 2 à 16 joueurs, 3 dés. Le premier joueur qui atteint ou dépasse 343 points gagne (343 = C-D-C, les initiales du jeu). Chacun lance un dé au départ : le plus petit score commence (égalité : on relance) et on tourne dans le sens inverse des aiguilles d'une montre.

À son tour, on lance deux dés (les chouettes), puis le troisième (le cul). En général, le lanceur marque les points de la combinaison.

Avec ce programme, le Maître du Jeu saisit les dés, puis indique qui a crié ou fait quoi : le programme annonce la combinaison, applique les points et tient le tableau des scores. « Annuler le dernier tour » corrige une erreur de saisie.

Si deux joueurs atteignent 343 en même temps, celui qui a le plus haut score gagne."""),

    ("Options choisies avant la partie", """\
SCORES NÉGATIFS
• Autorisés : un joueur qui atteint -343 est éliminé. Le Civet n'est pas limité par le score. Un défi Grelottine exige que les deux scores soient supérieurs à 0 (sinon Bévue).
• Interdits : le score ne descend jamais sous 0. Un joueur à 0 ne perd rien (même pas sur une Bévue) et la perte non payée est gagnée par chacun des autres joueurs. On a aussi besoin de 30 pts pour : obtenir ou garder une Grelottine, lancer ou subir un défi Grelottine ou une Soufflette. Un Civet ne peut pas dépasser le score du joueur ; un sirotage exige d'avoir au moins les points de la Chouette en jeu (sinon un adversaire crie « Sirop-Jeannot ! » et gagne un Contre-Sirop) ; les paris du Sirop et du Verdier demandent 5 pts.

RÈGLES À L'AQUITAINE
Le score est converti en gorgées. Pour chaque gain de points : on arrondit à la dizaine supérieure puis on divise par 10 (4 pts = 1 gorgée, 36 pts = 4 gorgées) : le joueur DONNE ces gorgées à qui il veut. Pour chaque perte, il les BOIT. La partie s'arrête quand les joueurs le décident (pas d'objectif de 343). Plus aucun minimum de points pour Grelottine, Sirop, Attrape-Oiseau, Soufflette, Civet, Achat, Verdier... Un Néant donne une Grelottine de plus (6 maximum) ; un défi Grelottine mise autant de gorgées que de Grelottines (pas de Sirop-Grelot). Nouvelle combinaison : l'EXCALIBUR (5-3-1, à 3 joueurs ou plus).

NIVEAU DE RÈGLES
★ = règles historiques ; ★★ = + Artichette, Soufflette, Suite-Velutée, Poulette, Passe-Grelot, Rigodon, Attrape-Oiseau, Contre-Sirop, Civet doublé, Cul de Chouette doublé, Achat ; ★★★ = + Bleu-Rouge, Pélican, Verdier, Jarret, Néant Soufflé."""),

    ("Combinaisons ★", """\
CHOUETTE : deux dés identiques. Points = carré du dé (1, 4, 9, 16, 25, 36). Le lanceur peut tenter un sirotage.
VELUTE : la somme de deux dés égale le 3e dé. Points = 2 x (plus grand dé)² : 3 = 18, 4 = 32, 5 = 50, 6 = 72. (1-2-3 est aussi une Suite.)
CHOUETTE-VELUTE : 1-1-2, 2-2-4 ou 3-3-6. Vaut sa Velute : le premier à taper dans ses mains en criant « Pas mou, le caillou ! » gagne les points. Égalité à l'annonce : les joueurs concernés perdent ces points. Pas de sirotage possible.
CUL DE CHOUETTE : trois dés identiques. Points = 40 + 10 x dé (50 à 100).
SUITE : trois dés qui se suivent. Tous tapent du poing sur la table en criant « Grelotte ça picote ! » : le dernier perd 10 pts. Égalité : « Sans fin, est la moisissure des bières bretonnes ! », puis un dé (le plus grand perd).
NÉANT : rien de tout ça. Le lanceur gagne une Grelottine (non cumulable)."""),

    ("Actions et défis ★", """\
GRELOTTINE : un joueur qui a une Grelottine peut défier, entre deux tours, un autre joueur qui en a une (« Grelottine ! » en le désignant). Si deux joueurs crient ensemble, le plus petit score devient le grelottin. Le grelottin choisit la combinaison à réaliser (Chouette, Velute, Chouette-Velute, Cul de Chouette ou Sirop-Grelot) et mise au maximum, du plus petit des deux scores (arrondi au supérieur) : Chouette 1/3, Velute 1/4, Cul de Chouette 1/8, Chouette-Velute 1/16, Sirop-Grelot 1/32. Le défié a 2 lancers (il s'arrête s'il réussit au premier). Réussite : il gagne la mise ; échec : il la perd. Dans tous les cas il marque les points de sa combinaison finale. La Grelottine du grelottin est dépensée. Pour le Sirop-Grelot : si le défié fait une Chouette au 2e lancer, le sirotage est obligatoire.
SIROP (sirotage) : sur une Chouette, le lanceur crie « Je sirote ! » et relance un dé. Réussite : il marque le Cul de Chouette correspondant. Échec : il perd les points de la Chouette (qu'il ne prend pas). Un échec sur 6 donne un Civet. Pendant ce temps les autres parient 5 pts sur la valeur du dé (gain 25 pts, sinon -5). Oiseaux : 1 Linotte, 2 Alouette, 3 Fauvette, 4 Mouette, 5 Bergeronnette, 6 Chouette. « Beau-Sirop ! » = parier sur la réussite ; « Couche-Sirop ! » / « File-Sirop ! » = ne pas parier.
CIVET : on l'obtient en ratant un sirotage de 6. Avant de lancer, le joueur annonce « Civet de X sur une [combinaison] ! » (mise de 1 à 102). Réussite : il gagne la mise + sa combinaison. Échec : il perd la mise mais gagne quand même sa combinaison. « Lance-Civet ! » permet de le donner à un joueur qui n'en a pas (sinon Bévue).
BÉVUE : toute erreur (mauvaise annonce, dé tombé, lancer dans le désordre...) coûte 5 pts, cumulables.
CHANTE-SLOUBI : pour entrer dans une partie commencée. Valeur = (meilleur score - 2e score) x nombre de tours / 10, maximum 228. Le nouveau chante « Sloubi 1, sloubi 2... » jusqu'à cette valeur : réussi, il démarre à 1,5 fois ce score, sinon au score seul."""),

    ("Règles ★★", """\
ARTICHETTE (4-4-3) : le lanceur gagne 16 pts en criant « Raitournelle ! », sauf si un autre lui crie « Artichette ! » en premier en le désignant : il perd alors 16 pts. Égalité : le lanceur est prioritaire. Pas de sirotage.
SOUFFLETTE (4-2-1) : le lanceur peut défier un joueur (« En garde ma mignonne ! »). Le soufflé a 3 lancers pour faire 4-2-1 : au 1er, il prend 50 pts au souffleur ; au 2e, 40 ; au 3e, 30. Échec : il perd 30 pts (gagnés par le souffleur), puis marque sa dernière combinaison.
SUITE-VELUTÉE (1-2-3) : la Suite s'applique. Si le lanceur attrape une chouette en criant « Patte de canaaard ! », il valide sa Velute (18 pts). Sinon le premier qui attrape les chouettes en criant « Velutée ! » les relance et marque la combinaison obtenue. Deux joueurs qui crient ensemble relancent chacun une chouette : les points de la combinaison sont retirés au lanceur.
POULETTE : si le défié rate un défi Grelottine par un Néant, le grelottin et le défié peuvent crier « Elle est où la Poulette ? » : le seul qui crie gagne 10 pts ; si les deux crient, ils perdent 10 pts chacun.
PASSE-GRELOT / RIGODON : celui qui a gagné un défi Grelottine est immunisé contre le suivant. Avant l'annonce de la mise, il peut crier « Passe-Grelot ! » pour renvoyer le défi à un autre joueur (3 joueurs minimum), ou « Rigodon ! » pour annuler le défi : les deux Grelottines disparaissent.
ATTRAPE-OISEAU : sur la Chouette d'un autre, un joueur peut siroter à sa place (« Attrape-Oiseau ! »). Le lanceur garde les points de sa Chouette. Réussite : l'attrapeur marque le Cul de Chouette ; échec : il perd les points de la Chouette. Priorité au premier qui attrape le dé.
CONTRE-SIROP : quand un sirotage ou un Attrape-Oiseau échoue et qu'aucun pari n'est gagné, le premier qui crie « J'apprécie les fruits au sirop ! » gagne 1/5 du Cul de Chouette visé (10, 12, 14, 16, 18, 20 pts). Égalité : les joueurs concernés perdent cette valeur. Le sirotant ne peut pas le prendre (sauf à deux joueurs).
CIVET DOUBLÉ : après l'annonce d'un Civet, un joueur qui a aussi un Civet peut crier « Civet doublé ! » : il le sacrifie et la mise est doublée (pas la combinaison).
CUL DE CHOUETTE DOUBLÉ : après un Cul de Chouette (ou un sirotage réussi), le joueur peut crier « Cul de Chouette ! » et relancer les 3 dés une seule fois, sans prendre les points avant. Nouveau Cul de Chouette : il gagne les deux. Même valeur : il remporte la partie. Échec : il est éliminé.
ACHAT : après les chouettes et avant le cul, un autre joueur peut crier « J'achète ! » (30 pts, il faut les avoir) : il lance le cul à la place du lanceur et marque la combinaison. Le lanceur ne garde que les points de sa éventuelle Chouette. Pas d'achat après une Chouette de 6, ni pendant un Civet. DOUBLE ACHAT : n'importe qui peut racheter le cul (30 pts), autant de fois qu'on veut.
GRAINES : quand un joueur se lève, il doit dire « Je ne mange pas de graines ! » avant de se rasseoir, sinon Bévue."""),

    ("Règles ★★★", """\
BLEU-ROUGE (3-4-3) : le lanceur gagne 9 pts (Chouette de 3), puis chaque joueur annonce une relance différente (somme des trois dés, de 3 à 18) et le lanceur relance les 3 dés. Le joueur dont l'annonce est exacte gagne 36 pts + 2 x la valeur + les points de la combinaison de la relance. Si personne ne trouve, aucune combinaison ne s'applique.
PÉLICAN : relance de 18 (6-6-6) pendant un Bleu-Rouge. Le premier à crier « Pélican ! » gagne 28 pts (égalité : « Passe-Montagne ! », puis « Zbradaraldjan ! », puis celui qui avait annoncé 18). Si le même joueur avait annoncé 18 : 72 + 100 + 28 = 200 pts d'un coup !
JARRET : si la relance d'un Bleu-Rouge est un Néant, le premier qui crie « Lance-Bûches ! » obtient un Jarret (non cumulable). À son tour, avant de lancer : MI-JARRET = deux lancers (il crie « Bjarret ! » pour garder le premier) ; BI-JARRET = la combinaison (et la mise du Civet) vaut le double ; LANCE-JARRET = donner son Jarret à un autre joueur.
VERDIER : quand les chouettes sont 6-4, 6-2 ou 4-2, les autres joueurs peuvent parier sur une Velute de 6 (6-4-2) en criant « Vert-Linette ! » : mise de 5 pts, gain 25 pts.
NÉANT SOUFFLÉ (1-4-6) : le premier qui crie « Mécréant ! » en se touchant le nez récupère la Grelottine (le lanceur peut participer). Avec « Je suis un misérable », personne ne la reçoit."""),

    ("Ce que le programme ne gère pas", """\
Règles ★★★★ : Flan (Double-Flan, Contre-Flan, Lance-Flan), Tichette (et Michette, Bichette, quiche), Civet-Filoché (et Civet-Filoché doublé), Cul de Chouette doublé diminué.
Détails ★★★ : Jarret-Souple, Jarret-Sifflet, Charret ; achat d'un sirotage.
Les « tris » à égalité (cris successifs, dés de départage) sont arbitrés par le Maître du Jeu : il indique simplement le résultat final."""),

    ("Conseils", """\
• Mettez-vous d'accord avant la partie sur ce qui est une Bévue.
• En cas de litige, un lancer de dé tranche : le plus petit score l'emporte.
• Il est possible d'annoncer une combinaison pendant que les dés roulent (« préventive ») : si elle échoue, c'est une Bévue.
• Si un dé tombe de la table : on relance les deux chouettes, ou le cul seul s'il est le seul à être tombé.
• Par équipes (« doublette ») : les points sont communs, mais chaque défi doit être relevé par le joueur concerné.

Source des règles : Wikilivres, « Boîte à jeux/Le cul de chouette » (texte résumé et reformulé)."""),
]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    Jeu().menu()


if __name__ == "__main__":
    main()
