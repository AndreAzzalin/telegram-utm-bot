PROGETTO PYTHON

**Dominio**

bot telegram che inserito all'interno di un group chat monitora la posizione geografica di ogni partecipante 
e converte la posizione in UTM WSG84(uno dei map datum più utilizzati e comodi in ambito cartografico)

**Funzionamento**  

L'admin del gruppo attiva il bot, i componenti del gruppo condividono la loro posizione iniziale

**Comandi**

`/start`avvia il trac

**Librerie utilizzate**

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) : interfaccia python per le API telegram
- [utm](https://github.com/Turbo87/utm) : convertitore da formato posizione "latitudine longitudine" a UTM WGS84