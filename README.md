# globalise-tools

tools for globalise tasks


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