<div align="center">

# ⚽ EA SPORTS FC 27 — Mac e iPhone, nativo a 60 fps

**EA SPORTS FC 27 (versione Nintendo Switch) che gira in modo nativo su Mac con Apple Silicon e su iPhone, a 60 fotogrammi al secondo, senza emulatore e senza artefatti grafici.**

Basato su [NX2Apple](https://github.com/LNPANDY/NX2Apple) · Licenza [MIT](LICENSE)

[🇮🇹 Italiano](#-il-progetto) · [🇬🇧 English](#-english)

</div>

---

## 🎯 Il progetto

Questo repository è un fork di NX2Apple dedicato a un solo obiettivo: **la piena compatibilità e ottimizzazione di EA SPORTS FC 27** su Mac e iPhone.

Il codice del gioco viene riscritto per Apple Silicon e i suoi shader vengono tradotti in Metal: il gioco gira direttamente sul processore e sulla GPU Apple, non dentro un emulatore. Il risultato è un gioco che, invece dei limiti della Switch, sfrutta la potenza dell'hardware Apple:

| | Nintendo Switch | Questo progetto (Mac M2) |
|---|---|---|
| Frame rate | limitato dall'hardware della console | **60 fps stabili** in menù, carriera e partita |
| Risoluzione interna | quella della console | **1920×1080**, portata a 2560×1440 con MetalFX |
| Filtro delle texture | quello della console | **anisotropico 16×** |
| Ombre | mappe a 16 bit | **mappe a 32 bit** (visi senza puntinature) |

> Nota onesta: i modelli, le texture e gli effetti sono quelli della versione Switch. Il progetto porta fluidità e pulizia dell'immagine, non la grafica della versione PS5.

## ✅ Stato

| Area | Mac | iPhone |
|---|---|---|
| Avvio, menù principale | ✅ 60 fps | ✅ si avvia a 60 fps |
| Partita completa | ✅ 60 fps, senza crash | da verificare |
| Carriera Tecnico (menù 3D, creazione tecnico) | ✅ | da verificare |
| Filmati (presentazione, conferenze, trattative) | ✅ | da verificare |
| Ritratti dei giocatori (rosa, rinnovi) | ✅ | da verificare |

## 🛠️ Cosa è stato corretto per FC 27

Tutti i difetti grafici trovati durante il porting, e la loro causa:

1. **Scene della carriera e filmati completamente neri.** Il passaggio "atmosfera" del motore Frostbite moltiplica la scena illuminata per la trasparenza dell'aria, passata come seconda uscita dello shader (*dual-source blending*). La traduzione non la supportava e la scena veniva moltiplicata per quasi zero. Ora gli shader con due uscite hanno una variante `<chiave>_bd.metallib` con `[[color(0), index(1)]]`, preparata in anticipo per Mac e iPhone.
2. **Luci della carriera mai conteggiate.** I contatori delle luci per riquadro dello schermo (operazioni atomiche su *buffer texture* viste in un altro formato) finivano in un buffer di appoggio scartato. Ora scrivono nella memoria del gioco.
3. **Riquadri scuri e bordi "a scalini" sui personaggi.** Il traduttore degli shader (derivato da Ryujinx) non implementava l'istruzione Maxwell `PRMT` (permutazione di byte), usata dallo shader che costruisce la griglia delle luci. Ora è implementata con tutte le modalità (`InstEmitPermute.cs`).
4. **Visi "sporchi" e puntinati nei ritratti.** Le GPU Apple arrotondano la profondità nelle mappe d'ombra a 16 bit in modo diverso dalla Switch, e le superfici si facevano ombra da sole. Le mappe d'ombra a 16 bit ora usano `Depth32Float`.
5. **Blocchi del menù Carriera Tecnico** dovuti a shader mancanti: catturati e tradotti (oltre 600 shader).
6. Funzioni NVN mancanti (`nvnEventGetMemoryPool/Offset`, `WaitEvent`) e ordinamento delle *indirect dispatch* rispetto ai calcoli precedenti.

Il dettaglio tecnico di ogni modifica è nella cronologia e nei commenti del codice (`dm/gfx/nvn/nvn_mtl.m`, `dm/gfx/tools/dmsh_build.py`, `dm/gfx/tex/nvn_fmt_mtl.c`).

## 📦 Installazione passo passo

### 1. Cosa ti serve

- Un **Mac con Apple Silicon** (M1 o successivo) con macOS recente, almeno **150 GB liberi** (NSP, file estratti, app e cartella `romfs`) e una connessione a Internet.
- **I tuoi file del gioco**, estratti dalla tua console (non sono inclusi qui e non vanno condivisi):
  - l'NSP base di EA SPORTS FC 27 (`0100C49025D3E000`, v0);
  - l'aggiornamento **v393216 (1.8d.310c)**;
  - facoltativo: il DLC della telecronaca in italiano;
  - le tue chiavi `prod.keys`.
- **Xcode** (dall'App Store, aperto almeno una volta per accettare la licenza) e **Homebrew**.

### 2. Preparare il Mac (una volta sola)

Apri il Terminale e scrivi:

```bash
xcode-select --install
brew install xcodegen zstd spirv-cross
brew install --cask dotnet-sdk
python3 -m pip install lz4 capstone fonttools backports.zstd
git clone https://github.com/sacoc96/NX2Apple-FC27.git
cd NX2Apple-FC27
```

Metti in una stessa cartella (per esempio `~/Downloads/Games/FC 27`) gli NSP del gioco, dell'aggiornamento e del DLC.

### 3A. Installare su macOS

1. Dal Terminale, nella cartella `NX2Apple-FC27`, costruisci l'app (la prima volta richiede parecchio tempo: estrazione, riscrittura del codice e traduzione degli shader):
   ```bash
   python3 scripts/build_ipa_from_nsp.py "$HOME/Downloads/Games/FC 27" --platform mac-app -k /percorso/prod.keys -l it
   ```
2. Alla fine trovi **`EA SPORTS FC 27.app`** nella cartella degli NSP. I file del gioco sono già dentro l'app (circa 33 GB): non serve copiare altro.
3. Trascina l'app nella cartella **Applicazioni** (facoltativo).
4. Primo avvio: l'app non è firmata da Apple, quindi fai **clic destro → Apri → Apri**. In alternativa: `xattr -dr com.apple.quarantine "EA SPORTS FC 27.app"`.
5. Gioca con un **controller** (Xbox, PlayStation, Switch Pro) collegato via Bluetooth o USB.

I salvataggi e le impostazioni sono in `~/Library/Application Support/nxnative/0100C49025D3E000/`, il registro in `~/Library/Logs/nxnative/0100C49025D3E000.log`.

### 3B. Installare su iPhone

1. **Costruisci l'IPA** dal Terminale, nella cartella `NX2Apple-FC27`:
   ```bash
   DM_ENTITLEMENTS=ios_entitlements.plist python3 scripts/build_ipa_from_nsp.py "$HOME/Downloads/Games/FC 27" --platform ios -k /percorso/prod.keys -l it
   ```
   Nella cartella degli NSP ottieni due cose:
   - **`EaSportsFc27.ipa`** (circa 1,6 GB): l'app;
   - la cartella **`romfs`** (circa 55 file, 32 GB in tutto: `romfs.idx`, `romfs.00`, `romfs.01`, …): i dati del gioco.
2. **Attiva la Modalità sviluppatore sull'iPhone**: Impostazioni → Privacy e sicurezza → **Modalità sviluppatore** → attiva e riavvia.
3. **Installa l'IPA** con **Impactor** (consigliato), **AltStore Classic 2.2 o successivo** oppure **Xcode con un Personal Team**, accedendo con il tuo Apple ID.
   - **Non usare Sideloadly**: scarta l'entitlement della memoria estesa e il gioco si chiude per mancanza di memoria.
   - Con un Apple ID gratuito l'app scade dopo 7 giorni e va reinstallata (i salvataggi restano).
4. Se richiesto, **autorizza lo sviluppatore**: Impostazioni → Generali → VPN e gestione dispositivo → il tuo Apple ID → Autorizza.
5. **Avvia l'app una volta e chiudila**: così iOS crea la sua cartella Documenti.
6. **Copia la cartella `romfs` sull'iPhone**, dentro i Documenti dell'app (ci vuole un po': sono circa 32 GB, quindi servono almeno 35 GB liberi sull'iPhone):
   - **dal Mac**: collega l'iPhone con il cavo → apri il Finder → seleziona l'iPhone nella barra laterale → scheda **File** → trascina la cartella `romfs` sopra **EA SPORTS FC 27**;
   - oppure con l'app **File** dell'iPhone (AirDrop o iCloud Drive), mettendola in *Su iPhone → EA SPORTS FC 27*.

   Alla fine deve esistere `Documents/romfs/romfs.idx` dentro l'app.
7. **Avvia il gioco.** Prima del gioco compare una schermata di impostazioni; poi parte FC 27. Usa un **controller Bluetooth** (Xbox, PlayStation, Switch Pro): quando è collegato i comandi touch spariscono. I primi secondi di ogni scena nuova possono avere un piccolo scatto, perché l'app prepara la grafica una volta sola e poi la ricorda.

Testato su iPhone 17. Su iPhone con meno di 8 GB di RAM il gioco potrebbe non avere memoria sufficiente.

Per capire cosa non va: nell'app **File**, cartella *EA SPORTS FC 27*, c'è `log.txt` (e `log.prev.txt` per l'avvio precedente). Le impostazioni si cambiano senza ricostruire scrivendo in `Documents/env.txt` una riga `CHIAVE=VALORE` per ogni impostazione, per esempio `DM_FPS_TARGET=30` per risparmiare batteria.

Il profilo del gioco è in [`dm/games/0100C49025D3E000`](dm/games/0100C49025D3E000); la guida completa di NX2Apple è in [README.NX2Apple.md](README.NX2Apple.md).

## ⚖️ Note legali

Questo repository contiene solo codice. Non contiene file del gioco, chiavi o contenuti di EA o Nintendo: per usarlo devi possedere il gioco ed estrarre tu i tuoi file. EA SPORTS FC è un marchio di Electronic Arts; Nintendo Switch è un marchio di Nintendo. Progetto non affiliato né approvato da nessuna delle due aziende.

---

## 🇬🇧 English

A fork of [NX2Apple](https://github.com/LNPANDY/NX2Apple) focused on **EA SPORTS FC 27 (Switch version) running natively on Apple Silicon Macs and iPhone at a locked 60 fps**, with every graphics bug found during the port fixed: dual-source blending for the Frostbite atmosphere pass (black career scenes), image atomics on buffer-texture views (light tile counters), the Maxwell `PRMT` instruction in the Ryujinx-based shader translator (blocky tiles on characters), and 16-bit shadow maps promoted to `Depth32Float` (speckled faces). Assets are the Switch ones: the project brings frame rate and a clean image, not PS5 graphics. Bring your own game dumps and keys; none are included. The original NX2Apple guide is in [README.NX2Apple.md](README.NX2Apple.md).
