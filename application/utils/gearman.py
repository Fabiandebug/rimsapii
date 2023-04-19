import json 

import python3_gearman as gearman 


class JSONDataEncoder(gearman.DataEncoder):

    @classmethod
    def encode(cls, encodable_object):
        return json.dumps(encodable_object)

    @classmethod
    def decode(cls, decodable_string):
        return json.loads(decodable_string)


class JSONGearmanClient(gearman.GearmanClient):
    data_encoder = JSONDataEncoder


class JSONGearmanWorker(gearman.GearmanWorker):
    data_encoder = JSONDataEncoder
