import random
import string


class UtilHelper:
    @staticmethod
    def get_random_string(length):
        result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
        return result_str
