
2023-09 xml fingerprint:

Paths:
  PcGts
  PcGts.Metadata
  PcGts.Metadata.Comment
  PcGts.Metadata.Created
  PcGts.Metadata.Creator
  PcGts.Metadata.LastChange
  PcGts.Metadata.MetadataItem[]
  PcGts.Metadata.MetadataItem[].Labels
  PcGts.Metadata.MetadataItem[].Labels.Label[]
  PcGts.Page
  PcGts.Page.ReadingOrder
  PcGts.Page.ReadingOrder.OrderedGroup
  PcGts.Page.ReadingOrder.OrderedGroup.RegionRefIndexed[]
  PcGts.Page.TextRegion[]
  PcGts.Page.TextRegion[].Coords
  PcGts.Page.TextRegion[].TextLine[]
  PcGts.Page.TextRegion[].TextLine[].Baseline
  PcGts.Page.TextRegion[].TextLine[].Coords
  PcGts.Page.TextRegion[].TextLine[].TextEquiv
  PcGts.Page.TextRegion[].TextLine[].TextEquiv.Unicode
  PcGts.Page.TextRegion[].TextLine[].TextStyle
  PcGts.Page.TextRegion[].TextLine[].Word[]
  PcGts.Page.TextRegion[].TextLine[].Word[].Coords
  PcGts.Page.TextRegion[].TextLine[].Word[].TextEquiv
  PcGts.Page.TextRegion[].TextLine[].Word[].TextEquiv.Unicode

Attributes:
  Baseline: points
  Coords: points
  Label: value, type
  Metadata: externalRef
  MetadataItem: value, name, type
  OrderedGroup: id
  Page: imageFilename, imageHeight, imageWidth
  PcGts: xmlns
  RegionRefIndexed: regionRef, index
  TextEquiv: conf
  TextLine: id
  TextRegion: custom, id
  TextStyle: xHeight
  Word: id

data/textrepo-data.csv : externalid,versionid,scanurl uit textrepo

- in /Volumes/ASMT 2105 Media/globalise/pagexml/2023-*/1.04.02/all-xml-files.lst een lijst van de xml bestanden
- er is een discrepantie: 
- 4802212 pagexml voor 2023-05
- 4784993 pagexml voor 2023-09

- alle pagexml verdelen in documenten:
- op https://github.com/globalise-huygens/annotation/tree/main/2024 staan csv's met scanranges voor sommige documenten 
- voor overige pagexml: per inv.nr.


# script for converting entity annotations in XMI (inception export) to web annotations

@Leon:
> Ik heb de tags nu ook maar als Concept gemodelleerd. De URI is steeds:
> https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/ + NER tag.
> Bijvoorbeeld:
> https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/SHIP
> Die URIs gaan gegarandeerd nog veranderen, maar dan staan ze er vast. Dus, je zou dit soort URIs op kunnen nemen in de annotaties.
> 
> De URIs van de eventtypes vind je voor nu in: https://github.com/globalise-huygens/annotation/blob/main/2023/inception/tagsets/events.json

---

inception: https://text-annotation.huc.knaw.nl/?2
----

Nog wat feedback over de WA's:
- TimeSpans hoeven geen URI te krijgen
- Kun je bij de generator waarde óók een D14_Software toevoegen als type?


Deze: https://ontome.net/class/487/namespace/211 ?
In welke context vind ik deze?
Ik verwachtte 'm in https://linked.art/ns/v1/linked-art.json  of desnoods https://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/contexts/aaao.json , maar daar zie ik 'm niet.

Kunnen daaraan:
Een crmdig:wasSoftwareOrFirmwareUsedBy met een linkje naar een D7_DigitalMachineEvent (https://ontome.net/class/480/namespace/211)

idem voor crmdig:wasSoftwareOrFirmwareUsedBy en D7_DigitalMachineEvent

Zo'n MachineEvent krijgt dan een timespanobject met de datum, en een _label.
En ook een Actor (of eigenlijk Group) eraan. Dat kan één URI zijn voor 'GLOBALISE Team' namens het hele project en iedereen die eraan meegewerkt heeft.
Een voorbeeld hiervan heb ik toegevoegd aan die Diagrams.net
Dan ook nog (voor later):

Bij de Classifications ontbreekt natuurlijk nog die ascribes_classification relatie, omdat we nog geen entity linking hebben gedaan. Op het moment dat we die waardes wel hebben, dan denk ik dat dat mooi met een AttributeAssignment kan. Ook dit staat in het Diagrams overzicht. Testdata hiervoor komt eraan.
Om die testdata te maken, zou ik graag alle entities op scan 797 verzamelen. Dan gaan wij die snel proberen te koppelen aan de referentiedata. In de sandbox/viewer/poc wordt dat dan het bruggetje naar een detailpagina voor zo'n entiteit. Maar, ik zag dat niet alle entiteiten die in INCEPTION zijn geannoteerd ook meegekomen zijn in de AnnotationPage die je nu hebt. Bijvoorbeeld genever. Enig idee waarom die ontbreekt? (samen met nog wat anderen)
DOC
In plaats van een AppellativeStatus moet dat een ClassificatoryStatus krijgen. Het is dan een verwijzing naar een documenttype naar onze Thesaurus.
CMDTY_NAME
De has_classificatory_subject mag naar een E54 Dimension verwijzen. We vergeten die Physical Thing even.
CMDTY_QUAL
Moet ik nog uitzoeken. Afhankelijk van of we die termen ook in onze thesaurus opnemen.
CMDTY_QUANT
Het zou mooi zijn om hier de boel uit te splitsen in een numerieke P90 value en een G4 Exchange Unit als waarde van de P91 has unit, die dan weer in een latere linking stap verbonden wordt aan de thesaurus. Maar, ik redeneer hier vanuit een soort ideale situatie. Ik weet niet hoe makkelijk dat is in de praktijk.
Wederom in een ideale wereld: dan komen we eraantoe om bovenstaande drie te groeperen in één Dimension. Die Dimension is dan in ieder geval het haakje.
Extra:
Omwille van de consistentie zou het handig kunnen zijn om bijvoorbeeld de body van een annotation altijd als array (van één, soms twee) te modelleren.
(edited)


---

2025-11-14

Leon:
Vraag over de herordende PageXML's (met bijbehorende XMI's):
Vergeleken met de eerdere PageXML (ook van data op Dataverse) ontbreken:
1996
2039
2040
2041
Daarvan kan ik geen pagexml en geen xmi vinden in HucDrive.
En van deze twee inventarisnummers heb ik wel een pagexml, maar geen xmi:
2022
2023
Zou je die nog kunnen maken/genereren en in HuCDrive kunnen zetten?

- in workspaces/globalise/globalise-tools
- `.local/missing-invnrs.lst`
```
for i in $(cat .local/missing-invnrs.lst); do cp -r ~/c/data/globalise/pagexml/$i .local/xml/; done
```
- 