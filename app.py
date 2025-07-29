#developmenty by: DanyDis

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
import re
import shutil  # mettilo in alto tra gli import
import sqlite3
from flask import session
import shutil
from datetime import datetime
import glob


app = Flask(__name__)
app.secret_key = os.urandom(24)  # genera 24 byte casuali

# Configura il database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pazienti.db'  # Percorso del file del database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disabilita il tracciamento delle modifiche per risparmiare memoria
db = SQLAlchemy(app)

def anno_valido(anno):
    # Verifica che l'anno sia un numero di 4 cifre
    return bool(re.fullmatch(r'^\d{4}$', anno))


# Modello del paziente
class Paziente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    codice_fiscale = db.Column(db.String(16), nullable=False, unique=True)
    data_nascita = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Paziente {self.nome} {self.cognome}>'

# Crea il database
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

# Funzione di validazione codice fiscale
def codice_fiscale_valido(cf):
    return bool(re.fullmatch(r'^[A-Z0-9]{16}$', cf.upper()))

# Funzione per formattare correttamente il cognome
def format_cognome(cognome):
    return cognome.title()


# Funzione per verificare se il paziente esiste già in base al codice fiscale
def paziente_esiste(codice_fiscale):
    return Paziente.query.filter_by(codice_fiscale=codice_fiscale).first() is not None

# Resetta l'auto-increment per la tabella 'paziente'

@app.route('/aggiungi_paziente', methods=['GET', 'POST'])
def aggiungi_paziente():
    if request.method == 'POST':
        nome = request.form['nome'].strip().capitalize()
        cognome = format_cognome(request.form['cognome'].strip())
        codice_fiscale = request.form['codice_fiscale'].strip().upper()
        data_nascita = request.form['data_nascita']

        if paziente_esiste(codice_fiscale):
            return render_template('aggiungi_paziente.html', errore="Il paziente con questo codice fiscale esiste già.")

        if not codice_fiscale_valido(codice_fiscale):
            return "Codice fiscale non valido (deve contenere 16 caratteri alfanumerici)", 400

        nuovo_paziente = Paziente(
            nome=nome,
            cognome=cognome,
            codice_fiscale=codice_fiscale,
            data_nascita=data_nascita
        )
        db.session.add(nuovo_paziente)
        db.session.commit()

        # Sanitizzo nome e cognome per il filesystem (es. sostituisco spazi con underscore)
        nome_sanitizzato = nome.replace(" ", "_")
        cognome_sanitizzato = cognome.replace(" ", "_")

        cartella_pazienti_base = os.path.join(os.getcwd(), 'pazienti')
        os.makedirs(cartella_pazienti_base, exist_ok=True)

        cartella_individuale = os.path.join(cartella_pazienti_base, f"{nuovo_paziente.id}_{nome_sanitizzato}_{cognome_sanitizzato}")
        os.makedirs(cartella_individuale, exist_ok=True)

        # --- SEZIONE DI DEBUG ESTESA ---
        print(f"\n--- DEBUG INIZIO ---")
        print(f"CWD (Current Working Directory): {os.getcwd()}")

        percorso_modelli_originali = r"C:\Users\danie\Downloads\VSCode\StudioDentistico\modelli"  # <--- CONFERMA QUESTO PERCORSO!

        print(f"Percorso specificato per i modelli: {percorso_modelli_originali}")

        if not os.path.exists(percorso_modelli_originali):
            print(f"ERRORE GRAVE: La cartella dei modelli NON ESISTE al percorso: {percorso_modelli_originali}")
            print(f"--- DEBUG FINE (Problema cartella inesistente) ---\n")
            return "Errore interno: Cartella modelli non trovata.", 500

        print(f"La cartella dei modelli esiste: {percorso_modelli_originali}")

        contenuto_modelli = os.listdir(percorso_modelli_originali)
        print(f"Contenuto della cartella '{percorso_modelli_originali}':")
        for item in contenuto_modelli:
            item_path = os.path.join(percorso_modelli_originali, item)
            print(f" - {item} (È file: {os.path.isfile(item_path)}, È directory: {os.path.isdir(item_path)})")

        nome_file_consenso = "Consenso_Paziente.pdf"
        nome_file_anamnesi = "Anamnesi_Cartellclinica.pdf"

        file_consenso_originale = os.path.join(percorso_modelli_originali, nome_file_consenso)
        file_anamnesi_originale = os.path.join(percorso_modelli_originali, nome_file_anamnesi)

        print(f"Percorso atteso file Consenso: {file_consenso_originale}")
        print(f"Percorso atteso file Anamnesi: {file_anamnesi_originale}")

        consenso_found = os.path.isfile(file_consenso_originale)
        anamnesi_found = os.path.isfile(file_anamnesi_originale)

        print(f"Consenso_Paziente.pdf trovato all'interno di modelli? {consenso_found}")
        print(f"Anamnesi_Cartellclinica.pdf trovato all'interno di modelli? {anamnesi_found}")

        print(f"--- DEBUG FINE ---\n")
        # --- FINE SEZIONE DI DEBUG ESTESA ---

        if consenso_found:
            try:
                shutil.copy(file_consenso_originale, cartella_individuale)
                print("✅ Consenso_Paziente.pdf copiato con successo.")
            except Exception as e:
                print(f"❌ Errore durante la copia di Consenso_Paziente.pdf: {e}")
        else:
            print(f"❌ File mancante: {file_consenso_originale}")

        if anamnesi_found:
            try:
                shutil.copy(file_anamnesi_originale, cartella_individuale)
                print("✅ Anamnesi_Cartellclinica.pdf copiato con successo.")
            except Exception as e:
                print(f"❌ Errore durante la copia di Anamnesi_Cartellclinica.pdf: {e}")
        else:
            print(f"❌ File mancante: {file_anamnesi_originale}")

        trattamenti_path = os.path.join(cartella_individuale, "trattamenti.txt")
        if not os.path.exists(trattamenti_path):
            open(trattamenti_path, 'w', encoding='utf-8').close()

        return redirect(url_for('home'))

    return render_template('aggiungi_paziente.html')



# Questo blocco è per far funzionare il codice in modo standalone per testarlo
if __name__ == '__main__':
    # Esempio di come potresti strutturare le tue directory per i modelli
    # Assicurati che esista una cartella 'modelli' nella stessa directory dello script
    # E che al suo interno ci siano i due file .html
    if not os.path.exists('modelli'):
        os.makedirs('modelli')
        with open(os.path.join('modelli', 'Consenso_Paziente.html'), 'w') as f:
            f.write("<html><body>Modello Consenso</body></html>")
        with open(os.path.join('modelli', 'Anamnesi_Cartellclinica.html'), 'w') as f:
            f.write("<html><body>Modello Anamnesi</body></html>")
    print("Prepara i file modello per il test.")
    # Puoi avviare l'app Flask qui per testarla
    # app.run(debug=True)


@app.route('/elenco_pazienti') # O qualsiasi rotta tu abbia per questa pagina, es. '/visualizza_pazienti'
def elenco_pazienti(): # O il nome che hai dato a questa funzione, es. visualizza_pazienti
    search_cognome = request.args.get('cognome', '').strip()
    query = Paziente.query

    if search_cognome:
        query = query.filter(Paziente.cognome.ilike(f'%{search_cognome}%'))

    pazienti = query.all()

    # ******* MODIFICA QUI *******
    # Assicurati che 'visualizza_pazienti.html' sia il nome corretto del tuo file HTML
    return render_template('visualizza_pazienti.html', # <--- CAMBIA QUI: da 'elenco_pazienti.html' a 'visualizza_pazienti.html'
                           pazienti=pazienti,
                           request=request)


@app.route('/visualizza_pazienti')
def visualizza_pazienti():
    pazienti = Paziente.query.all()
    return render_template('visualizza_pazienti.html', pazienti=pazienti)

@app.route('/elimina_paziente/<int:paziente_id>', methods=['GET', 'POST'])
def elimina_paziente(paziente_id):
    paziente = Paziente.query.get_or_404(paziente_id)

    # Elimina la cartella del paziente
    cartella_individuale = os.path.join(os.getcwd(), 'pazienti', f"{paziente.id}_{paziente.nome}_{paziente.cognome}")



    if os.path.exists(cartella_individuale):
        shutil.rmtree(cartella_individuale)


    # Elimina il paziente dal database
    db.session.delete(paziente)
    db.session.commit()

    return redirect(url_for('visualizza_pazienti'))

#PER QUANTO RIGUARDA la funzione di cerca paziente e successivamente inserimento trattamento

# Funzione per ottenere il paziente
def get_pazienti(nome, cognome):
    nome = nome.strip().lower()
    cognome = cognome.strip().lower()
    return Paziente.query.filter(
        db.func.lower(Paziente.nome) == nome,
        db.func.lower(Paziente.cognome) == cognome
    ).all()


# Funzione per ottenere i trattamenti del paziente


def get_trattamenti(paziente):
    trattamenti = []

    # Supporta sia oggetto Paziente che dizionario
    if isinstance(paziente, dict):
        paziente_id = paziente.get('id')
        nome = paziente.get('nome')
        cognome = paziente.get('cognome')
    else:
        paziente_id = paziente.id
        nome = paziente.nome
        cognome = paziente.cognome

    if not paziente_id or not nome or not cognome:
        print("Errore: ID, nome o cognome mancante per il paziente.")
        return trattamenti

    nome = nome.replace(" ", "_")
    cognome = cognome.replace(" ", "_")
    cartella = os.path.join('cartelle_pazienti', f"{paziente_id}_{nome}_{cognome}")

    os.makedirs(cartella, exist_ok=True)

    file_path = os.path.join(cartella, 'trattamenti.txt')

    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write("Data | Denti | Importo | Descrizione\n")

    with open(file_path, 'r') as f:
        for linea in f:
            parts = linea.strip().split('|')
            if len(parts) == 4:
                data, denti, importo, descrizione = [p.strip() for p in parts]
                trattamenti.append({
                    'data': data,
                    'denti_interessati': denti,
                    'importo': importo,
                    'descrizione': descrizione
                })

    trattamenti.sort(key=lambda x: x['data'], reverse=True)
    return trattamenti

def leggi_trattamenti_raw(paziente):
    if isinstance(paziente, dict):
        paziente_id = paziente.get('id')
        nome = paziente.get('nome')
        cognome = paziente.get('cognome')
    else:
        paziente_id = paziente.id
        nome = paziente.nome
        cognome = paziente.cognome

    nome = nome.replace(" ", "_")
    cognome = cognome.replace(" ", "_")
    cartella = os.path.join('cartelle_pazienti', f"{paziente_id}_{nome}_{cognome}")

    file_path = os.path.join(cartella, 'trattamenti.txt')

    if not os.path.exists(file_path):
        return ""  # Nessun trattamento ancora

    with open(file_path, 'r', encoding='utf-8') as f:
        contenuto = f.read()

    return contenuto



# Route per aggiungere un trattamento
@app.route('/aggiungi_trattamento', methods=['GET', 'POST'])
def aggiungi_trattamento():
    nome = None
    cognome = None
    pazienti = []
    errore = None

    if request.method == 'POST':
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')

        # Funzione di ricerca dei pazienti
        pazienti = get_pazienti(nome, cognome)

        if pazienti:
            # Se ci sono risultati, passiamo anche nome e cognome
            return render_template(
                'aggiungi_trattamento.html',
                pazienti=pazienti,
                nome=nome,
                cognome=cognome,
                ricerca_effettuata=True
            )
        else:
            errore = "Nessun paziente trovato"
            # Se non ci sono risultati, mostriamo l'errore
            return render_template(
                'aggiungi_trattamento.html',
                errore=errore,
                nome=nome,
                cognome=cognome,
                ricerca_effettuata=True
            )

    return render_template('aggiungi_trattamento.html', ricerca_effettuata=False)



# Route per aggiungere i dettagli del trattamento
# Route per aggiungere i dettagli del trattamento
@app.route('/aggiungi_trattamento_dettagli', methods=['GET', 'POST'])
def aggiungi_trattamento_dettagli():
    nome = request.args.get('nome')
    cognome = request.args.get('cognome')
    paziente = (nome, cognome)

    if not paziente:
        flash("Paziente non trovato. Torna a cercarlo.", "error")
        return redirect(url_for('aggiungi_trattamento'))

    if request.method == 'POST':
        denti_interessati = request.form['denti_interessati']
        importo = request.form['importo']
        descrizione = request.form['descrizione']

        # Controlla se la cartella del paziente esiste, altrimenti creala
        cartella = os.path.join('cartelle_pazienti', f"{nome}_{cognome}")
        if not os.path.exists(cartella):
            os.makedirs(cartella)  # Crea la cartella se non esiste

        file_path = os.path.join(cartella, 'trattamenti.txt')

        with open(file_path, 'a') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {denti_interessati} | {importo} | {descrizione}\n")

        flash("Trattamento aggiunto con successo", "success")  # Messaggio di successo
        return redirect(url_for('aggiungi_trattamento', nome=nome, cognome=cognome))

    trattamenti = get_trattamenti(paziente)
    return render_template('aggiungi_trattamento.html', paziente=paziente, trattamenti=trattamenti)


# Route per cercare o inserire un trattamento (nel caso in cui non ci siano pazienti trovati)
@app.route('/cerca_o_inserisci_trattamento')
def cerca_o_inserisci_trattamento():
    return render_template('aggiungi_trattamento.html')


@app.route('/paziente/<int:paziente_id>/trattamenti', methods=['GET', 'POST'])
def dettagli_trattamento_paziente(paziente_id):
    paziente = Paziente.query.get(paziente_id)
    if not paziente:
        flash("Paziente non trovato", "error")
        return redirect(url_for('aggiungi_trattamento'))

    if request.method == 'POST':
        denti_interessati = request.form.getlist('denti_interessati')
        importo = request.form.get('importo', '').strip()
        descrizione = request.form.get('descrizione', '').strip()

        # Debug stampa
        print("DEBUG: denti_interessati =", denti_interessati)
        print("DEBUG: importo =", importo)
        print("DEBUG: descrizione =", descrizione)

        denti_str = ', '.join(denti_interessati)

        # Trova la cartella corretta già creata in fase di inserimento paziente
        pattern = os.path.join('pazienti', f"{paziente.id}_*")
        cartelle_possibili = glob.glob(pattern)

        if not cartelle_possibili:
            flash("Cartella paziente non trovata", "error")
            return redirect(url_for('aggiungi_trattamento'))

        cartella = cartelle_possibili[0]
        file_path = os.path.join(cartella, 'trattamenti.txt')

        print("DEBUG: file_path =", os.path.abspath(file_path))

        # Qui NON serve creare la cartella, deve già esistere

        with open(file_path, 'a', encoding='utf-8') as f:
            f.write("------------------------------------------------------------\n")
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {denti_str} | {importo} €\n")
            f.write(f"{descrizione}\n\n")

        flash("Trattamento aggiunto con successo", "success")
        return redirect(url_for('dettagli_trattamento_paziente', paziente_id=paziente.id))

    trattamenti = get_trattamenti({
        'nome': paziente.nome,
        'cognome': paziente.cognome,
        'codice_fiscale': paziente.codice_fiscale,
        'data_nascita': paziente.data_nascita
    })

    return render_template('dettagli_trattamento_paziente.html', paziente=paziente, trattamenti=trattamenti)


@app.route('/visualizzatrattamenti', methods=['GET', 'POST'])
def visualizzatrattamenti():
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        cognome = request.form['cognome'].strip()

        # Salva in sessione per ricordare la ricerca
        session['nome_ricerca'] = nome
        session['cognome_ricerca'] = cognome

        pazienti = Paziente.query.filter(
            db.func.lower(Paziente.nome) == nome.lower(),
            db.func.lower(Paziente.cognome) == cognome.lower()
        ).all()

        return render_template('visualizzatrattamenti.html',
                               ricerca_effettuata=True,
                               nome=nome,
                               cognome=cognome,
                               pazienti=pazienti,
                               errore=None)

    else:  # GET
        # prova a prendere i parametri da sessione
        nome = session.get('nome_ricerca')
        cognome = session.get('cognome_ricerca')

        if nome and cognome:
            pazienti = Paziente.query.filter(
                db.func.lower(Paziente.nome) == nome.lower(),
                db.func.lower(Paziente.cognome) == cognome.lower()
            ).all()

            return render_template('visualizzatrattamenti.html',
                                   ricerca_effettuata=True,
                                   nome=nome,
                                   cognome=cognome,
                                   pazienti=pazienti,
                                   errore=None)

        # Se non c'è ricerca salvata, mostra form vuoto
        return render_template('visualizzatrattamenti.html',
                               ricerca_effettuata=False,
                               errore=None)

def evidenzia_testo(testo):
    parole_chiave = ["Data:", "Descrizione:", "Denti:", "Importo:"]
    for parola in parole_chiave:
        testo = testo.replace(parola, f'<span class="chiave">{parola}</span>')
    return testo


@app.route('/visualizza_trattamenti/<int:paziente_id>')
def mostra_trattamenti_paziente(paziente_id):
    paziente = Paziente.query.get(paziente_id)
    if not paziente:
        flash("Paziente non trovato", "error")
        return redirect(url_for('visualizzatrattamenti'))

    nome_sanitizzato = paziente.nome.replace(" ", "_")
    cognome_sanitizzato = paziente.cognome.replace(" ", "_")
    cartella = os.path.join('pazienti', f"{paziente.id}_{nome_sanitizzato}_{cognome_sanitizzato}")
    path_trattamenti = os.path.join(cartella, 'trattamenti.txt')

    contenuto = "Nessun trattamento registrato."
    if os.path.exists(path_trattamenti):
        with open(path_trattamenti, 'r', encoding='utf-8') as f:
            contenuto = f.read()
        contenuto = evidenzia_testo(contenuto)

    return render_template('trattamenti_paziente.html', paziente=paziente, contenuto=contenuto)


def leggi_trattamenti(path):
    trattamenti = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            contenuto = f.read().strip()
            blocchi = contenuto.split('\n\n')  # separa i trattamenti da doppio invio
            for blocco in blocchi:
                righe = blocco.split('\n')
                trattamento = {}
                for riga in righe:
                    if ': ' in riga:
                        chiave, valore = riga.split(': ', 1)
                        trattamento[chiave.strip().lower()] = valore.strip()
                if trattamento:
                    trattamenti.append(trattamento)
    return trattamenti

@app.route('/modifica_trattamenti/<int:paziente_id>', methods=['GET', 'POST'])
def modifica_trattamenti(paziente_id):
    paziente = Paziente.query.get(paziente_id)
    if not paziente:
        flash("Paziente non trovato", "error")
        return redirect(url_for('home'))

    nome_sanitizzato = paziente.nome.replace(" ", "_")
    cognome_sanitizzato = paziente.cognome.replace(" ", "_")
    cartella = os.path.join('pazienti', f"{paziente.id}_{nome_sanitizzato}_{cognome_sanitizzato}")
    path_trattamenti = os.path.join(cartella, 'trattamenti.txt')

    if request.method == 'POST':
        nuovo_contenuto = request.form.get('contenuto', '')
        with open(path_trattamenti, 'w', encoding='utf-8') as f:
            f.write(nuovo_contenuto)
        flash("Trattamenti salvati correttamente", "success")
        return redirect(url_for('visualizzatrattamenti'))

    contenuto = ""
    if os.path.exists(path_trattamenti):
        with open(path_trattamenti, 'r', encoding='utf-8') as f:
            #contenuto = f.read()
            contenuto = elimina_righe_vuote_doppie(f.read())

    return render_template('modifica_trattamenti.html', paziente=paziente, contenuto=contenuto)



@app.route('/modifica_trattamenti/<int:paziente_id>', methods=['POST'])
def salva_trattamenti(paziente_id):
    paziente = Paziente.query.get(paziente_id)
    if not paziente:
        flash("Paziente non trovato", "error")
        return redirect(url_for('home'))

    contenuto = request.form.get('contenuto', '')

    nome_sanitizzato = paziente.nome.replace(" ", "_")
    cognome_sanitizzato = paziente.cognome.replace(" ", "_")
    cartella = os.path.join('pazienti', f"{paziente.id}_{nome_sanitizzato}_{cognome_sanitizzato}")
    os.makedirs(cartella, exist_ok=True)
    path_trattamenti = os.path.join(cartella, 'trattamenti.txt')

    # **Salva esattamente come ricevuto, senza modifiche**
    with open(path_trattamenti, 'w', encoding='utf-8') as f:
        f.write(contenuto)

    flash("Trattamenti aggiornati con successo", "success")
    return redirect(url_for('mostra_trattamenti_paziente', paziente_id=paziente.id))


import re

def elimina_righe_vuote_doppie(testo):
    # 1) Limita righe vuote multiple a massimo 1 riga vuota
    testo = re.sub(r'\n{3,}', '\n\n', testo)

    # 2) Rimuove righe vuote tra "Trattamento Dente XX:" e descrizione
    testo = re.sub(r'(Trattamento Dente \d+):\n\s*\n', r'\1:\n', testo)

    # 3) Rimuove righe vuote tra:
    # - linea "-----" e la riga data (data ha formato YYYY-MM-DD ...)
    # - riga data e la prima riga "Trattamento Dente XX:"
    #    (si considerano righe vuote tra queste, le elimina)

    # Tra linea di separazione e data
    testo = re.sub(r'(------------------------------------------------------------)\n\s*\n(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \|)', r'\1\n\2', testo)

    # Tra data e "Trattamento Dente XX:"
    testo = re.sub(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| [^\n]+)\n\s*\n(Trattamento Dente \d+:)', r'\1\n\2', testo)

    return testo



@app.route('/reset_ricerca')
def reset_ricerca():
    session.pop('nome_ricerca', None)
    session.pop('cognome_ricerca', None)
    return redirect(url_for('visualizzatrattamenti'))

