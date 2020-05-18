import appdaemon.plugins.hass.hassapi as hass
import time, json

class padKeys(hass.Hass):

    def initialize(self):
        self.listen_state(self.key, self.args["key"])

    def key(self, entity, attribute, old, new, kwargs):
        if "key" in new:
            self.log("key".ljust(11, ".")+": " + new)
            jsoncode = json.loads(new)
            key = jsoncode["key"]
            if key in self.args["keys"]:

                self.log("entity from".ljust(11, ".")+": " + entity)
                c = self.args["keys"][key]

                if "condition" in c:
                    c = c["condition"]
                    if "entity_id" in c and "state" in c:
                        if self.get_state(c["entity_id"].strip(), attribute = "state") == c["state"].strip():
                            self.log("Condition met!")
                        else: 
                            self.call_service(self.args["message_service"].replace(".","/"), text = c["alert"])
                            return

                c = self.args["keys"][key]
                if "entity_id" in c:
                    self.log("entity_id".ljust(11, ".")+": " + c["entity_id"])
                if "service" in c:
                    self.log("service".ljust(11, ".")+": " + c["service"])
                if "message" in c:
                    self.log("message".ljust(11, ".")+": " + c["message"])

                if "entity_id" in c:
                    state1 = self.get_state(c["entity_id"].strip(), attribute = "all")
                else: state1 = self.get_state(c["service"].strip(), attribute = "all")

                if "entity_id" in c:
                    self.call_service(c["service"].strip().replace(".","/"), entity_id = c["entity_id"])
                else: self.call_service(c["service"].strip().replace(".","/"))

                time.sleep(0.5)
                
                if "entity_id" in c:
                    state2 = self.get_state(c["entity_id"].strip(), attribute = "all")
                else: state2 = self.get_state(c["service"].strip(), attribute = "all")

                if state1:
                    if "message" in c:
                        mes = c["message"].format(state1["state"], state2["state"])
                    else: 
                        if "service" in c and c["service"].split('.')[0] in ['switch', 'light']:
                            mes = state2["attributes"]["friendly_name"] + "*turned " + state2["state"] + "*from " + state1["state"] + "!"
                            self.log(mes)
                        else: mes = state2["attributes"]["friendly_name"] + "*executed!*"
                    self.log(self.args["message_service"])
                    self.call_service(self.args["message_service"].replace(".","/").strip(), text = mes)
            
            else: 
                r = "Key "+jsoncode["key"]+" not defined!"
                self.log(r)
                r = r.replace(" ","*")
                self.call_service(self.args["message_service"].replace(".","/"), text = r)
        else: 
            self.log("Received something but not a key!")

