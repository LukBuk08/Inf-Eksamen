# Projektbeskrivelse: Sundhedsstyrelsen 2050

## Opgave

Der er udviklet et digitalt escape-room for Sundhedsstyrelsen. Escape-roomet foregaar i en taenkt fremtid, aar 2050, og handler om nye teknologiske muligheder inden for bioteknologi og digital sundhed.

## Problemstilling

Hvordan kan Sundhedsstyrelsen bruge genetiske data, personlig medicin og digitale sundhedsloesninger til at fremme sundhed og forebygge sygdom, samtidig med at borgernes privatliv, retfaerdighed og selvbestemmelse beskyttes?

## Brugere

Brugerne er unge i undervisning. De skal kunne forstaa baade muligheder og risici ved fremtidens sundhedsteknologi. Derfor bruger spillet korte tekster, dilemmaer, pixel-art og interaktive opgaver.

## Design

Spillet er et top-down 2D pixel-art escape-room. Brugeren styrer en figur gennem rum, finder ledetraade, loeser opgaver og vaelger mellem forskellige veje. Valgene er ikke-lineaere, fordi ruterne foerer til forskellige afslutninger.

Opgaverne er varierede. Nogle kraever at brugeren skriver en kode, nogle er multiple choice med 1-4, og nogle kraever at brugeren saetter procestrin i den rigtige raekkefoelge.

## Flere mulige slutninger

Spillet har fire centrale slutninger:

- Haandtering af sundhedsdata
- Genetisk screening
- Adgang til behandling
- Overvaagning af borgere

Hver slutning forklarer kort, hvorfor teknologien kan blive vigtig i 2050, og hvilket dilemma den skaber.

## Informatikfaglige elementer

Programmet modellerer data i brugerprofiler og gemmer progression i JSON. Det bruger objektorienteret programmering, interaktionsdesign, brugerinput, lokal datalagring og grafisk brugerflade med Pygame.

## Brugertest

Loesningen kan testes ved at lade en bruger:

1. Oprette en profil.
2. Navigere med tastaturet.
3. Loese en opgave.
4. Gaa gennem en aaben doer.
5. Vaelge forskellige ruter.
6. Vurdere om opgaverne er forstaaelige og engagerende.

## Innovation

Loesningen er mere engagerende end en almindelig tekst eller quiz, fordi brugeren selv udforsker et scenarie og oplever konsekvenserne af sine valg. Spillet bruger escape-room-formen til at kombinere laering, dilemmaer og programmering.
