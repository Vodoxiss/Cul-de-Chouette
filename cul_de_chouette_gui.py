import importlib
import re
import subprocess
import sys
import traceback
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

import cul_de_chouette as cdc

APP = None   

BRUN, BRUN_CLAIR = "#5B3A1E", "#8B5E34"
CREME, SABLE, OR = "#FBF5E6", "#F3E8CF", "#F4D03F"
VERT, ROUGE = "#2E7D32", "#B3261E"


def nettoyer(texte):
    texte = re.sub(r"\s*\(.*\)(\s*:)?\s*$", lambda m: m.group(1) or "", texte)
    return re.sub(r"\s+", " ", texte).strip()

class Dialogue(tk.Toplevel):

    def __init__(self, titre, question="", annonce=None, fermable=False):
        super().__init__(APP)
        self.title(titre or "Cul de Chouette")
        self.configure(bg=CREME)
        self.transient(APP)
        self.resizable(False, False)
        self.resultat = None
        self.protocol("WM_DELETE_WINDOW", self.fermer if fermable else self.bell)
        corps = tk.Frame(self, bg=CREME, padx=18, pady=14)
        corps.pack(fill="both", expand=True)
        if annonce is None:
            annonce = APP.annonce()
        if annonce:
            tk.Label(corps, text=annonce, bg=SABLE, fg=BRUN, justify="left", anchor="w",
                     wraplength=520, padx=10, pady=8).pack(fill="x", pady=(0, 10))
        if question:
            tk.Label(corps, text=question, bg=CREME, fg=BRUN, justify="left", anchor="w",
                     wraplength=520, font=("TkDefaultFont", 12, "bold")).pack(fill="x", pady=(0, 8))
        self.zone = tk.Frame(corps, bg=CREME)
        self.zone.pack(fill="x")
        self.barre = tk.Frame(corps, bg=CREME)
        self.barre.pack(fill="x", pady=(14, 0))

    def bouton(self, texte, commande, **kw):
        b = ttk.Button(self.barre, text=texte, command=commande, **kw)
        b.pack(side="right", padx=4)
        return b

    def terminer(self, resultat=None):
        self.resultat = resultat
        self.destroy()

    def fermer(self):
        self.terminer(None)

    def montrer(self):
        self.update_idletasks()
        x = APP.winfo_rootx() + (APP.winfo_width() - self.winfo_reqwidth()) // 2
        y = APP.winfo_rooty() + (APP.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.wait_visibility()
        self.grab_set()
        self.focus_set()
        self.wait_window(self)
        return self.resultat


class DialogueDes(Dialogue):

    def __init__(self, titre, question, labels, extras=(), fermable=False):
        super().__init__(titre, question, fermable=fermable)
        self.labels = labels
        self.vars = [tk.IntVar(value=0) for _ in labels]
        seul = len(labels) == 1
        for i, nom in enumerate(labels):
            ligne = tk.Frame(self.zone, bg=CREME)
            ligne.pack(fill="x", pady=3)
            tk.Label(ligne, text=nom, width=11, anchor="w", bg=CREME, fg=BRUN,
                     font=("TkDefaultFont", 11, "bold")).pack(side="left")
            for v in range(1, 7):
                tk.Radiobutton(ligne, text=str(v), value=v, variable=self.vars[i],
                               indicatoron=False, width=3, bg=SABLE, selectcolor=OR,
                               activebackground=OR, font=("TkDefaultFont", 16, "bold"),
                               command=self.valider if seul else self.maj).pack(side="left", padx=2)
        self.resume = tk.Label(self.zone, text="", bg=CREME, fg=BRUN_CLAIR, font=("TkDefaultFont", 11))
        self.resume.pack(anchor="w", pady=(8, 0))
        self.ok = self.bouton("Valider", self.valider, state="disabled")
        if fermable:
            self.bouton("Fermer", self.fermer)
        for code, texte in extras:
            self.bouton(texte, lambda c=code: self.terminer(c))
        self.bind("<Key>", self.touche)
        self.bind("<Return>", lambda e: self.valider())
        self.maj()

    def touche(self, event):
        if event.char and event.char in "123456":
            for v in self.vars:
                if v.get() == 0:
                    v.set(int(event.char))
                    break
            if len(self.vars) == 1:
                self.valider()
                return
        elif event.keysym == "BackSpace":
            for v in reversed(self.vars):
                if v.get():
                    v.set(0)
                    break
        self.maj()

    def maj(self):
        vals = [v.get() for v in self.vars]
        complet = all(vals)
        self.ok.state(["!disabled"] if complet else ["disabled"])
        txt = " · ".join(str(x) if x else "–" for x in vals)
        if complet and len(vals) == 3:
            jeu = APP.jeu
            txt += "   =>   " + cdc.analyser(vals, jeu.niveau, jeu.aquitaine).libelle()
        self.resume.config(text="Dés : " + txt + ("" if complet or len(vals) == 1
                                                  else "     (clavier : tape les chiffres)"))

    def valider(self):
        vals = [v.get() for v in self.vars]
        if all(vals):
            self.terminer(vals)


def ask_yes_no(question):
    d = Dialogue("Question", question.strip())
    d.bouton("Oui", lambda: d.terminer(True))
    d.bouton("Non", lambda: d.terminer(False))
    for k in ("o", "y"):
        d.bind(f"<Key-{k}>", lambda e: d.terminer(True))
    d.bind("<Key-n>", lambda e: d.terminer(False))
    return bool(d.montrer())


def ask_int(question, lo, hi, vide_ok=False):
    d = Dialogue("Valeur", nettoyer(question), fermable=vide_ok)
    if hi - lo + 1 <= 7:                         
        ligne = tk.Frame(d.zone, bg=CREME)
        ligne.pack()
        for n in range(lo, hi + 1):
            txt = str(n)
            if (lo, hi) == (1, 6):
                txt += "\n" + cdc.OISEAUX[n]
            ttk.Button(ligne, text=txt, width=9, command=lambda n=n: d.terminer(n)).pack(
                side="left", padx=3)
            d.bind(f"<Key-{n}>", lambda e, n=n: d.terminer(n))
        if vide_ok:
            d.bouton("Aucun", lambda: d.terminer(None))
        return d.montrer()
    var = tk.StringVar(value=str(lo))
    ligne = tk.Frame(d.zone, bg=CREME)
    ligne.pack(anchor="w")
    sb = ttk.Spinbox(ligne, from_=lo, to=hi, textvariable=var, width=8, font=("TkDefaultFont", 14))
    sb.pack(side="left")
    tk.Label(ligne, text=f"  (de {lo} à {hi})", bg=CREME, fg=BRUN_CLAIR).pack(side="left")
    err = tk.Label(d.zone, text="", bg=CREME, fg=ROUGE)
    err.pack(anchor="w")

    def ok(*_):
        try:
            v = int(var.get())
        except ValueError:
            v = None
        if v is not None and lo <= v <= hi:
            d.terminer(v)
        else:
            err.config(text=f"Entre un nombre entre {lo} et {hi}.")
    d.bouton("Valider", ok)
    sb.bind("<Return>", ok)
    d.bind("<Return>", ok)
    sb.focus_set()
    return d.montrer()


def choisir_option(titre, options):
    d = Dialogue("Choix", nettoyer(titre))
    var = tk.StringVar(value="")
    for cle, label in options:
        tk.Radiobutton(d.zone, text=label, value=cle, variable=var, bg=CREME, anchor="w",
                       justify="left", wraplength=500, activebackground=CREME,
                       font=("TkDefaultFont", 12)).pack(fill="x", pady=2)

    def ok():
        if var.get():
            d.terminer(var.get())
        else:
            d.bell()
    d.bouton("Valider", ok)
    return d.montrer()


def saisir_lancer(invite, labels, extras=()):
    d = DialogueDes("Lancer de dés", nettoyer(invite), labels, extras)
    return d.montrer()


cdc.ask_yes_no = ask_yes_no
cdc.ask_int = ask_int
cdc.choisir_option = choisir_option
cdc.saisir_lancer = saisir_lancer


def dialogue_nouvelle_partie():
    d = Dialogue("Nouvelle partie", "Joueurs (2 minimum) et options de la partie :",
                 annonce="", fermable=True)
    noms = []
    saisie = tk.StringVar()
    ligne = tk.Frame(d.zone, bg=CREME)
    ligne.pack(fill="x")
    entree = ttk.Entry(ligne, textvariable=saisie, font=("TkDefaultFont", 13))
    entree.pack(side="left", fill="x", expand=True)
    liste = tk.Listbox(d.zone, height=6, font=("TkDefaultFont", 13), activestyle="none")
    liste.pack(fill="x", pady=8)

    def maj():
        liste.delete(0, "end")
        for n in noms:
            liste.insert("end", n)
        go.state(["!disabled"] if len(noms) >= 2 else ["disabled"])

    def ajouter(*_):
        n = saisie.get().strip()
        if n and n.lower() not in (x.lower() for x in noms):
            noms.append(n)
            saisie.set("")
            maj()
        elif n:
            d.bell()

    def retirer():
        for i in reversed(liste.curselection()):
            del noms[i]
        maj()
    ttk.Button(ligne, text="Ajouter", command=ajouter).pack(side="left", padx=(6, 0))
    ttk.Button(d.zone, text="Retirer le joueur sélectionné", command=retirer).pack(anchor="w")

    cadre = tk.LabelFrame(d.zone, text=" Options de la partie ", bg=CREME, fg=BRUN, padx=10, pady=6)
    cadre.pack(fill="x", pady=(12, 0))
    neg = tk.BooleanVar(value=True)
    aq = tk.BooleanVar(value=False)
    niv = tk.IntVar(value=3)
    cb_neg = tk.Checkbutton(cadre, text="Autoriser les scores négatifs (élimination à -343)",
                            variable=neg, bg=CREME, activebackground=CREME, anchor="w")
    cb_neg.pack(fill="x")
    cb_aq = tk.Checkbutton(cadre, text="Règles à l'Aquitaine (le score est converti en gorgées)",
                           variable=aq, bg=CREME, activebackground=CREME, anchor="w")
    cb_aq.pack(fill="x")

    def maj_aq(*_):
        if aq.get():
            neg.set(True)
            cb_neg.config(state="disabled")
        else:
            cb_neg.config(state="normal")
    aq.trace_add("write", maj_aq)
    tk.Label(cadre, text="Niveau de règles :", bg=CREME, fg=BRUN, anchor="w",
             font=("TkDefaultFont", 10, "bold")).pack(fill="x", pady=(6, 0))
    for v, t in ((1, "★  Règles historiques (Chouette, Velute, Suite, Néant, Sirop, Civet, Grelottine)"),
                 (2, "★★  + Artichette, Soufflette, Attrape-Oiseau, Achat, Cul de Chouette doublé..."),
                 (3, "★★★  Complet : + Bleu-Rouge, Pélican, Verdier, Jarret, Néant Soufflé")):
        tk.Radiobutton(cadre, text=t, value=v, variable=niv, bg=CREME, activebackground=CREME,
                       anchor="w").pack(fill="x")

    def commencer():
        d.terminer({"noms": list(noms), "negatifs": neg.get(), "aquitaine": aq.get(),
                    "niveau": niv.get()})
    go = d.bouton("Commencer", commencer, state="disabled")
    d.bouton("Annuler", d.fermer)
    entree.bind("<Return>", ajouter)
    entree.focus_set()
    return d.montrer()


class FenetreRegles(tk.Toplevel):
    def __init__(self):
        super().__init__(APP)
        self.title("Règles du Cul de Chouette")
        self.geometry("980x680")
        self.configure(bg=CREME)
        gauche = tk.Frame(self, bg=SABLE)
        gauche.pack(side="left", fill="y")
        tk.Label(gauche, text="Sommaire", bg=SABLE, fg=BRUN, font=("TkDefaultFont", 12, "bold")).pack(
            padx=10, pady=(10, 4), anchor="w")
        self.liste = tk.Listbox(gauche, width=30, activestyle="none", font=("TkDefaultFont", 11),
                                exportselection=False, bg=SABLE, relief="flat")
        self.liste.pack(fill="y", expand=True, padx=8, pady=4)
        zone = tk.Frame(self, bg=CREME)
        zone.pack(side="left", fill="both", expand=True)
        self.texte = tk.Text(zone, wrap="word", bg="white", relief="flat", padx=16, pady=12,
                             font=("TkDefaultFont", 11), spacing2=2, spacing3=4)
        defil = ttk.Scrollbar(zone, command=self.texte.yview)
        self.texte.configure(yscrollcommand=defil.set)
        defil.pack(side="right", fill="y")
        self.texte.pack(side="left", fill="both", expand=True)
        self.texte.tag_configure("titre", font=("TkDefaultFont", 15, "bold"), foreground=BRUN,
                                 spacing1=14, spacing3=6)
        self.texte.tag_configure("rub", font=("TkDefaultFont", 11, "bold"), foreground=BRUN_CLAIR)
        for i, (titre, corps) in enumerate(cdc.REGLES):
            self.liste.insert("end", titre)
            self.texte.mark_set(f"s{i}", "end-1c")
            self.texte.mark_gravity(f"s{i}", "left")
            self.texte.insert("end", titre + "\n", "titre")
            for para in corps.split("\n"):
                tete, sep, reste = para.partition(" : ")
                mot = re.split(r"[ /(]", tete)[0]
                if sep and len(tete) < 55 and len(mot) >= 3 and mot.isupper():
                    self.texte.insert("end", tete + " :", "rub")
                    self.texte.insert("end", " " + reste + "\n")
                elif para.isupper() and para.strip():
                    self.texte.insert("end", para + "\n", "rub")
                else:
                    self.texte.insert("end", para + "\n")
        self.texte.configure(state="disabled")
        self.liste.bind("<<ListboxSelect>>", self.aller)
        self.bind("<Escape>", lambda e: self.destroy())

    def aller(self, _):
        sel = self.liste.curselection()
        if sel:
            self.texte.see("end")
            self.texte.yview(f"s{sel[0]}")

def pillow_pret():
    try:
        import PIL.Image
        import PIL.ImageDraw
        import PIL.ImageFont  
        return True
    except Exception as e:
        erreur = f"{type(e).__name__}: {e}"
    if not messagebox.askyesno(
            "Pillow introuvable",
            "Pillow n'est pas disponible pour le Python qui lance ce programme :\n\n"
            f"{sys.executable}\n\nErreur : {erreur}\n\n"
            "(Cela arrive quand pip a installé Pillow pour un autre Python.)\n\n"
            "L'installer maintenant pour ce Python ?", parent=APP):
        return False
    APP.config(cursor="watch")
    APP.update()
    res = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pillow"],
                         capture_output=True, text=True,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    APP.config(cursor="")
    importlib.invalidate_caches()
    try:
        import PIL.Image  
        import PIL.ImageDraw  
        import PIL.ImageFont  
        return True
    except Exception as e:
        messagebox.showerror(
            "Installation impossible",
            f"Python utilisé : {sys.executable}\nErreur : {type(e).__name__}: {e}\n\n"
            "Sortie de pip :\n" + (res.stdout + res.stderr)[-1000:] +
            "\n\nEssaie dans une console :\n"
            f'"{sys.executable}" -m pip install pillow', parent=APP)
        return False



class JeuGUI(cdc.Jeu):
    def afficher_scores(self):
        APP.rafraichir()

    def afficher_journal(self):
        pass

    def afficher_regles(self):
        APP.ouvrir_regles()

    def lire_chouettes(self, j):
        while True:
            extras = [("undo", "Annuler le dernier tour")] if self.etats else []
            d = DialogueDes(f"Chouettes de {j.nom}", f"Quelles sont les chouettes de {j.nom} ?",
                            cdc.LABELS2, extras, fermable=True)
            r = d.montrer()
            if r is None:
                raise cdc.RetourMenu
            if r == "undo":
                if self.annuler():
                    raise cdc.Recommencer
                continue
            return r

    def choisir_joueurs(self, question, parmi=None, un_seul=False):
        parmi = parmi if parmi is not None else self.actifs
        if not parmi:
            return []
        d = Dialogue("Choix des joueurs", nettoyer(question))
        police = ("TkDefaultFont", 12)
        if un_seul:
            var = tk.IntVar(value=-1)
            for i, p in enumerate(parmi):
                tk.Radiobutton(d.zone, text=f"{p.nom}   ({p.score} pts)", value=i, variable=var,
                               bg=CREME, anchor="w", activebackground=CREME, font=police).pack(
                    fill="x", pady=2)

            def valider():
                if var.get() < 0:
                    d.bell()
                else:
                    d.terminer([parmi[var.get()]])
        else:
            cases = [tk.BooleanVar() for _ in parmi]
            for p, v in zip(parmi, cases):
                tk.Checkbutton(d.zone, text=f"{p.nom}   ({p.score} pts)", variable=v, bg=CREME,
                               anchor="w", activebackground=CREME, font=police).pack(fill="x", pady=2)
            tk.Label(d.zone, text="Plusieurs joueurs possibles (ex. égalité).", bg=CREME,
                     fg=BRUN_CLAIR).pack(anchor="w", pady=(6, 0))

            def valider():
                d.terminer([p for p, v in zip(parmi, cases) if v.get()])
        d.bouton("Valider", valider)
        d.bouton("Personne", lambda: d.terminer([]))
        return d.montrer() or []

    def exporter(self, termine):
        if not self.joueurs or not pillow_pret():
            return
        defaut = f"cul_de_chouette_{datetime.now():%Y-%m-%d_%Hh%M}.png"
        chemin = filedialog.asksaveasfilename(
            parent=APP, title="Enregistrer le tableau des scores", defaultextension=".png",
            initialfile=defaut, filetypes=[("Image PNG", "*.png")])
        if not chemin:
            print("   Export annulé.")
            return
        res = cdc.exporter_png(self, chemin, termine=termine)
        if res:
            print(f"   Tableau enregistré : {res}")
            messagebox.showinfo("Tableau enregistré", f"Le tableau des scores a été enregistré :\n{res}",
                                parent=APP)
        else:
            messagebox.showerror("Export impossible", "L'image n'a pas pu être créée.", parent=APP)


class Sortie:

    def write(self, s):
        try:
            APP.ecrire(s)
        except tk.TclError:
            pass

    def flush(self):
        pass

class App(tk.Tk):
    def __init__(self):
        global APP
        super().__init__()
        APP = self
        self.title("Cul de Chouette V2.0 - Maître du Jeu (by Vodoxiss)")
        self.geometry("1280x740")
        self.minsize(1120, 580)
        self.configure(bg=CREME)
        self.tampon = ""
        self._ligne = ""
        self.fenetre_regles = None
        self.jeu = JeuGUI()
        self.construire()
        sys.stdout = Sortie()
        self.protocol("WM_DELETE_WINDOW", self.quitter)
        self.rafraichir()
        print("Bienvenue ! Clique sur « Nouvelle partie » pour choisir les joueurs et les options.")
        print("Le bouton « Règles » affiche toutes les règles du jeu.")

    def report_callback_exception(self, exc, val, tb):
        messagebox.showerror("Erreur", "".join(traceback.format_exception(exc, val, tb))[-1500:])

    def construire(self):
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("TButton", padding=6)
        st.configure("Treeview", rowheight=40, font=("TkDefaultFont", 13), background=CREME,
                     fieldbackground=CREME)
        st.configure("Treeview.Heading", font=("TkDefaultFont", 12, "bold"), background=BRUN_CLAIR,
                     foreground="white")
        st.map("Treeview", background=[("selected", SABLE)], foreground=[("selected", "black")])
        st.configure("Gros.TButton", font=("TkDefaultFont", 14, "bold"), padding=10)

        haut = tk.Frame(self, bg=BRUN)
        haut.pack(fill="x")
        tk.Label(haut, text="CUL DE CHOUETTE", bg=BRUN, fg=CREME,
                 font=("TkDefaultFont", 24, "bold")).pack(side="left", padx=18, pady=10)
        self.statut = tk.Label(haut, text="", bg=BRUN, fg="#E8D5B0", font=("TkDefaultFont", 12),
                               justify="right")
        self.statut.pack(side="right", padx=18)

        barre = tk.Frame(self, bg=SABLE, pady=6)
        barre.pack(fill="x")
        self.boutons = {}

        def ajouter_bouton(cle, texte, cmd):
            b = ttk.Button(barre, text=texte, command=cmd)
            b.pack(side="left", padx=4)
            self.boutons[cle] = b
        ajouter_bouton("nouvelle", "Nouvelle partie", self.nouvelle_partie)
        ajouter_bouton("regles", "Règles", self.ouvrir_regles)
        ajouter_bouton("joueur", "Inscrire un joueur", self.inscrire)
        self.menu_actions = tk.Menu(self, tearoff=0)
        self.menu_actions.add_command(label="Bévue (-5 pts)", command=self.bevue)
        self.menu_actions.add_command(label="Défi Grelottine", command=self.defi)
        self.menu_actions.add_command(label="Lance-Civet (donner un Civet)", command=self.lance_civet)
        mb = ttk.Menubutton(barre, text="Actions  ▾", menu=self.menu_actions)
        mb.pack(side="left", padx=4)
        self.boutons["actions"] = mb
        ajouter_bouton("annuler", "Annuler le dernier tour", self.annuler)
        ajouter_bouton("exporter", "Exporter en PNG", lambda: self.jeu.exporter(termine=False))
        ajouter_bouton("terminer", "Terminer la partie + PNG", self.terminer)

        corps = tk.Frame(self, bg=CREME)
        corps.pack(fill="both", expand=True, padx=14, pady=12)
        corps.columnconfigure(0, weight=0, minsize=720)
        corps.columnconfigure(1, weight=1)
        corps.rowconfigure(0, weight=1)

        gauche = tk.Frame(corps, bg=CREME)
        gauche.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.banniere = tk.Label(gauche, text="", bg=SABLE, fg=BRUN, wraplength=680, height=2,
                                 font=("TkDefaultFont", 13, "bold"), pady=6)
        self.banniere.pack(fill="x")
        self.banniere.bind("<Configure>", lambda e: self.banniere.config(wraplength=e.width - 20))
        self.lancer = ttk.Button(gauche, text="", style="Gros.TButton", command=self.lancer_tour)
        self.lancer.pack(fill="x", pady=10)
        cols = ("rang", "joueur", "score", "reste", "don", "bue", "objets")
        self.tree = ttk.Treeview(gauche, columns=cols, show="headings", selectmode="none")
        for c, titre, larg, ancre in (("rang", "#", 45, "center"), ("joueur", "Joueur", 190, "w"),
                                      ("score", "Score", 80, "center"), ("reste", "Reste", 80, "center"),
                                      ("don", "Données", 90, "center"), ("bue", "Bues", 70, "center"),
                                      ("objets", "Objets", 230, "w")):
            self.tree.heading(c, text=titre)
            self.tree.column(c, width=larg, anchor=ancre)
        self.tree.tag_configure("courant", background=OR)
        self.tree.tag_configure("elimine", foreground="#999999")
        self.tree.pack(fill="both", expand=True)

        droite = tk.Frame(corps, bg=CREME)
        droite.grid(row=0, column=1, sticky="nsew")
        tk.Label(droite, text="Journal du Maître du Jeu", bg=CREME, fg=BRUN,
                 font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
        zone = tk.Frame(droite)
        zone.pack(fill="both", expand=True)
        self.log = tk.Text(zone, width=30, wrap="word", state="disabled", bg="white", relief="flat",
                           font=("TkDefaultFont", 11), padx=8, pady=6)
        defil = ttk.Scrollbar(zone, command=self.log.yview)
        self.log.configure(yscrollcommand=defil.set)
        defil.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        self.log.tag_configure("combo", font=("TkDefaultFont", 12, "bold"), foreground=BRUN, spacing1=6)
        self.log.tag_configure("tour", font=("TkDefaultFont", 11, "bold"), foreground=BRUN_CLAIR)
        self.log.tag_configure("gain", foreground=VERT)
        self.log.tag_configure("perte", foreground=ROUGE)
        self.log.tag_configure("sep", foreground="#BBBBBB")

    def ecrire(self, s):
        self.tampon += s
        self._ligne += s
        while "\n" in self._ligne:
            ligne, self._ligne = self._ligne.split("\n", 1)
            self.ajouter_ligne(ligne)

    def ajouter_ligne(self, ligne):
        txt = ligne.rstrip()
        tag = ()
        if txt and set(txt) == {"="}:
            txt, tag = "─" * 34, ("sep",)
        elif ">>" in txt:
            m = re.search(r"([+-]\d+) pts", txt)
            tag = ("gain",) if (m and m.group(1).startswith("+")) else ("perte",)
            txt = txt.replace(">>", "•", 1)
        elif "=>" in txt:
            tag = ("combo",)
            self.banniere.config(text=txt.strip())
        elif txt.startswith("TOUR"):
            tag = ("tour",)
        self.log.configure(state="normal")
        self.log.insert("end", txt + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def annonce(self):
        lignes = [l.strip() for l in self.tampon.split("\n")
                  if l.strip() and set(l.strip()) != {"="}]
        self.tampon = ""
        return "\n".join(lignes[-8:])

    def joueur_courant(self):
        j = self.jeu
        if not (j.en_cours and j.joueurs):
            return None
        i = j.idx
        for _ in range(len(j.joueurs)):
            if not j.joueurs[i].elimine:
                return j.joueurs[i]
            i = (i + 1) % len(j.joueurs)
        return None

    def rafraichir(self):
        j = self.jeu
        self.tree["displaycolumns"] = (("rang", "joueur", "score", "don", "bue", "objets") if j.aquitaine
                                       else ("rang", "joueur", "score", "reste", "objets"))
        self.tree.delete(*self.tree.get_children())
        courant = self.joueur_courant()
        for rang, p in cdc.classer(j.joueurs):
            tags = ("courant",) if p is courant else (("elimine",) if p.elimine else ())
            self.tree.insert("", "end", tags=tags, values=(
                rang, p.nom + ("   (à jouer)" if p is courant else ""), p.score,
                max(0, cdc.OBJECTIF - p.score), p.gorgees_donnees, p.gorgees_bues, cdc.objets(p)))
        jouable = j.en_cours and len(j.actifs) >= 2
        if jouable:
            self.lancer.config(text=f"Saisir les chouettes de {courant.nom}")
            ligne2 = ("Règles à l'Aquitaine" if j.aquitaine else
                      f"objectif {cdc.OBJECTIF} pts - scores négatifs " + ("autorisés" if j.negatifs else "interdits"))
            self.statut.config(text=f"Tour {j.tour + 1}  -  règles {'★' * j.niveau}\n{ligne2}")
        else:
            self.lancer.config(text="Saisir les chouettes")
            self.statut.config(text="Partie terminée" if j.joueurs and not j.en_cours
                               else "Aucune partie en cours")
        etat = lambda ok: ["!disabled"] if ok else ["disabled"]
        self.lancer.state(etat(jouable))
        self.boutons["actions"].state(etat(j.en_cours and j.joueurs))
        self.boutons["annuler"].state(etat(j.etats and j.en_cours))
        self.boutons["terminer"].state(etat(j.en_cours and j.joueurs))
        self.boutons["exporter"].state(etat(j.joueurs))

    def ouvrir_regles(self):
        if self.fenetre_regles is not None and self.fenetre_regles.winfo_exists():
            self.fenetre_regles.deiconify()
            self.fenetre_regles.lift()
            return
        self.fenetre_regles = FenetreRegles()

    def nouvelle_partie(self):
        if self.jeu.en_cours and self.jeu.joueurs and not messagebox.askyesno(
                "Nouvelle partie", "Une partie est en cours. L'abandonner ?", parent=self):
            return
        opts = dialogue_nouvelle_partie()
        if not opts:
            return
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.banniere.config(text="")
        self.tampon = ""
        self.jeu.nouvelle(opts["noms"], opts["negatifs"], opts["aquitaine"], opts["niveau"])
        self.rafraichir()

    def inscrire(self):
        nom = simpledialog.askstring("Inscrire un joueur", "Nom du joueur :", parent=self)
        if not nom or not nom.strip():
            return
        if not self.jeu.en_cours:
            self.jeu.reset()
            self.jeu.en_cours = True
        self.tampon = ""
        if not self.jeu.inscrire(nom.strip()):
            messagebox.showwarning("Inscription impossible",
                                   "Le joueur n'a pas pu être inscrit (nom déjà pris ou Sloubi trop élevé).\n"
                                   "Voir le journal.", parent=self)
        self.rafraichir()

    def lancer_tour(self):
        j = self.jeu
        if not (j.en_cours and len(j.actifs) >= 2):
            return
        self.tampon = ""
        try:
            j.tour_suivant()
        except (cdc.RetourMenu, cdc.Recommencer):
            self.rafraichir()
            return
        self.rafraichir()
        j.verifier_victoire()
        self.rafraichir()

    def bevue(self):
        self.tampon = ""
        self.jeu.bevue()
        self.rafraichir()

    def defi(self):
        self.tampon = ""
        self.jeu.defi_manuel()
        self.rafraichir()
        self.jeu.verifier_victoire()
        self.rafraichir()

    def lance_civet(self):
        self.tampon = ""
        self.jeu.lance_civet()
        self.rafraichir()

    def annuler(self):
        self.jeu.annuler()
        self.rafraichir()

    def terminer(self):
        if not self.jeu.en_cours:
            return
        if not messagebox.askyesno("Terminer la partie", "Terminer la partie et enregistrer le "
                                   "tableau des scores en .png ?", parent=self):
            return
        self.tampon = ""
        self.jeu.terminer()
        self.rafraichir()

    def quitter(self):
        if self.jeu.en_cours and self.jeu.joueurs and not messagebox.askyesno(
                "Quitter", "Une partie est en cours. Quitter quand même ?", parent=self):
            return
        sys.stdout = sys.__stdout__
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
