
from typing import List
import re
from ..Script import Script
from UM.Logger import Logger

class InsertGCodeAtLayer(Script):

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Insert G-Code at layer",
            "key": "InsertGCodeAtLayer",
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
                "layer_number":
                {
                    "label": "Layer",
                    "description": "At what layer the gcode should be inserted. This will be before the layer starts printing. Specify multiple layers with a comma.",
                    "unit": "",
                    "type": "str",
                    "default_value": "1",
                    "enabled": "enabled"
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
        layer_nums = self.getSettingValueByKey("layer_number")
        macro = re.sub("\\s*,\\s*", "\n", self.getSettingValueByKey("macro"))

        if not enabled:
            return data


        layerNumbers = [int(num) for num in layer_nums.split(',') if num.strip().isdigit()]
        Logger.log("d", f'Inserting G-code at layers: {layerNumbers}: {macro}')

        if len(layerNumbers) > 0:
            for index, layer in enumerate(data):
                lines = layer.split("\n")
                convertedLines = []
                for line in lines:

                    if line.startswith(";LAYER:"):
                        
                        currentLayerNum = line[len(";LAYER:"):]
                        try:
                            currentLayerNum = int(currentLayerNum)

                        # Couldn't cast to int. Something is wrong with this
                        # g-code data
                        except ValueError:
                            continue

                        if currentLayerNum in layerNumbers:
                            gcode = f';BEGIN InsertGCodeAtLayer plugin, Layer {currentLayerNum}\n{macro}\n;END InsertGCodeAtLayer plugin\n'
                            line = gcode + line
                    convertedLines.append(line)
                data[index] = "\n".join(convertedLines)

        return data
    
