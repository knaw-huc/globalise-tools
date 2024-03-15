
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
- - op https://github.com/globalise-huygens/annotation/tree/main/2024 staan csv's met scanranges voor sommige documenten
- - voor overige pagexml: per inv.nr.


# script for converting entity annotations in XMI (inception export) to web annotations

@Leon:
> Ik heb de tags nu ook maar als Concept gemodelleerd. De URI is steeds:
> https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/ + NER tag.
> Bijvoorbeeld:
> https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/SHIP
> Die URIs gaan gegarandeerd nog veranderen, maar dan staan ze er vast. Dus, je zou dit soort URIs op kunnen nemen in de annotaties.
> 
> De URIs van de eventtypes vind je voor nu in: https://github.com/globalise-huygens/annotation/blob/main/2023/inception/tagsets/events.json