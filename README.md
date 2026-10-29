<div align="center">

# ⚽ EA SPORTS FC 27 — Mac & iPhone, native 60 fps

**EA SPORTS FC 27 (versione Nintendo Switch) che gira in modo nativo su Mac con Apple Silicon e su iPhone, a 60 fotogrammi al secondo, senza emulatore e senza artefatti grafici.**

**EA SPORTS FC 27 (Nintendo Switch version) running natively on Apple Silicon Macs and iPhone at 60 frames per second, without an emulator and without graphics artifacts.**

Basato su / Based on [NX2Apple](https://github.com/LNPANDY/NX2Apple) · [MIT](LICENSE)

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

I risultati qui sopra sono con tutti i 609 shader catturati. La cattura automatica (punto 3) è stata provata a parte; una costruzione completa da zero su un Mac diverso non è ancora stata provata: se qualcosa non va, apri una segnalazione (Issue).

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

### 3. Catturare gli shader (la prima volta)

FC 27 non tiene i suoi shader in una forma che si possa estrarre dai file del gioco: il gioco li crea mentre gira. Per questo **non sono inclusi nel repository** (sono codice di EA) e ognuno li cattura dalla propria copia. Nel profilo c'è l'elenco dei **609 shader** che servono (`dm/games/0100C49025D3E000/nvn_capture.tsv`), così la costruzione sa quando la cattura è completa.

1. **Prima costruzione, cattura automatica.** Lancia la costruzione per Mac (punto 4A, comando sotto). Prima di tradurre gli shader avvia il gioco da sola, senza finestra, per al massimo 15 minuti, premendo A ogni pochi secondi: cattura gli shader dell'avvio e dei primi menù. Alla fine dice quanti ne mancano, per esempio `shader capture: 59 of 609 shaders`.
2. **Cattura giocando.** Lancia:
   ```bash
   python3 scripts/nvn_capture_play.py "$HOME/Downloads/Games/FC 27" -l it
   ```
   Si apre il gioco in una finestra con gli shader catturati fino a quel momento: dove ne mancano vedrai zone nere o sbagliate, è normale. Gioca e visita **tutto**: menù principale, Carriera Tecnico (crea una carriera, guarda la presentazione e i filmati, apri rosa e rinnovi), Carriera Professionista, una **partita completa** (con replay e intervallo). Nel Terminale compare il conteggio (`350 of 609 shaders captured`…). Quando dice **complete**, chiudi il gioco.
3. **Ricostruisci** l'app (punto 4A) o l'IPA (punto 4B): ora ha tutti gli shader e la grafica è completa.

Puoi ripetere il punto 2 quante volte vuoi: ogni volta riparte dagli shader già catturati, e la costruzione usa sempre quelli che ci sono. Gli shader catturati restano nella cartella di lavoro (`<cartella NSP>/0100C49025D3E000_build/extract/v393216/nvn_capture`): non cancellarla.

### 4A. Installare su macOS

1. Dal Terminale, nella cartella `NX2Apple-FC27`, costruisci l'app (la prima volta richiede parecchio tempo: estrazione, riscrittura del codice e traduzione degli shader):
   ```bash
   python3 scripts/build_ipa_from_nsp.py "$HOME/Downloads/Games/FC 27" --platform mac-app -k /percorso/prod.keys -l it
   ```
   La prima volta segui poi il punto 3 (cattura degli shader) e ricostruisci.
2. Alla fine trovi **`EA SPORTS FC 27.app`** nella cartella degli NSP. I file del gioco sono già dentro l'app (circa 33 GB): non serve copiare altro.
3. Trascina l'app nella cartella **Applicazioni** (facoltativo).
4. Primo avvio: l'app non è firmata da Apple, quindi fai **clic destro → Apri → Apri**. In alternativa: `xattr -dr com.apple.quarantine "EA SPORTS FC 27.app"`.
5. Gioca con un **controller** (Xbox, PlayStation, Switch Pro) collegato via Bluetooth o USB.

I salvataggi e le impostazioni sono in `~/Library/Application Support/nxnative/0100C49025D3E000/`, il registro in `~/Library/Logs/nxnative/0100C49025D3E000.log`.

### 4B. Installare su iPhone

1. **Completa prima la cattura degli shader** (punto 3) sul Mac.
2. **Costruisci l'IPA** dal Terminale, nella cartella `NX2Apple-FC27`:
   ```bash
   DM_ENTITLEMENTS=ios_entitlements.plist python3 scripts/build_ipa_from_nsp.py "$HOME/Downloads/Games/FC 27" --platform ios -k /percorso/prod.keys -l it
   ```
   Nella cartella degli NSP ottieni due cose:
   - **`EaSportsFc27.ipa`** (circa 1,6 GB): l'app;
   - la cartella **`romfs`** (circa 55 file, 32 GB in tutto: `romfs.idx`, `romfs.00`, `romfs.01`, …): i dati del gioco.
3. **Attiva la Modalità sviluppatore sull'iPhone**: Impostazioni → Privacy e sicurezza → **Modalità sviluppatore** → attiva e riavvia.
4. **Installa l'IPA** con **Impactor** (consigliato), **AltStore Classic 2.2 o successivo** oppure **Xcode con un Personal Team**, accedendo con il tuo Apple ID.
   - **Non usare Sideloadly**: scarta l'entitlement della memoria estesa e il gioco si chiude per mancanza di memoria.
   - Con un Apple ID gratuito l'app scade dopo 7 giorni e va reinstallata (i salvataggi restano).
5. Se richiesto, **autorizza lo sviluppatore**: Impostazioni → Generali → VPN e gestione dispositivo → il tuo Apple ID → Autorizza.
6. **Avvia l'app una volta e chiudila**: così iOS crea la sua cartella Documenti.
7. **Copia la cartella `romfs` sull'iPhone**, dentro i Documenti dell'app (ci vuole un po': sono circa 32 GB, quindi servono almeno 35 GB liberi sull'iPhone):
   - **dal Mac**: collega l'iPhone con il cavo → apri il Finder → seleziona l'iPhone nella barra laterale → scheda **File** → trascina la cartella `romfs` sopra **EA SPORTS FC 27**;
   - oppure con l'app **File** dell'iPhone (AirDrop o iCloud Drive), mettendola in *Su iPhone → EA SPORTS FC 27*.

   Alla fine deve esistere `Documents/romfs/romfs.idx` dentro l'app.
8. **Avvia il gioco.** Prima del gioco compare una schermata di impostazioni; poi parte FC 27. Usa un **controller Bluetooth** (Xbox, PlayStation, Switch Pro): quando è collegato i comandi touch spariscono. I primi secondi di ogni scena nuova possono avere un piccolo scatto, perché l'app prepara la grafica una volta sola e poi la ricorda.

Testato su iPhone 17. Su iPhone con meno di 8 GB di RAM il gioco potrebbe non avere memoria sufficiente.

Per capire cosa non va: nell'app **File**, cartella *EA SPORTS FC 27*, c'è `log.txt` (e `log.prev.txt` per l'avvio precedente). Le impostazioni si cambiano senza ricostruire scrivendo in `Documents/env.txt` una riga `CHIAVE=VALORE` per ogni impostazione, per esempio `DM_FPS_TARGET=30` per risparmiare batteria.

Il profilo del gioco è in [`dm/games/0100C49025D3E000`](dm/games/0100C49025D3E000); la guida completa di NX2Apple è in [README.NX2Apple.md](README.NX2Apple.md).

## ⚖️ Note legali

Questo repository contiene solo codice. Non contiene file del gioco, chiavi o contenuti di EA o Nintendo: per usarlo devi possedere il gioco ed estrarre tu i tuoi file. EA SPORTS FC è un marchio di Electronic Arts; Nintendo Switch è un marchio di Nintendo. Progetto non affiliato né approvato da nessuna delle due aziende.

---

## 🇬🇧 English

### 🎯 The project

This repository is a fork of NX2Apple with one goal: **full compatibility and optimization of EA SPORTS FC 27** on Mac and iPhone.

The game's code is rewritten for Apple Silicon and its shaders are translated to Metal: the game runs directly on the Apple CPU and GPU, not inside an emulator. The result is a game that uses the power of Apple hardware instead of the limits of the Switch:

| | Nintendo Switch | This project (Mac M2) |
|---|---|---|
| Frame rate | limited by the console hardware | **locked 60 fps** in menus, career and matches |
| Internal resolution | the console's | **1920×1080**, upscaled to 2560×1440 with MetalFX |
| Texture filtering | the console's | **16× anisotropic** |
| Shadows | 16-bit shadow maps | **32-bit shadow maps** (no speckled faces) |

> Honest note: models, textures and effects are those of the Switch version. The project brings smoothness and a clean image, not the graphics of the PS5 version.

### ✅ Status

| Area | Mac | iPhone |
|---|---|---|
| Boot, main menu | ✅ 60 fps | ✅ boots at 60 fps |
| Full match | ✅ 60 fps, no crashes | to be verified |
| Manager Career (3D menus, manager creation) | ✅ | to be verified |
| Cutscenes (presentation, press conferences, negotiations) | ✅ | to be verified |
| Player portraits (squad, contract renewals) | ✅ | to be verified |

The results above are with all 609 shaders captured. The automatic capture (step 3) was tested on its own; a full build from scratch on a different Mac has not been tested yet: if something goes wrong, please open an Issue.

### 🛠️ What was fixed for FC 27

Every graphics bug found during the port, and its cause:

1. **Black career scenes and cutscenes.** Frostbite's atmosphere pass multiplies the lit scene by the air's transmittance, passed as the shader's second output (*dual-source blending*). The translation did not support it, so the scene was multiplied by almost zero. Fragment shaders with two outputs now get a `<key>_bd.metallib` variant with `[[color(0), index(1)]]`, built ahead of time for Mac and iPhone.
2. **Career lights never counted.** The per-screen-tile light counters (image atomics on *buffer textures* viewed in another format) went to a discarded scratch buffer. They now write to the game's memory.
3. **Dark squares and stair-stepped edges on characters.** The shader translator (derived from Ryujinx) did not implement the Maxwell `PRMT` instruction (byte permute), used by the shader that builds the light grid. It is now implemented with all its modes (`InstEmitPermute.cs`).
4. **"Dirty", speckled faces in portraits.** Apple GPUs round depth into 16-bit shadow maps differently from the Switch, so surfaces shadowed themselves. 16-bit shadow maps now use `Depth32Float`.
5. **Manager Career menu freezes** caused by missing shaders: captured and translated (over 600 shaders).
6. Missing NVN functions (`nvnEventGetMemoryPool/Offset`, `WaitEvent`) and ordering of *indirect dispatches* after earlier compute work.

The technical detail of every change is in the history and in the code comments (`dm/gfx/nvn/nvn_mtl.m`, `dm/gfx/tools/dmsh_build.py`, `dm/gfx/tex/nvn_fmt_mtl.c`).

### 📦 Step-by-step installation

#### 1. What you need

- A **Mac with Apple Silicon** (M1 or later) on a recent macOS, at least **150 GB free** (NSPs, extracted files, app and `romfs` folder) and an Internet connection.
- **Your own game files**, dumped from your console (they are not included here and must not be shared):
  - the EA SPORTS FC 27 base NSP (`0100C49025D3E000`, v0);
  - update **v393216 (1.8d.310c)**;
  - optional: the commentary DLC;
  - your `prod.keys`.
- **Xcode** (from the App Store, opened at least once to accept the license) and **Homebrew**.

#### 2. Prepare the Mac (once)

Open Terminal and type:

```bash
xcode-select --install
brew install xcodegen zstd spirv-cross
brew install --cask dotnet-sdk
python3 -m pip install lz4 capstone fonttools backports.zstd
git clone https://github.com/sacoc96/NX2Apple-FC27.git
cd NX2Apple-FC27
```

Put the game, update and DLC NSPs in one folder (for example `~/Downloads/Games/FC 27`).

#### 3. Capture the shaders (the first time)

FC 27 does not keep its shaders in a form that can be extracted from the game files: the game creates them while it runs. That is why they are **not included in this repository** (they are EA's code) and everyone captures them from their own copy. The profile lists the **609 shaders** the game needs (`dm/games/0100C49025D3E000/nvn_capture.tsv`), so the build knows when the capture is complete.

1. **First build, automatic capture.** Run the Mac build (step 4A, command below). Before translating the shaders it boots the game by itself, without a window, for up to 15 minutes, pressing A every few seconds: it captures the shaders of the boot and the first menus. At the end it says how many are missing, for example `shader capture: 59 of 609 shaders`.
2. **Capture by playing.** Run:
   ```bash
   python3 scripts/nvn_capture_play.py "$HOME/Downloads/Games/FC 27"
   ```
   The game opens in a window with the shaders captured so far: where some are missing you will see black or wrong areas, that is expected. Play and visit **everything**: main menu, Manager Career (create a career, watch the presentation and the cutscenes, open the squad and the contract renewals), Player Career, a **full match** (with replays and half time). Terminal shows the count (`350 of 609 shaders captured`…). When it says **complete**, close the game.
3. **Build again** the app (step 4A) or the IPA (step 4B): it now has every shader and the graphics are complete.

You can repeat step 2 as many times as you like: each time it starts from the shaders already captured, and the build always uses what is there. The captured shaders stay in the build folder (`<NSP folder>/0100C49025D3E000_build/extract/v393216/nvn_capture`): do not delete it.

#### 4A. Install on macOS

1. In Terminal, inside the `NX2Apple-FC27` folder, build the app (the first time takes a while: extraction, code rewrite and shader translation):
   ```bash
   python3 scripts/build_ipa_from_nsp.py "$HOME/Downloads/Games/FC 27" --platform mac-app -k /path/to/prod.keys
   ```
   (English by default; add `-l it` for Italian, `-l fr`, `-l de`, `-l es`… for other languages.)
   The first time, then follow step 3 (shader capture) and build again.
2. When it finishes you will find **`EA SPORTS FC 27.app`** in the NSP folder. The game files are already inside the app (about 33 GB): nothing else to copy.
3. Drag the app into **Applications** (optional).
4. First launch: the app is not signed by Apple, so **right-click → Open → Open**. Alternatively: `xattr -dr com.apple.quarantine "EA SPORTS FC 27.app"`.
5. Play with a **controller** (Xbox, PlayStation, Switch Pro) connected over Bluetooth or USB.

Saves and settings are in `~/Library/Application Support/nxnative/0100C49025D3E000/`, the log in `~/Library/Logs/nxnative/0100C49025D3E000.log`.

#### 4B. Install on iPhone

1. **First complete the shader capture** (step 3) on the Mac.
2. **Build the IPA** in Terminal, inside the `NX2Apple-FC27` folder:
   ```bash
   DM_ENTITLEMENTS=ios_entitlements.plist python3 scripts/build_ipa_from_nsp.py "$HOME/Downloads/Games/FC 27" --platform ios -k /path/to/prod.keys
   ```
   In the NSP folder you get two things:
   - **`EaSportsFc27.ipa`** (about 1.6 GB): the app;
   - the **`romfs`** folder (about 55 files, 32 GB in total: `romfs.idx`, `romfs.00`, `romfs.01`, …): the game data.
3. **Turn on Developer Mode on the iPhone**: Settings → Privacy & Security → **Developer Mode** → on, then restart.
4. **Install the IPA** with **Impactor** (recommended), **AltStore Classic 2.2 or later** or **Xcode with a Personal Team**, signing in with your Apple ID.
   - **Do not use Sideloadly**: it drops the extended memory entitlement and the game is killed for lack of memory.
   - With a free Apple ID the app expires after 7 days and must be reinstalled (saves are kept).
5. If asked, **trust the developer**: Settings → General → VPN & Device Management → your Apple ID → Trust.
6. **Open the app once and close it**: this makes iOS create its Documents folder.
7. **Copy the `romfs` folder to the iPhone**, into the app's Documents (it takes a while: about 32 GB, so you need at least 35 GB free on the iPhone):
   - **from the Mac**: connect the iPhone with a cable → open Finder → select the iPhone in the sidebar → **Files** tab → drag the `romfs` folder onto **EA SPORTS FC 27**;
   - or with the iPhone's **Files** app (AirDrop or iCloud Drive), placing it in *On My iPhone → EA SPORTS FC 27*.

   In the end `Documents/romfs/romfs.idx` must exist inside the app.
8. **Launch the game.** A settings screen comes first, then FC 27 starts. Use a **Bluetooth controller** (Xbox, PlayStation, Switch Pro): while it is connected the touch controls disappear. The first seconds of each new scene can stutter slightly, because the app prepares its graphics once and then remembers them.

Tested on iPhone 17. On iPhones with less than 8 GB of RAM the game may run out of memory.

When something goes wrong: in the **Files** app, folder *EA SPORTS FC 27*, there is `log.txt` (and `log.prev.txt` for the previous launch). Settings can be changed without rebuilding by writing one `KEY=VALUE` line per setting in `Documents/env.txt`, for example `DM_FPS_TARGET=30` to save battery.

The game profile is in [`dm/games/0100C49025D3E000`](dm/games/0100C49025D3E000); the full NX2Apple guide is in [README.NX2Apple.md](README.NX2Apple.md).

### ⚖️ Legal

This repository contains code only. It contains no game files, keys or EA or Nintendo content: to use it you must own the game and dump your own files. EA SPORTS FC is a trademark of Electronic Arts; Nintendo Switch is a trademark of Nintendo. This project is not affiliated with or endorsed by either company.
