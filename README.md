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

## 📦 Come si costruisce

Servono **i tuoi file del gioco** (dump personali, non inclusi e non distribuiti qui): l'NSP base, l'aggiornamento v393216 (1.8d.310c), eventuale DLC della telecronaca e le tue chiavi `prod.keys`.

Requisiti: Mac con Apple Silicon, Xcode, Python 3, .NET 10 SDK (solo per ricompilare il traduttore).

```bash
# App per Mac
python3 scripts/build_ipa_from_nsp.py "<cartella con gli NSP>" --platform mac-app -k <prod.keys> -l it

# IPA per iPhone (con l'entitlement per la memoria estesa)
DM_ENTITLEMENTS=ios_entitlements.plist python3 scripts/build_ipa_from_nsp.py "<cartella con gli NSP>" --platform ios -k <prod.keys> -l it
```

L'IPA va installata insieme alla cartella `romfs` generata, come descritto nella [guida originale di NX2Apple](README.NX2Apple.md). Il profilo del gioco è in [`dm/games/0100C49025D3E000`](dm/games/0100C49025D3E000).

## ⚖️ Note legali

Questo repository contiene solo codice. Non contiene file del gioco, chiavi o contenuti di EA o Nintendo: per usarlo devi possedere il gioco ed estrarre tu i tuoi file. EA SPORTS FC è un marchio di Electronic Arts; Nintendo Switch è un marchio di Nintendo. Progetto non affiliato né approvato da nessuna delle due aziende.

---

## 🇬🇧 English

A fork of [NX2Apple](https://github.com/LNPANDY/NX2Apple) focused on **EA SPORTS FC 27 (Switch version) running natively on Apple Silicon Macs and iPhone at a locked 60 fps**, with every graphics bug found during the port fixed: dual-source blending for the Frostbite atmosphere pass (black career scenes), image atomics on buffer-texture views (light tile counters), the Maxwell `PRMT` instruction in the Ryujinx-based shader translator (blocky tiles on characters), and 16-bit shadow maps promoted to `Depth32Float` (speckled faces). Assets are the Switch ones: the project brings frame rate and a clean image, not PS5 graphics. Bring your own game dumps and keys; none are included. The original NX2Apple guide is in [README.NX2Apple.md](README.NX2Apple.md).
