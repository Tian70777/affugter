### 1.1 Baggrund
Smart home-teknologi (SHT) er i hastig vækst, og Danmark er blandt frontløberne inden for EU. I 2024 anvendte 73,38 % af befolkningen internetforbundne fjernsyn, men kun 17,44 % anvendte internetforbundne energistyringssystemer (Eurostat).

En analyse af barriererne for anvendelsen af IoT viser, at 2,41 % angiver manglende kendskab til IoT systemerne som årsag. 7,51 % peger på høje omkostninger og 5,57 % på manglende kompetencer. Dog ser 34,78 % ikke et behov for anvendelsen af SHT (Eurostat, 2024, Internet of Things - barriers to use). Den største barriere er dermed hverken pris eller kompetencer, men at behovet ikke opleves. 

En undersøgelse af Hansen et al. (2024) identificerer tre gennemgående kendetegn ved SHT, herunder at enhederne er forbundne. Mange husholdningsapparater, som allerede er i brug, er derfor pr. definition uden for SHT. Forbindelsen kan imidlertid tilføjes udefra, uden at apparatet selv ændres. Den mulighed er blot ikke synlig for brugeren, og heri ligger et synlighedsproblem.

Dette projekt undersøger derfor, hvordan ikke-smarte husholdningsapparater generelt kan gøres i stand til at indgå i automatiseret styring.

### 1.2 Case
Projektet tager udgangspunkt i en konkret case fra gruppen. Casen er valgt, fordi den giver direkte adgang til brugeren gennem hele forløbet.

Casen omhandler et værelse, hvor der om vinteren opstår skimmel i to hjørner i loftet. Den relative luftfugtighed ligger typisk over 68 %.

For at løse problemet blev der anskaffet en affugter. Den skal som regel køre i over tre timer for at sænke luftfugtigheden til under 50 %. På hverdage falder disse timer i det tidsrum, hvor elprisen er højest på dagen - mindst tre gange dyrere end i døgnets billigste timer.

Behovet for at kunne fjernstyre affugteren opstod først, efter at den havde været anvendt i en periode. Affugteren kan imidlertid ikke self tilsluttes et netværk og har hverken app, API eller mulighed for at tilføje en wifi-komponent. Husstanden råder i forvejen over robotstøvsuger og robotplæneklipper. Alligevel indgik netværksfunktion ikke i overvejelserne ved købet af affugteren.

Casen er ikke enestående. Den illustrerer dermed det mønster, som Eurostat-tallene viser: behovet blev ikke set på købstidspunktet, men opstod først gennem brug. 

### 1.3 Problemformulering og afgrænsing
Hvordan kan ikke-smarte husholdningsapparater styres ud fra både elprisen og brugerens faktiske behov?

Projektet afgrænses til en ikke-smart affugter (eeese, model: Emil 2508). Vi undersøger, om det er muligt at få den til automatisk at tænde og slukke baseret på elprisen og fugtighedsniveauet i rummet — uden at ændre på selve apparatet.


### Reference:
Internet of Things – barriers to use, Eurostat, 
https://ec.europa.eu/eurostat/databrowser/view/isoc_iiot_bx/default/table?lang=en&category=isoc.isoc_i.isoc_iiot

Internet of Things – use, Eurostat, 
https://ec.europa.eu/eurostat/databrowser/view/isoc_iiot_use/default/table?lang=en

Hansen, A. R., Trotta, G., & Gram-Hanssen, K. (2024). Smart home technology adoption in Denmark: Diffusion, social differences, and energy consumption. Energy Efficiency, 17(16). https://doi.org/10.1007/s12053-024-10202-3
