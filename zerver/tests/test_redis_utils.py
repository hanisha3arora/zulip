# -*- coding: utf-8 -*-

import mock

from zerver.lib.test_classes import ZulipTestCase
from zerver.lib.redis_utils import get_redis_client, get_dict_from_redis, put_dict_in_redis, \
    ZulipRedisKeyTooLongError, ZulipRedisKeyOfWrongFormatError, MAX_KEY_LENGTH

class RedisUtilsTest(ZulipTestCase):
    key_format = "test_redis_utils_{token}"
    expiration_seconds = 60

    @classmethod
    def setUpClass(cls) -> None:
        cls.redis_client = get_redis_client()
        return super().setUpClass()

    def test_put_and_get_data(self) -> None:
        data = {
            "a": 1,
            "b": "some value"
        }
        key = put_dict_in_redis(self.redis_client, self.key_format, data,
                                expiration_seconds=self.expiration_seconds)
        retrieved_data = get_dict_from_redis(self.redis_client, self.key_format, key)
        self.assertEqual(data, retrieved_data)

    def test_put_data_key_length_check(self) -> None:
        data = {
            "a": 1,
            "b": "some value"
        }

        max_valid_token_length = MAX_KEY_LENGTH - (len(self.key_format) - len('{token}'))
        key = put_dict_in_redis(self.redis_client, self.key_format, data,
                                expiration_seconds=self.expiration_seconds,
                                token_length=max_valid_token_length)
        retrieved_data = get_dict_from_redis(self.redis_client, self.key_format, key)
        self.assertEqual(data, retrieved_data)

        # Trying to put data under an overly long key should get stopped before even
        # generating the random token.
        with mock.patch("zerver.lib.redis_utils.generate_random_token") as mock_generate:
            with self.assertRaises(ZulipRedisKeyTooLongError):
                put_dict_in_redis(self.redis_client, self.key_format, data,
                                  expiration_seconds=self.expiration_seconds,
                                  token_length=max_valid_token_length + 1)
            mock_generate.assert_not_called()

    def test_get_data_key_length_check(self) -> None:
        with self.assertRaises(ZulipRedisKeyTooLongError):
            get_dict_from_redis(self.redis_client, key_format='{token}', key='A' * (MAX_KEY_LENGTH + 1))

    def test_get_data_key_format_validation(self) -> None:
        with self.assertRaises(ZulipRedisKeyOfWrongFormatError):
            get_dict_from_redis(self.redis_client, self.key_format, 'nonmatching_format_1111')
