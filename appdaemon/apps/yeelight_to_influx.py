from datetime import datetime
from datetime import timedelta
import appdaemon.plugins.hass.hassapi as hass
from influxdb import InfluxDBClient, exceptions

#
# Hellow World App
#
# Args:
#

class YeelightMetricsToInflux(hass.Hass):
    def initialize(self):
        self.log("Opening InfluxDB connection")
        self.influx_client = InfluxDBClient(self.args["influx_host"],
                            self.args["influx_port"],self.args["influx_user"],
                            self.args["influx_password"],self.args["influx_db"])
        self.log("Opened InfluxDB connection")
        
        # execute function every 10 sec
        # self.run_every(self.yeelight_to_influx_main, datetime.now(), 10)

        for entity_id in self.args["entities"]:
            self.listen_state(self.yeelight_to_influx_main, entity_id)

    # Select the last value of the old state from entity measurement of the influxdb where the
    # and convert it to dictionary which will be returned value
    def get_last_value_from_influx(self, entity, state):
        # entity = light.bathroom_ceilinglight_1
        query = 'SELECT * FROM "{0}" WHERE state = \'{1}\' ORDER BY DESC LIMIT 1'.format(entity, state)
        result = self.influx_client.query(query)
        zip_iterator = zip(result.raw['series'][0]['columns'], result.raw['series'][0]['values'][0])
        return dict(zip_iterator)

    def yeelight_to_influx_main(self, entity, attribute, old, new, kwargs=None):
        entity_id = entity
        ha_metric = self.get_state(entity_id, attribute = "all")
        influx_metric = self.get_last_value_from_influx(entity_id, old)

        if (old == "on" or old == "off") and new == "unavailable":
            metric = [
            {
                "measurement": entity_id,
                "time": str((datetime.utcnow() - timedelta(0,1)).strftime('%Y-%m-%d %H:%M:%SZ')),
                "tags": {
                    "domain": entity_id.split(".")[0],
                    "entity_id": entity_id.split(".")[1],
                },
                "fields": {
                    "brightness": influx_metric["brightness"],
                    "color_temp": influx_metric["color_temp"],
                    "effect_list_str": influx_metric["effect_list_str"],
                    "flowing": influx_metric["flowing"],
                    "friendly_name_str": influx_metric["friendly_name_str"],
                    "max_mireds": influx_metric["max_mireds"],
                    "min_mireds": influx_metric["min_mireds"],
                    "night_light": influx_metric["night_light"],
                    "state": influx_metric["state"],
                    "supported_features": influx_metric["supported_features"],
                    "value": influx_metric["value"]
                }
            },
            {
                "measurement": entity_id,
                "time": str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')),
                "tags": {
                    "domain": entity_id.split(".")[0],
                    "entity_id": entity_id.split(".")[1],
                },
                "fields": {
                    "brightness": -1.0,
                    "color_temp": -1.0,
                    "effect_list_str": str(ha_metric["attributes"]["effect_list"]),
                    "flowing": 0.0,
                    "friendly_name_str": ha_metric["attributes"]["friendly_name"],
                    "max_mireds": float(ha_metric["attributes"]["max_mireds"]),
                    "min_mireds": float(ha_metric["attributes"]["min_mireds"]),
                    "night_light": 0.0,
                    "state": ha_metric["state"],
                    "supported_features": float(ha_metric["attributes"]["supported_features"]),
                    "value": -1.0
                }
            }]
            self.influx_client.write_points(metric)

        if old == "unavailable" and new == "on":
            metric = [
            {
                "measurement": entity_id,
                "time": str((datetime.utcnow() - timedelta(0,1)).strftime('%Y-%m-%d %H:%M:%SZ')),
                "tags": {
                    "domain": entity_id.split(".")[0],
                    "entity_id": entity_id.split(".")[1],
                },
                "fields": {
                    "brightness": -1.0,
                    "color_temp": -1.0,
                    "effect_list_str": str(ha_metric["attributes"]["effect_list"]),
                    "flowing": 0.0,
                    "friendly_name_str": ha_metric["attributes"]["friendly_name"],
                    "max_mireds": float(ha_metric["attributes"]["max_mireds"]),
                    "min_mireds": float(ha_metric["attributes"]["min_mireds"]),
                    "night_light": 0.0,
                    "state": "unavailable",
                    "supported_features": float(ha_metric["attributes"]["supported_features"]),
                    "value": -1.0
                }
            }]
            self.influx_client.write_points(metric)

        # the last value is the freshest one because the new metric is received faster in Influxdb then having it in Appdaemon
        # because of this I have to work with the value before the last one and NOT the last one
        if (old == "on" and new == "off") or (old == "off" and new == "on"):
            metric = [
            {
                "measurement": entity_id,
                "time": str((datetime.utcnow() - timedelta(0,1)).strftime('%Y-%m-%d %H:%M:%SZ')),
                "tags": {
                    "domain": entity_id.split(".")[0],
                    "entity_id": entity_id.split(".")[1],
                },
                "fields": {
                    "brightness": influx_metric["brightness"],
                    "color_temp": influx_metric["color_temp"],
                    "effect_list_str": influx_metric["effect_list_str"],
                    "flowing": influx_metric["flowing"],
                    "friendly_name_str": influx_metric["friendly_name_str"],
                    "max_mireds": influx_metric["max_mireds"],
                    "min_mireds": influx_metric["min_mireds"],
                    "night_light": influx_metric["night_light"],
                    "state": influx_metric["state"],
                    "supported_features": influx_metric["supported_features"],
                    "value": influx_metric["value"]
                }
            }]
            self.influx_client.write_points(metric)

    def terminate(self):
        self.log("Closing InfluxDB connection")
        self.influx_client.close()
        self.log("Closed InfluxDB connection")











