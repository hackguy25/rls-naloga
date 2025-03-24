# Poskusna naloga za zaposlitev na podjetju RLS

Ta repozitorij vsebuje izvorno kodo programa z grafičnim vmesnikom za enkoder [AksIM-2](https://www.rls.si/eng/aksim-2-off-axis-rotary-absolute-encoder).
Grafični vmesnik je spisan v programskem jeziku Python, z uporabo knjižnice [tkinter](https://docs.python.org/3/library/tkinter.html).
Programska oprema za razvojni board Nucleo je spisana v programskem jeziku C v okolju [STM32CubeIDE](https://www.st.com/en/development-tools/stm32cubeide.html).

## Programske zahteve in odvisnosti

Za razvojni board:
- Relativno sveža verzija okolja SMT32CubeIDE.

Za grafični vmesnik:
- Namestitev programskega jezika Python z vključeno tkinter knjižnico (<https://stackoverflow.com/a/76012964>)
- Python knjižnica Pyserial (<https://pyserial.readthedocs.io/en/latest/pyserial.html#installation>)

## Priklop enkoderja na Nucleo board

- SCK na D10
- MOSI na D11
- MISO na D12
- NCS na D13
- temp1 in temp2 nista v uporabi
- ostalo (5V, GND, shield) na primerne pine

## Izvajanje

1. V okolju STM32CubeIDE prevedi kodo v mapi `nucleo` in jo flashaj na Nucleo board.
   - Če je enkoder pravilno priključen na board, se prek serijca izpisujejo meritve vsako sekundo, ali po vsakem pritisku katerekoli tipke.
2. V `gui/gui.py` popravi vrstico `SERIAL_DEVICE_PATH = ...` (na vrhu datoteke) tako, da bo kazala na serijska vrata Nucleo boarda.
3. Zaženi `python gui/gui.py` v terminalu.

## Opomba

Ta program je bil spisan in testiran na računalniku z operacijskim sistemom Linux (Fedora).
Spisan je tako, da bi moral brez težav delati tudi na operacijskem sistemu Windows, a tega nisem uspel testirati.
