from frictionless import Detector as BaseDetector 


class Detector(BaseDetector):

    def detect_schema(self, fragment, *, labels, schema):
        schema =  super().detect_schema(fragment, labels=labels, schema=schema)
        # 1) do some modifications to read date fields and add date format to the schema
        # 2) do modifications to add bareNumber to currency and decimal fields having the currency or decimal symbol
        return schema 

