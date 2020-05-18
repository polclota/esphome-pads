import appdaemon.plugins.hass.hassapi as hass
import time
import json
import requests
from datetime import datetime

class padCodes(hass.Hass):

    def initialize(self):
        self.listen_state(self.exec, self.args["code"])

    def exec(self, entity, attribute, old, new, kwargs):
        self.log(new)
        if "code" in new:
            jsoncode = json.loads(new)
            code = jsoncode["code"]
            self.log("domIoT codes checker")
            self.log("Code: '" + code + "'")
            if len(code)==6:
                if not self.Nuki(code):
                    r = "Nuki code not found, checking other!"
                    self.log(r)
                    r = r.replace(" ","*")
                    self.call_service(self.args["message_service"].replace(".","/"), text = r)
                else: return
            if not self.codes(code):
                r = "Code not found!"
                self.log(r)
                r = r.replace(" ","*")
                self.call_service(self.args["message_service"].replace(".","/"), text = r)

    def codes(self, code):
        self.log("Checking within the rest!")
        if not code in ['unavailable', 'unknown']:
            optL = code[-1:]
            if optL in ['#']:
                code = code[0:-1]
                lcode = float(code)
                c = self.args["codes"]
                if lcode in c:
                    c = self.args["codes"][lcode]
                else: return False
                c = c["options"]
                r = "OPTIONS*"
                for o in c:
                    if c[o]: r += o+":"+c[o]["name"]+"*"
                self.call_service(self.args["message_service"].replace(".", "/"), text=r)
                return True
            if not optL in ['A','B','C','D']:
                lcode = float(code)
                c = self.args["codes"]
                if lcode in c:
                    c = self.args["codes"][lcode]
                else: return False
                c = c["options"]
                r = ""
                for o in c:
                    if c[o]: r += o+":"+c[o]["name"]+"*"
                self.call_service(self.args["message_service"].replace(".", "/"), text=r)
                return True
            code = code[0:-1]
            if code:
                lcode = float(code)
                if lcode in self.args["codes"]:
                    c = self.args["codes"][lcode]
                    if "options" in c:
                        c = c["options"]
                        r = ""
                        for o in c:
                            if c[o]:
                                if c[o]["ha"]:
                                    if optL==o:
                                        c = c[o]["ha"]
                                        if "entity_id" in c:
                                            self.log("entity_id".ljust(11, ".")+": " + c["entity_id"])
                                        if "service" in c:
                                            self.log("service".ljust(11, ".")+": " + c["service"])
                                        if "message" in c:
                                            self.log("message".ljust(11, ".")+": " + c["message"])

                                        if "entity_id" in c:
                                            state1 = self.get_state(
                                                c["entity_id"].strip(), attribute="all")
                                        else:
                                            state1 = self.get_state(
                                                c["service"].strip(), attribute="all")

                                        if "entity_id" in c:
                                            self.call_service(c["service"].strip().replace(
                                                ".", "/"), entity_id=c["entity_id"])
                                        else:
                                            self.call_service(c["service"].strip().replace(".", "/"))
                                        
                                        time.sleep(0.5)

                                        if "entity_id" in c:
                                            state2 = self.get_state(
                                                c["entity_id"].strip(), attribute="all")
                                        else:
                                            state2 = self.get_state(
                                                c["service"].strip(), attribute="all")

                                        if state1:
                                            if "message" in c:
                                                mes = c["message"].format(state1["state"], state2["state"])
                                            else:
                                                if "service" in c and c["service"].split('.')[0] in ['switch', 'light']:
                                                    mes = state2["attributes"]["friendly_name"] + "*turned " + \
                                                        state2["state"] + "*from " + \
                                                        state1["state"] + "!"
                                                    self.log(mes)
                                                else:
                                                    mes = state2["attributes"]["friendly_name"] + \
                                                        "*executed!*"
                                            self.call_service(
                                                self.args["message_service"].replace(".", "/"), text=mes)

                                        return True
                else: return False
            else: return False
        else: return False

    def Nuki(self, code):
        self.log("Checking within Nuki ones!")
        lock = self.args["nuki"]["lock"]
        bearer = self.args["nuki"]["bearer"]
        action_ok = self.args["nuki"]["action_ok"]
        action_ko = self.args["nuki"]["action_ko"]
        dateFormat = '%Y-%m-%dT%H:%M:%S.%f%z'
        name = ""

        URL = "https://api.nuki.io/smartlock/" + lock + "/auth"

        HEADERS = {'Accept': 'application/json',
                   'Authorization': 'Bearer ' + bearer}

        r = requests.get(url=URL, headers=HEADERS)
        if r:
            Nuki = json.loads(r.text)
            checkOk = False
            outOfdates = False
            for c in range(len(Nuki)):
                if not checkOk and "code" in Nuki[c].keys() and Nuki[c]["enabled"] and int(code) == Nuki[c]["code"]:
                    checkOk = True
                    if "name" in Nuki[c].keys() and not name:
                        name = Nuki[c]["name"]
                    if "allowedFromDate" in Nuki[c].keys() and "allowedUntilDate" in Nuki[c].keys():
                        outOfdates = not (datetime.utcnow().timestamp() >= datetime.strptime(Nuki[c]["allowedFromDate"], dateFormat).timestamp()
                                          and datetime.utcnow().timestamp() <= datetime.strptime(Nuki[c]["allowedUntilDate"], dateFormat).timestamp())
                        self.log("outOfdates: " + str(outOfdates))
                    else:
                        if "allowedFromDate" in Nuki[c].keys():
                            outOfdates = not datetime.utcnow().timestamp() >= datetime.strptime(
                                Nuki[c]["allowedFromDate"], dateFormat).timestamp()
                        if "allowedUntilDate" in Nuki[c].keys():
                            outOfdates = not datetime.utcnow().timestamp() <= datetime.strptime(
                                Nuki[c]["allowedUntilDate"], dateFormat).timestamp()
        else:
            self.log(r)

        d = "Code*"
        if checkOk and not outOfdates:
            d += "correct*Wellcome*" + name + "!"
            self.turn_on(action_ok)
            xt = True
        else:
            if outOfdates:
                d += "out of date*Please*renew it!"
            else:
                d += "not found*Please*retry!"
            self.turn_on(action_ko)
            xt = False

        self.call_service(self.args["message_service"].replace(".", "/"), text=d)
        d = d.replace("*", " ")
        self.log(d)
        self.call_service("persistent_notification/create", message=d,
                          notification_id="nukiCode")
        time.sleep(10)
        self.call_service("persistent_notification/dismiss",
                          notification_id="nukiCode")
        return xt