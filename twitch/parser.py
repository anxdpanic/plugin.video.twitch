# -*- encoding: utf-8 -*-

from twitch.keys import QUALITY_LIST_STREAM


class M3UPlaylist(object):
    def __init__(self, source, qualityList=QUALITY_LIST_STREAM):
        self.playlist = dict()
        self.qualityList = qualityList

        def parse_quality(ExtXMediaLine, ExtXStreamInfLine, Url):
            # find name of current quality, NAME=", 6 chars
            namePosition = ExtXMediaLine.find('NAME')
            if(namePosition == -1):
                raise ValueError('Unexpected Exception; '
                                 'M3UPlaylist')
            qualityString = ''
            namePosition += 6
            for char in ExtXMediaLine[namePosition:]:
                if(char == '"'):
                    break
                qualityString += char
            return qualityString, Url

        lines = source.splitlines()
        linesIterator = iter(lines)
        for line in linesIterator:
            if(line.startswith('#EXT-X-MEDIA')):
                quality, url = parse_quality(
                        line,
                        next(linesIterator),
                        next(linesIterator))
                qualityInt = self.qualityList.index(quality)
                self.playlist[qualityInt] = url
        if not self.playlist:
            # playlist dict is empty
            raise ValueError('could not find playable urls')

    # returns selected quality or best match if not available
    def get_quality(self, selectedQuality):
        if(selectedQuality in self.playlist.keys()):
            # selected quality is available
            return self.playlist[selectedQuality]
        else:
            # not available, calculate differences to available qualities
            # return lowest difference / lower quality if same distance
            bestDistance = len(self.qualityList) + 1
            bestMatch = None

            for quality in sorted(self.playlist, reverse=True):
                newDistance = abs(selectedQuality - quality)
                if newDistance < bestDistance:
                    bestDistance = newDistance
                    bestMatch = quality

            return self.playlist[bestMatch]

    def __str__(self):
        return repr(self.playlist)
