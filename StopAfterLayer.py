
from typing import List
import re
from UM.Application import Application
from UM.Logger import Logger
from ..Script import Script

class StopAfterLayer(Script):

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Stop after layer",
            "key": "StopAfterLayer",
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
                "comment_out":
                {
                    "label": "Comment out instead of removing",
                    "description": "Check to comment out the gcode instead of removing it.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enabled"
                },
                "layer_number":
                {
                    "label": "Layer",
                    "description": "After what layer the print should stop. All gcode after this layer will be removed.",
                    "unit": "",
                    "type": "str",
                    "default_value": "1",
                    "enabled": "enabled"
                },
                "macro":
                {
                    "label": "G-code",
                    "description": "Any custom G-code to run after stopping. Use {machine_end_gcode} to include the machine's end gcode. Use comma to separate commands.",
                    "unit": "",
                    "type": "str",
                    "default_value": "{machine_end_gcode}",
                    "enabled": "enabled"
                }
            }
        }"""

    def initialize(self) -> None:
        super().initialize()

    def execute(self, data: List[str]):
        """Removes all g-code at specific layer numbers.

        :param data: A list of layers of g-code.
        :return: A similar list, with g-code commands inserted.
        """
        enabled = self.getSettingValueByKey("enabled")
        comment_out = self.getSettingValueByKey("comment_out")
        layer_num = self.getSettingValueByKey("layer_number")
        macro = re.sub("\\s*,\\s*", "\n", self.getSettingValueByKey("macro"))

        if not enabled:
            return data

        try:
            layer_num = int(layer_num)
        except ValueError:
            Logger.log("e", f'Invalid layer number setting specified. Not an integer: {layer_num}')
            return data

        if("{machine_end_gcode}" in macro):
                machine_end_gcode = Application.getInstance().getGlobalContainerStack().getProperty("machine_end_gcode", "value")
                macro = macro.replace("{machine_end_gcode}", machine_end_gcode)
        Logger.log("d", f'{"Commenting out" if comment_out else "Removing"} all G-code after layer {layer_num} and inserting gcode: {macro}')

        convertedData = []
        layerAfterWasFound = False
        lastLayerWasFound = False
        lastLayerNum = 0
        for layer in data:
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
                        Logger.log("e", f'Could not convert LAYER "{currentLayerNum}" to int')
                        continue
                    
                    # note: First layer has currentLayerNum == 0
                    if currentLayerNum == layer_num:
                        layerAfterWasFound = True
                        convertedLines.append(f';BEGIN StopAfterLayer plugin, Stopping after {layer_num} layers\n')

                        if(macro.strip() != ""):
                            convertedLines.append(macro+"\n")
                    lastLayerNum = currentLayerNum
                elif line.startswith(";LAYER_COUNT:"):
                    layerCount = line[len(";LAYER_COUNT:"):]
                    try:
                        layerCount = int(layerCount)
                    # Couldn't cast to int. Something is wrong with this
                    # g-code data
                    except ValueError:
                        Logger.log("e", f'Could not convert LAYER_COUNT "{layerCount}" to int')
                        continue
                    if(layerCount > layer_num):
                       line = f';LAYER_COUNT:{layer_num}'
                if layerAfterWasFound:
                    if(comment_out):
                        convertedLines.append(f'; {line}')
                    else:
                        continue
                else:
                    convertedLines.append(line)
            if len(convertedLines) > 0:
                convertedData.append("\n".join(convertedLines))

        if lastLayerNum >= layer_num:
            if not layerAfterWasFound:
                Logger.log("i", f'Last layer was already {lastLayerNum + 1}. Not changing anything')
                return data
        else:
            Logger.log("w", f'Could not find layer {layer_num} in g-code data. Last layer was {lastLayerNum + 1}')
            return data
        
        removedNumberOfLayers = lastLayerNum - layer_num + 1
        convertedData.append(f';END StopAfterLayer plugin. {removedNumberOfLayers} {"layer" if removedNumberOfLayers == 1 else "layers"} removed\n')

        return convertedData
    
