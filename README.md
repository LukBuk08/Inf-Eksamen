# Sundhedsstyrelsen 2050

Et separat digitalt escape-room i Python/Pygame udviklet til opgave 8: **Escape Room for Sundhedsstyrelsen**.

Spillet foregaar i en taenkt fremtid, aar 2050, hvor Sundhedsstyrelsen arbejder med nye teknologiske muligheder inden for bioteknologi og digital sundhed. Spilleren skal gennem rum med dilemmaer om sundhedsdata, genetisk screening, adgang til behandling og overvaagning af borgere.

## Problemstilling

Hvordan kan Sundhedsstyrelsen i 2050 bruge genetiske data, personlig medicin og digitale sundhedsloesninger til at fremme sundhed og forebygge sygdom, uden at borgernes privatliv, retfaerdighed og selvbestemmelse bliver svaekket?

## Brugere

Maalgruppen er unge i undervisning, cirka 13-18 aar. Spillet er lavet som et engagerende it-system, hvor brugerne ikke bare laeser om dilemmaerne, men selv undersoeger rum, vurderer information og vaelger vej.

## Temaer

- Haandtering af sundhedsdata
- Genetisk screening
- Adgang til behandling
- Overvaagning af borgere
- Personlig medicin
- Datasikkerhed, samtykke og digital identitet

## Gameplay

- Start i en menu.
- Opret eller vaelg brugerprofil.
- Gaa rundt med WASD eller piletaster.
- Interager med objekter med E.
- Loes opgaver for at aabne doere.
- Vaelg en rute gennem Sundhedsstyrelsens fremtidsscenarie.
- Hver rute ender i sit eget afslutningsrum.

## Ruter og slutninger

- Dataarkiv -> Data-slutrum: haandtering af sundhedsdata
- Genetisk screening -> Screening-slutrum: genetisk screening og personlig medicin
- Behandlingsraadet -> Behandling-slutrum: adgang til behandling
- Behandlingsraadet -> Overvaagnings-slutrum: overvaagning af borgere

## Opgavetyper

Spillet bruger flere opgavetyper:

- skriv en kode, fx aarstallet 2050 eller et kodeord fra ledetraade
- multiple choice, hvor spilleren svarer med 1-4
- saet en raekkefoelge, fx proceskort eller trin i ansvarlig screening
- kombinationsopgaver, hvor spilleren skriver valgte numre med bindestreger

Der findes ogsaa en skjult udviklertest: Naar en bruger er logget ind, kan P aabne den naermeste laaste doer.

## Koer spillet

Installer Pygame:

```bash
pip install -r requirements.txt
```

Start spillet:

```bash
python main.py
```

## Data og gemning

Brugerdata gemmes lokalt i `profiles.json`. Her gemmes navn, progression, loeste opgaver, aabnede doere og valgt afslutning.

## Programmering og struktur

Programmet bruger objektorienteret programmering med blandt andet:

- `Game`
- `UserProfile`
- `Player`
- `Room`
- `Door`
- `Interactable`
- `Quiz`

## Testforslag

1. Start spillet med `python main.py`.
2. Opret en ny bruger.
3. Tjek at profilen gemmes i `profiles.json`.
4. Proev mindst to forskellige ruter.
5. Tjek at doere foerst aabner efter opgaver.
6. Tjek at spilleren fysisk kan gaa gennem aabne doere.
7. Tjek at hver rute ender i et forskelligt slutrum.
8. Brug P til hurtigt at teste laaste ruter under udvikling.

## Grafik

Spillet bruger egne pixel-art objekter tegnet direkte med Pygame-rects og simple former. Der kraeves derfor ingen eksterne sprite-filer for at koere spillet.
