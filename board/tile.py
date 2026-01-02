class Tile:

    pieceonTile= None
    tileCoordinate= None

    def __init__(self,coordinate, piece):
        self.tileCoordinate=coordinate
        self.pieceonTile=piece