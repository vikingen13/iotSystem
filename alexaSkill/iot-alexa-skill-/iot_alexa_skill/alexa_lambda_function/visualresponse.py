APL_DOCUMENT_ID = "TempDisplay"

APL_DOCUMENT_TOKEN = "documentToken"

#class to handle visual response
class VisualResponse:
    def __init__(self):
        self.theResponse = DATASOURCE

    def getResponse(self):
        return self.theResponse
    
    def setTitle(self, aTitle):
        self.theResponse["textListData"]["title"] = aTitle

    def setBackgroundImage(self, aUrl):
        self.theResponse["textListData"]["backgroundImage"]["sources"][0]["url"] = aUrl
    
    def addListItem(self, aPrimaryText):
        self.theResponse["textListData"]["listItems"].append({
            "primaryText": aPrimaryText            
        })

    def emptyListItem(self):
        self.theResponse["textListData"]["listItems"] = []

    def setLogo(self, aUrl):
        self.theResponse["textListData"]["logoUrl"] = aUrl

DATASOURCE = {
    "textListData": {
        "type": "object",
        "objectId": "textListSample",
        "backgroundImage": {
            "contentDescription": None,
            "smallSourceUrl": None,
            "largeSourceUrl": None,
            "sources": [
                {
                    "url": "",
                    "size": "large"
                }
            ]
        },
        "title": "",
        "listItems": [            
'''            {
                "primaryText": "Peonies & Petals Nursery",
                "primaryAction": [
                    {
                        "type": "SetValue",
                        "componentId": "plantList",
                        "property": "headerTitle",
                        "value": "${payload.textListData.listItems[0].primaryText} is selected"
                    }
                ]
            }'''
        ],
        "logoUrl": ""
    }
}