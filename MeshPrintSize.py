# From https://gist.github.com/frankbags/c85d37d9faff7bce67b6d18ec4e716ff
# Replaces all occurrences %MINX% %MINY% %MINZ% %MAXX% %MAXY% %MAXZ% with the size of the mesh in the GCODE
# Install this as Post processing script in Cura
import re #To perform the search and replace.

from ..Script import Script


class MeshPrintSize(Script):

    def getSettingDataString(self):
        return """{
            "name": "Insert Mesh Print Size",
            "key": "MeshPrintSize",
            "metadata": {},
            "version": 2,
            "settings":{}
        }"""

    def execute(self, data):
            minMaxXY = {'MINX':0,'MINY':0,'MINZ':0,'MAXX':0,'MAXY':0,'MAXZ':0,}
            lineData = ''

            for layer_number, layer in enumerate(data):
                for k,v in minMaxXY.items():
                    result = re.search(str(k)+":(\d*\.?\d*)",layer)
                    if result is not None:
                        minMaxXY[k] = result.group(1)

                areaStartGcode = re.search(".*%(MINX|MAXX|MINY|MAXY|MINZ|MAXZ)%.*",layer)

                if areaStartGcode is not None:
                    if not lineData:
                        lineData = layer
                    for k, v in minMaxXY.items():    
                        pattern3 = re.compile('%' + k + '%')
                        lineData = re.sub(pattern3, v, lineData)
                    
                    data[layer_number] = lineData
        
                                         
            return data