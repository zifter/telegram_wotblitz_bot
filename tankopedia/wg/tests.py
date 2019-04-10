from unittest import TestCase

from wg.accounts import WOTBAccounts, Account


class WOTBAccountTestCase(TestCase):
    def __init(self):
        self.wotb = None

    def setUp(self):
        self.wotb = WOTBAccounts()

    def tearDown(self):
        self.wotb = None

    def test_search_zifter_ok(self):
        result = self.wotb.fuzzy_search("zifter")
        self.assertListEqual(result, [Account("zifter", 12667056)])

    def test_get_fuzzy_nickname_ok(self):
        result = self.wotb.get_player_info_by_name("zif")
        self.assertIsNone(result)

    def test_get_zifter_ok(self):
        detailed = self.wotb.get_player_info_by_name("zifter")
        self.assertEqual(detailed[0].raw.created_at, 1415187883)

    def test_search_ang_get_zifter_ok(self):
        detailed = self.wotb.fuzzy_search_and_get_info("zifter")
        self.assertEqual(detailed[0].raw.created_at, 1415187883)

