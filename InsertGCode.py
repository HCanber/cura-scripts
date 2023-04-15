
from typing import List
import re
from ..Script import Script
from UM.Logger import Logger

class InsertGCode(Script):

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Insert G-Code",
            "key": "InsertGCode",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enabled":
                {
                    "label": "Enable",
                    "description": "Uncheck to temporarily disable this feature.",
                    "type": "bool",
                    "default_value": true
                },
                "location":
                {
                    "label": "Location",
                    "type": "enum",
                    "options": {
                        "layers": "Layers", 
                        "heights": "Heights", 
                        "end": "At end of gcode",
                        "start": "At start of gcode",
                        "beforeFirstLayer": "Before first layer",
                        "afterLastLayer": "After last layer"
                    },
                    "description": "Where to insert the g-code.",
                    "default_value": "layers",
                    "enabled": "enabled"
                },
                "layer_nums":
                {
                    "label": "Layers",
                    "description": "At what layers the gcode should be inserted. Specify multiple layers with a comma, and ranges using -. Example: 4,6-8",
                    "unit": "",
                    "type": "str",
                    "default_value": "10-",
                    "enabled": "enabled and location == 'layers'"
                },
                "height_nums":
                {
                    "label": "Layers at heights",
                    "description": "At what z heights [mm] the gcode should be inserted. Specify multiple values with a comma, and ranges using -. Example: 4,6-8",
                    "unit": "mm",
                    "type": "str",
                    "default_value": "5-10",
                    "enabled": "enabled and location == 'heights'"
                },
                "insert_location":
                {
                    "label": "When to insert",
                    "description": "Whether to insert code before or after layer change.",
                    "type": "enum",
                    "options": {"before": "Before", "after": "After"},
                    "default_value": "after",
                    "enabled": "enabled and (location == 'layers' or location == 'heights')"
                },
                "macro":
                {
                    "label": "G-code",
                    "description": "Any custom G-code to run at specified layers. For example: M300 S1000 P10000 for a long beep. Use comma to separate commands.",
                    "unit": "",
                    "type": "str",
                    "default_value": "M300 S1000 P10000",
                    "enabled": "enabled"
                }
            }
        }"""

    def initialize(self) -> None:
        super().initialize()

    def execute(self, data: List[str]):
        """Inserts g-code at specific layer numbers.

        :param data: A list of layers of g-code.
        :return: A similar list, with g-code commands inserted.
        """
        enabled = self.getSettingValueByKey("enabled")

        if not enabled:
            return data

        macro = re.sub("\\s*,\\s*", "\n", self.getSettingValueByKey("macro"))
        insert_location = self.getSettingValueByKey("insert_location")
        heightRanges = []
        layerRanges = []
        match self.getSettingValueByKey("location"):
            case "end":
                Logger.log("d", f'Inserting G-code at end of gcode: {macro}')
                gcode = f';BEGIN InsertGCodeAtLayer plugin\n{macro}\n;END InsertGCodeAtLayer plugin\n'
                data[-1] = data[-1] + gcode
                return data
            case "start":
                Logger.log("d", f'Inserting G-code at start of gcode: {macro}')
                gcode = f';BEGIN InsertGCodeAtLayer plugin\n{macro}\n;END InsertGCodeAtLayer plugin\n'
                data[0] = gcode + data[0]
                return data
            case "layers":
                layerRanges = self.convertLayerSpecToRanges(self.getSettingValueByKey("layer_nums"))
                Logger.log("d", f'Inserting G-code {insert_location} layers: {self.rangesToStr(layerRanges)}: {macro}')
            case "heights":
                heightRanges = self.convertLayerSpecToRanges(self.getSettingValueByKey("height_nums"))
                Logger.log("d", f'Inserting G-code {insert_location} heights: {self.rangesToStr(heightRanges)} mm: {macro}')
            case "beforeFirstLayer":
                Logger.log("d", f'Inserting G-code before first layer: {macro}')
                layerRanges = [(0,0)]
                insert_location = "before"
            case "afterLastLayer":
                Logger.log("d", f'Inserting G-code after last layer: {macro}')
                layerRanges = [(float('inf'),float('inf'))]
                insert_location = "after"
            case _:
                Logger.log("e", f'Unknown location: {self.getSettingValueByKey("location")}')
                return data
                

        # Logger.log("d", f'Before preprocess data: {data}')
        layers = self.preprocessGCode(data)
        # Logger.log("d", f'Preprocessed {len(layers)} layers: {layers}')

        result = []
        for (layerNum, currentZ, lines) in layers:
            if(self.is_within_range(layerRanges, layerNum) or self.is_within_range(heightRanges, currentZ, False)):
                gcode = f'\n;BEGIN InsertGCode plugin, Layer {layerNum}, Height {currentZ} mm\n{macro}\n;END InsertGCodeAtLayer plugin\n\n'
                if self.getSettingValueByKey("insert_location") == "before":
                    result.append(lines[0])
                    result.append(gcode)
                    result.extend(lines[1:])
                else:
                    result.extend(lines)
                    result.append(gcode)
            else:
                result.extend(lines)
        # Logger.log("d", f'Result: {result}')
        
        return result

    def convertLayerSpecToRanges(self, layerSpec: str):
        layerSpec = layerSpec.replace(" ", "")
        ranges = layerSpec.split(",")
        result = []
        for r in ranges:
            # If the range contains only a single number, treat it as a range from that number to itself
            if "-" not in r:
                num = float(r)
                result.append((num, num))
            else:
                from_val, to_val = map(lambda x: float(x) if x != "" else None, r.split("-"))
                if from_val is None:
                    from_val = 0
                if to_val is None:
                    to_val = float('inf')
                result.append((from_val, to_val))
        return result
    
    def rangesToStr(self, ranges):
        output = []
        for r in ranges:
            if r[0] == r[1]:
                output.append(str(r[0]))
            else:
                output.append(f"{r[0]}-{r[1]}")
        return ", ".join(output)
    
    def is_within_range(self, ranges, number, inclusiveEnd = True):
        for from_val, to_val in ranges:
            if from_val <= number:
                if(inclusiveEnd):
                    return number <= to_val 
                return number < to_val
        return False

    def preprocessGCode(self, data: List[str]):
        currentLayerNum = -1
        currentZ = -1
        result = []
        currentLines = []
        for d in data:
            # Ignore trailing new line
            lines = (d[:-1] if d.endswith("\n") else d).split("\n")
            for line in lines:
                if line.startswith(";LAYER:"):
                    # New layer, so add the current lines to the result
                    result.append((currentLayerNum, currentZ, currentLines))
                    currentLines = []
                    currentLayerNum = int(line[len(";LAYER:"):]) + 1
                    # Logger.log("d", f'Layer number: {currentLayerNum}, Line={line}')
                else:
                    if line.startswith("G0 ") or line.startswith("G1 "):
                        # Get Z component from G0/G1 command
                        zNumReg=r"Z(?P<z>\d+(?:.\d+)?)"
                        zNumMatch=re.search(zNumReg, line)
                        if zNumMatch:
                            currentZ=float(zNumMatch.group("z"))
                            # Logger.log("d", f'Z component in G0/G1 command: {currentZ} mm')
                        else:
                            # Log if we didn't find a Z component but a Z exists in the line
                            if "Z" in line:
                                Logger.log("w", f'No Z component found in G0/G1 command: {line}')
                currentLines.append(line + "\n")
        if(len(currentLines) > 0):
            result.append((currentLayerNum, currentZ, currentLines))
        return result