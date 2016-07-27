from namespacepkg import module_2
from namespacepkg import module_1
import json


def foo():
    module_1.test_method_1()
    module_2.test_method_2()
    json.dumps({"hi": "there"})
