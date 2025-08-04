import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
from tkcalendar import DateEntry

# Import the main conversion function and constants
from .main import main, CHOIX_OPTIM_VALUES
from . import utils
from .mapper import DEFAULT_BATTERY_PROFILE, DATA_DIR as MAPPER_DATA_DIR

# Mapping of field keys to expected input types for hints
TYPE_HINTS = {
    "resultat": "path",
    "battery_profile_path": "path",
    "donnees_camions_path": "path",
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
    "projection": "int",
    "soc_cible": "int",
    "infrastructure_path": "path",
    "marge_securite": "int",
    "marge_prechauffage": "int",
    "diminution_soc": "int",
    "pas_de_temps": "int",
    "temps_chargement": "int",
    "temps_dechargement": "int",
    "maximum_exec_temps": "int",
    "axe_optim_degrade": "list[int]",
    "choix_optim": "str",
    "output": "path",
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("X2J")
        self.option_add("*Font", ("Segoe UI", 10))
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", padding=2)
        style.configure("TButton", padding=4)

        # Frame principal
        self.main = ttk.Frame(self, padding=20)
        self.main.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)

        # Barre d'outils (réservée si besoin)
        self._create_toolbar()
        # Notebook pour onglets
        self._create_notebook()
        # Menu en haut
        self._create_menu()

    def _create_toolbar(self):
        self.toolbar = ttk.Frame(self.main)
        self.toolbar.pack(side="top", fill="x", pady=(0, 10))

    def _create_notebook(self):
        # Création du widget Notebook
        self.notebook = ttk.Notebook(self.main)
        self.notebook.pack(fill="both", expand=True)

        # Groupes de champs
        groups = [
            (
                "Fichiers",
                [
                    ("Resultat (.xlsx)", "resultat", "file_input"),
                    ("Profil Batterie (.xlsx)", "battery_profile_path", "file_input"),
                    ("Données Camions (.xlsx)", "donnees_camions_path", "file_input"),
                    ("Infratructure", "infrastructure_path", "file_input"),
                    ("Start Date", "start", "date"),
                    ("End Date", "end", "date"),
                    ("Maximum Exec Temps", "maximum_exec_temps", "entry"),
                    ("Output (.json)", "output", "file_output"),
                ],
            ),
            (
                "Simulation",
                [
                    ("Choix Optim", "choix_optim", "combo", CHOIX_OPTIM_VALUES),
                    ("Projection", "projection", "combo", [0, 2, 5, 10]),
                    ("Marge Sécurité", "marge_securite", "entry"),
                    ("Marge Préchauffage", "marge_prechauffage", "entry"),
                    ("Temps Chargement", "temps_chargement", "entry"),
                    ("Temps Déchargement", "temps_dechargement", "entry"),
                    ("Axe Optim Degrade", "axe_optim_degrade", "listorder"),
                    ("Pas de Temps", "pas_de_temps", "entry"),

                ],
            ),
            (
                "Infrastructure",
                [
                    ("SOC Cible", "soc_cible", "entry"),
                    ("Diminution SOC", "diminution_soc", "entry"),
                ],
            ),
        ]

        self.widgets = {}
        default_values = self._get_default_values()

        for group_name, params in groups:
            frame = ttk.Frame(self.notebook, padding=(10, 10))
            frame.columnconfigure(1, weight=1)
            self.notebook.add(frame, text=group_name)

            for i, (label_text, key, wtype, *extra) in enumerate(params):
                ttk.Label(frame, text=label_text).grid(row=i, column=0, sticky="e", padx=5, pady=3)
                widget = self._create_widget(frame, wtype, key, extra, default_values)
                widget.grid(row=i, column=1, sticky="w", padx=5, pady=3)
                hint_btn = ttk.Button(frame, text="?", width=2, command=lambda k=key: self._show_hint(k))
                hint_btn.grid(row=i, column=2, sticky="w", padx=5)
                self.widgets[key] = widget

        ttk.Button(self.main, text="Convert", command=self._run_conversion).pack(pady=15)

    def _create_widget(self, parent, wtype, key, extra, defaults):
        # Widgets pour fichier
        if wtype in ("file_input", "file_output"):
            frame = ttk.Frame(parent)
            entry = ttk.Entry(frame, width=30)
            entry.pack(side="left", fill="x", expand=True)
            text = "Browse" if wtype == "file_input" else "Save"
            btn = ttk.Button(frame, text=text, command=lambda k=key: self._browse_file(k))
            btn.pack(side="left", padx=5)
            if defaults.get(key):
                entry.insert(0, defaults[key])
            frame.widget = entry
            return frame

        # Widget date
        if wtype == "date":
            widget = DateEntry(
                parent,
                width=12,
                background="darkblue",
                foreground="white",
                borderwidth=2,
                date_pattern="y-mm-dd",
            )
            if defaults.get(key):
                widget.set_date(defaults[key])
            return widget

        # Combo
        if wtype == "combo":
            values = extra[0]
            widget = ttk.Combobox(parent, values=values, state="readonly", width=10)
            default = defaults.get(key, values[0])
            try:
                widget.current(values.index(default))
            except ValueError:
                widget.current(0)
            return widget

        # Listorder
        if wtype == "listorder":
            frame = ttk.Frame(parent)
            listbox = tk.Listbox(frame, height=3, exportselection=False, width=5)
            listbox.pack(side="left")
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(side="left", padx=5)
            ttk.Button(btn_frame, text="↑", width=2, command=lambda lb=listbox: self._move_list_item(lb, -1)).pack(fill="x")
            ttk.Button(btn_frame, text="↓", width=2, command=lambda lb=listbox: self._move_list_item(lb, 1)).pack(fill="x")
            for v in defaults.get(key, []):
                listbox.insert("end", v)
            frame.widget = listbox
            return frame

        # Entrée texte
        widget = ttk.Entry(parent, width=20)
        if defaults.get(key) is not None:
            widget.insert(0, str(defaults[key]))
        return widget

    def _get_default_values(self):
        return {
            'resultat': str(utils.DEFAULT_RESULTAT_SIMU),
            'battery_profile_path': str(DEFAULT_BATTERY_PROFILE),
            'donnees_camions_path': str(MAPPER_DATA_DIR / 'donnees_camions.xlsx'),
            'projection': 0,
            'pas_de_temps': 15,
            'temps_chargement': 30,
            'temps_dechargement': 45,
            'soc_cible': 100,
            'marge_securite': 15,
            'marge_prechauffage': 30,
            'diminution_soc': 5,
            'maximum_exec_temps': 10,
            'axe_optim_degrade': [1,2,3],
            'choix_optim': CHOIX_OPTIM_VALUES[0],
        }

    def _browse_file(self, key: str):
        if key == 'output':
            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")],
                title="Select output JSON file"
            )
        else:
            if key == 'infrastructure_path':
                filetypes = [("JSON/YAML", "*.json *.yaml *.yml")]
            else:
                filetypes = [("Excel Files", "*.xlsx *.xls")]
            path = filedialog.askopenfilename(
                filetypes=filetypes,
                title="Select file"
            )
        if path:
            widget = self.widgets[key]
            entry = getattr(widget, 'widget', widget)
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def _show_hint(self, key: str) -> None:
        hint = TYPE_HINTS.get(key)
        if hint:
            messagebox.showinfo("Expected type", hint)

    def _move_list_item(self, listbox: tk.Listbox, direction: int) -> None:
        selection = listbox.curselection()
        if not selection:
            return
        index = selection[0]
        new_index = index + direction
        if new_index < 0 or new_index >= listbox.size():
            return
        value = listbox.get(index)
        listbox.delete(index)
        listbox.insert(new_index, value)
        listbox.selection_set(new_index)

    def _create_menu(self):
        menubar = tk.Menu(self)
        schema_menu = tk.Menu(menubar, tearoff=0)
        schema_menu.add_command(
            label="Show JSON Template",
            underline=5,
            command=self._show_schema,
            accelerator="Alt+J",
        )
        menubar.add_cascade(label="JSON Template", menu=schema_menu)
        self.bind_all("<Alt-j>", lambda _e: self._show_schema())
        self.config(menu=menubar)

    def _show_schema(self):
        try:
            root_dir = Path(__file__).resolve().parent.parent
            schema_path = root_dir / 'docs' / 'json_scheme.txt'
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_text = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load schema: {e}")
            return
        win = tk.Toplevel(self)
        win.title("JSON Template")
        text_widget = scrolledtext.ScrolledText(win, width=80, height=30)
        text_widget.pack(fill='both', expand=True, padx=5, pady=5)
        text_widget.insert('1.0', schema_text)
        text_widget.configure(state='disabled')

    def _run_conversion(self):
        inputs = {}
        for key, widget in self.widgets.items():
            entry = getattr(widget, 'widget', widget)
            if isinstance(entry, tk.Listbox):
                values = entry.get(0, tk.END)
                inputs[key] = [int(v) for v in values]
            else:
                entry = getattr(widget, 'widget', widget)
                inputs[key] = entry.get()

        try:
            kwargs = {
                'battery_profile_path': inputs['battery_profile_path'] or None,
                'donnees_camions_path': inputs['donnees_camions_path'] or None,
                'start': inputs['start'],
                'end': inputs['end'],
                'projection': int(inputs['projection']),
                'soc_cible': int(inputs['soc_cible']) if inputs['soc_cible'] else None,
                'marge_securite': inputs['marge_securite'] or None,
                'marge_prechauffage': inputs['marge_prechauffage'] or None,
                'diminution_soc': int(inputs['diminution_soc']) if inputs['diminution_soc'] else None,
                'maximum_exec_temps': int(inputs['maximum_exec_temps']) if inputs['maximum_exec_temps'] else None,
                'pas_de_temps': int(inputs['pas_de_temps']) if inputs['pas_de_temps'] else None,
                'temps_chargement': int(inputs['temps_chargement']) if inputs['temps_chargement'] else None,
                'temps_dechargement': int(inputs['temps_dechargement']) if inputs['temps_dechargement'] else None,
                'infrastructure_path': inputs.get('infrastructure_path') or None,
                'output': inputs['output'],
                'axe_optim_degrade': inputs.get('axe_optim_degrade'),
                'choix_optim': inputs.get('choix_optim'),
            }

            main(inputs['resultat'], **kwargs)
            messagebox.showinfo("Success", "Conversion completed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
